#!/usr/bin/env python3
"""Complete the two ROS TODOs. Rotation functions are provided."""
import argparse
import numpy as np
import rospy
import yaml
from sensor_msgs.msg import PointCloud2
from cloud_io import read_xyz, replace_xyz


def rotation_matrix(roll_deg, pitch_deg, yaw_deg):
    """Return Rz(yaw) @ Ry(pitch) @ Rx(roll). Right handed, column vectors."""
    roll, pitch, yaw = np.deg2rad([roll_deg, pitch_deg, yaw_deg])
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return rz @ ry @ rx


def correct_points(xyz, rotation):
    """Return a copy. Rotate finite rows only; keep invalid rows and point order."""
    result = xyz.copy()
    valid = np.isfinite(xyz).all(axis=1)
    # Points are stored as rows, so multiply by the transposed rotation.
    result[valid] = xyz[valid] @ rotation.T
    return result


class CloudCorrector:
    def __init__(self, config):
        self.rotation = rotation_matrix(config['roll_deg'], config['pitch_deg'], config['yaw_deg'])
        # TODO 1: создайте ROS Publisher и Subscriber по контракту из задания.
        raise NotImplementedError('TODO 1: publisher and subscriber')

    def callback(self, msg):
        # TODO 2: read_xyz -> correct_points -> replace_xyz(frame_id='lidar_level')
        # -> publish. Do not replace msg.header.stamp by rospy.Time.now().
        raise NotImplementedError('TODO 2: callback')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yaml')
    args = parser.parse_args(rospy.myargv()[1:])
    with open(args.config, encoding='utf-8') as stream:
        config = yaml.safe_load(stream)
    rospy.init_node('cloud_corrector')
    node = CloudCorrector(config)
    rospy.spin()
