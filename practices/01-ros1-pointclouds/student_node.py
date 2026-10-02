#!/usr/bin/env python3
"""Complete four TODOs. The angles describe YOUR correction, not corruption."""
import argparse
import numpy as np
import rospy
import yaml
from sensor_msgs.msg import PointCloud2
from cloud_io import read_xyz, replace_xyz


def rotation_matrix(roll_deg, pitch_deg, yaw_deg):
    """Return Rz(yaw) @ Ry(pitch) @ Rx(roll). Right handed, column vectors."""
    # TODO 1: degrees -> radians; construct Rx, Ry, Rz; return their product.
    raise NotImplementedError('TODO 1: rotation_matrix')


def correct_points(xyz, rotation):
    """Return a copy. Rotate finite rows only; keep invalid rows and point order."""
    # TODO 2: each point is stored as a ROW in xyz (shape N x 3).
    raise NotImplementedError('TODO 2: correct_points')


class CloudCorrector:
    def __init__(self, config):
        self.rotation = rotation_matrix(config['roll_deg'], config['pitch_deg'], config['yaw_deg'])
        # TODO 3: create Publisher('/points_corrected', PointCloud2, queue_size=20)
        # and Subscriber('/points_raw', PointCloud2, self.callback,
        #                queue_size=100, buff_size=16777216).
        # Store both handles as self.pub and self.sub.
        raise NotImplementedError('TODO 3: publisher and subscriber')

    def callback(self, msg):
        # TODO 4: read_xyz -> correct_points -> replace_xyz(frame_id='lidar_level')
        # -> publish. Do not replace msg.header.stamp by rospy.Time.now().
        raise NotImplementedError('TODO 4: callback')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yaml')
    args = parser.parse_args(rospy.myargv()[1:])
    with open(args.config, encoding='utf-8') as stream:
        config = yaml.safe_load(stream)
    rospy.init_node('cloud_corrector')
    node = CloudCorrector(config)
    rospy.spin()
