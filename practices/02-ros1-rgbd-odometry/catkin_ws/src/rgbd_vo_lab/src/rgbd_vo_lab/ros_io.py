"""Prepared image conversion, diagnostics and pose conversion."""
from pathlib import Path
import json
import time
import yaml
import numpy as np
import rospy
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_matrix
from .geometry import Odometry


class LabIO:
    def __init__(self):
        cfg=Path(rospy.get_param('~config','/lab/config.yaml'))
        self.config=yaml.safe_load(cfg.read_text())
        if self.config['frame_stride']<1 or self.config['min_inliers']<6:
            raise ValueError('frame_stride >= 1, min_inliers >= 6 required')
        self.out=Path(rospy.get_param('~out'))
        (self.out/'frames').mkdir(parents=True,exist_ok=True)
        self.engine=Odometry(self.config);self.bridge=CvBridge();self.received=0
        self.log=open(self.out/'diagnostics.jsonl','w',buffering=1)
        rospy.on_shutdown(self.log.close)

    def process_messages(self, color, depth, info):
        index=self.received;self.received+=1
        (self.out/'received.txt').write_text(str(self.received))
        if index%int(self.config['frame_stride']): return None
        started=time.monotonic()
        rgb=self.bridge.imgmsg_to_cv2(color,'rgb8')
        z=self.bridge.imgmsg_to_cv2(depth,'32FC1')
        K=np.asarray(info.K,np.float64).reshape(3,3)
        if rgb.shape[:2]!=z.shape or not np.isfinite(K).all() or K[0,0]<=0:
            raise ValueError('RGB/depth registration or CameraInfo is invalid')
        result=self.engine.process(rgb,z,K)
        stamp=color.header.stamp.to_sec()
        np.savez_compressed(self.out/'frames'/('%05d.npz'%index),
                            rgb=rgb,depth=z,K=K,stamp=stamp,index=index,**result)
        row={k:v for k,v in result.items() if k not in ('T','uv','reference_uv','inlier_mask')}
        row.update(index=index,stamp=stamp,processing_s=time.monotonic()-started)
        self.log.write(json.dumps(row,allow_nan=False)+'\n')
        if result['status']=='lost':
            rospy.logwarn('Frame %s lost: %s',index,result['reason'])
            return None
        msg=PoseStamped();msg.header.stamp=color.header.stamp;msg.header.frame_id='vo_world'
        xyz=result['T'][:3,3];q=quaternion_from_matrix(result['T'])
        msg.pose.position.x,msg.pose.position.y,msg.pose.position.z=map(float,xyz)
        msg.pose.orientation.x,msg.pose.orientation.y,msg.pose.orientation.z,msg.pose.orientation.w=map(float,q)
        return msg
