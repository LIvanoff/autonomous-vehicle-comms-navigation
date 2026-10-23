#!/usr/bin/env python3
"""Create a small ROS1 bag from the ORIGINAL TUM RGB-D PNG archive."""
import argparse, hashlib, json, tarfile, shutil
from pathlib import Path
import cv2
import numpy as np
import rosbag, rospy
from cv_bridge import CvBridge
from sensor_msgs.msg import CameraInfo
from geometry_msgs.msg import PoseStamped
from scipy.spatial.transform import Rotation, Slerp


def main():
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path)
    p.add_argument('--out',type=Path,default=Path('data/tum_rgbd_12s.bag'))
    p.add_argument('--seconds',type=float,default=12.);p.add_argument('--hz',type=float,default=10.)
    a=p.parse_args()
    if a.out.exists(): raise FileExistsError(a.out)
    bridge=CvBridge(); rows=[];K=[525.,0.,319.5,0.,525.,239.5,0.,0.,1.]
    cache=a.archive.parent/'tum_source'
    cache.mkdir(exist_ok=True)
    marker=cache/'complete.txt'
    if not marker.exists():
        with tarfile.open(a.archive,'r|gz') as stream:
            for member in stream:
                if not member.isfile():continue
                target=(cache/member.name).resolve()
                if cache.resolve() not in target.parents:raise ValueError('Unsafe archive path')
                target.parent.mkdir(parents=True,exist_ok=True)
                with stream.extractfile(member) as src,open(target,'wb') as dst:shutil.copyfileobj(src,dst)
        marker.write_text('Extracted safely')
    if True:
        root=next(cache.glob('*/rgb.txt')).parent
        def lines(name):
            return [line.split() for line in (root/name).read_text().splitlines()
                    if line.strip() and not line.startswith('#')]
        rgb=lines('rgb.txt'); dep=lines('depth.txt');gt=np.asarray(lines('groundtruth.txt'),float)
        dt=np.asarray([float(x[0]) for x in dep]); start=float(rgb[0][0])+1.
        rotations=Slerp(gt[:,0],Rotation.from_quat(gt[:,4:8]))
        last=-float('inf'); used=set();a.out.parent.mkdir(parents=True,exist_ok=True)
        with rosbag.Bag(str(a.out),'w',compression='bz2') as bag:
            for item in rgb:
                t=float(item[0])
                if t<start or t>start+a.seconds or t-last<.95/a.hz: continue
                j=int(np.argmin(abs(dt-t)))
                if abs(dt[j]-t)>.02 or j in used or not gt[0,0]<=t<=gt[-1,0]: continue
                def decode(name):
                    return cv2.imread(str(root/name),cv2.IMREAD_UNCHANGED)
                color=cv2.cvtColor(decode(item[1]),cv2.COLOR_BGR2RGB)
                depth=decode(dep[j][1]).astype(np.float32)/5000.
                stamp=rospy.Time.from_sec(t)
                cm=bridge.cv2_to_imgmsg(color,'rgb8');dm=bridge.cv2_to_imgmsg(depth,'32FC1')
                ci=CameraInfo();ci.width=color.shape[1];ci.height=color.shape[0];ci.K=K
                ci.D=[0.]*5;ci.distortion_model='plumb_bob'
                ci.R=np.eye(3).ravel().tolist();ci.P=[525.,0.,319.5,0.,0.,525.,239.5,0.,0.,0.,1.,0.]
                for msg in (cm,dm,ci):
                    msg.header.seq=len(rows);msg.header.stamp=stamp;msg.header.frame_id='camera_optical'
                pose=PoseStamped();pose.header.stamp=stamp;pose.header.frame_id='mocap_world'
                xyz=[np.interp(t,gt[:,0],gt[:,c]) for c in (1,2,3)];q=rotations([t]).as_quat()[0]
                pose.pose.position.x,pose.pose.position.y,pose.pose.position.z=xyz
                pose.pose.orientation.x,pose.pose.orientation.y,pose.pose.orientation.z,pose.pose.orientation.w=q
                for topic,msg in [('/camera/rgb/image_raw',cm),('/camera/depth/image_raw',dm),
                                  ('/camera/rgb/camera_info',ci),('/ground_truth/pose',pose)]:
                    bag.write(topic,msg,stamp)
                rows.append(dict(stamp=t,rgb=item[1],depth=dep[j][1],depth_original_stamp=float(dt[j]),
                                 gt_position=xyz,gt_quaternion=q.tolist()))
                last=t;used.add(j)
    digest=hashlib.sha256()
    with a.archive.open('rb') as src:
        for block in iter(lambda:src.read(1024*1024),b''):digest.update(block)
    manifest=dict(source='TUM RGB-D freiburg1_xyz',source_url='https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download',
                  archive_sha256=digest.hexdigest(),
                  frames=len(rows),K=K,depth_unit='metres; original uint16 PNG / 5000',
                  registration='TUM pre-registered depth; ROS default intrinsics per TUM recommendation; no extra undistortion',
                  association='nearest unused depth <=20 ms; original RGB stamp copied to associated depth for exact ROS sync',
                  ground_truth='interpolated camera poses; translation linear, orientation SLERP; evaluator only',samples=rows)
    a.out.with_suffix('.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(dict(frames=len(rows),duration=rows[-1]['stamp']-rows[0]['stamp'],bag=str(a.out))))


if __name__=='__main__':main()
