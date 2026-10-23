#!/usr/bin/env python3
import sys,json
from pathlib import Path
import rospy,rosbag
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path as RosPath

rospy.init_node('vo_recorder')
out=Path(sys.argv[1]);bag=rosbag.Bag(str(out/'poses.bag'),'w')
stream=open(out/'published.jsonl','w',buffering=1)
path=RosPath();path.header.frame_id='vo_world'
pub=rospy.Publisher('/vo/path',RosPath,queue_size=2,latch=True)
def callback(msg):
    bag.write('/vo/pose',msg,msg.header.stamp)
    path.header=msg.header;path.poses.append(msg);pub.publish(path)
    bag.write('/vo/path',path,msg.header.stamp)
    p=msg.pose.position;q=msg.pose.orientation
    stream.write(json.dumps(dict(stamp=msg.header.stamp.to_sec(),frame=msg.header.frame_id,
                                position=[p.x,p.y,p.z],quaternion=[q.x,q.y,q.z,q.w]))+'\n')
sub=rospy.Subscriber('/vo/pose',PoseStamped,callback,queue_size=100)
rospy.spin()
bag.close();stream.close()
