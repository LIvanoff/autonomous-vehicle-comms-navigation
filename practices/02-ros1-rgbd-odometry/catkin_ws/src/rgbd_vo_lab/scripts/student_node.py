#!/usr/bin/env python3
import rospy
import message_filters
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped
from rgbd_vo_lab.ros_io import LabIO


class StudentNode:
    def __init__(self):
        self.lab = LabIO()
        # TODO 1: создать rospy.Publisher для позы; сохранить в self.pub.
        # TODO 2: создать три message_filters.Subscriber:
        # self.rgb_sub (RGB), self.depth_sub (глубина), self.info_sub (CameraInfo).
        # Топики, типы сообщений и параметры очередей указаны в README.md.
        raise NotImplementedError('Создайте publisher и три подписчика')

        # Готовая синхронизация: callback получит тройку с одинаковым header.stamp.
        # Этот блок менять не нужно. Подписчики выше должны быть созданы заранее.
        self.sync = message_filters.TimeSynchronizer(
            [self.rgb_sub, self.depth_sub, self.info_sub], queue_size=20
        )
        self.sync.registerCallback(self.callback)

    def callback(self, color, depth, info):
        # TODO 3: передать сообщения в готовый self.lab.process_messages.
        # TODO 4: если результат не None, опубликовать его.
        pass


if __name__ == '__main__':
    rospy.init_node('rgbd_vo_student')
    node = StudentNode()
    rospy.spin()
