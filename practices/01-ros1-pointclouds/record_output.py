#!/usr/bin/env python3
"""Provided output recorder. Images are rendered AFTER replay, not in callback."""
import sys
import threading
import rosbag
import rospy
from sensor_msgs.msg import PointCloud2

rospy.init_node('cloud_recorder')
bag = rosbag.Bag(sys.argv[1], 'w', compression='lz4')
lock = threading.Lock()
count = 0

def callback(msg):
    global count
    with lock:
        bag.write('/points_corrected', msg, t=msg.header.stamp)
        count += 1

sub = rospy.Subscriber('/points_corrected', PointCloud2, callback, queue_size=200, buff_size=33554432)
print('RECORDER_READY', flush=True)
try:
    rospy.spin()
finally:
    sub.unregister()
    with lock:
        bag.close()
    print('RECORDED', count, flush=True)
