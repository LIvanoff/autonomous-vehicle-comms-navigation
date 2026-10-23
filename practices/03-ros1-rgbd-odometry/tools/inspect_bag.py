#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import rosbag

REQUIRED={'/camera/rgb/image_raw':'sensor_msgs/Image','/camera/depth/image_raw':'sensor_msgs/Image',
          '/camera/rgb/camera_info':'sensor_msgs/CameraInfo'}

def inspect(path):
    with rosbag.Bag(str(path)) as bag:
        topics={k:dict(type=v.msg_type,count=v.message_count) for k,v in bag.get_type_and_topic_info().topics.items()}
        missing=[k for k,v in REQUIRED.items() if k not in topics or topics[k]['type']!=v]
        return dict(topics=topics,duration_s=bag.get_end_time()-bag.get_start_time(),rgbd_ready=not missing,missing=missing)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('bag');p.add_argument('--preview',type=Path)
    a=p.parse_args();report=inspect(a.bag);print(json.dumps(report,indent=2))
    if a.preview:
        a.preview.mkdir(parents=True,exist_ok=True)
        report['kind']='rgb_only';frames=[]
        with rosbag.Bag(a.bag) as bag:
            for _,msg,t in bag.read_messages():
                if msg._type=='sensor_msgs/CompressedImage':
                    file='%05d.jpg'%len(frames);(a.preview/file).write_bytes(msg.data)
                    frames.append(dict(file=file,stamp=msg.header.stamp.to_sec()))
        report['frames']=frames
        (a.preview/'input_report.json').write_text(json.dumps(report,indent=2))
    if not report['rgbd_ready']:raise SystemExit(2)
