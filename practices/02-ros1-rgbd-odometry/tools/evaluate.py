"""Verify actual ROS output against diagnostics; compare with GT, without scale fitting."""
import json
from pathlib import Path
import numpy as np
import rosbag
from scipy.spatial.transform import Rotation

def matrix(xyz,q):
    rotation=Rotation.from_quat(q)
    R=rotation.as_matrix() if hasattr(rotation,'as_matrix') else rotation.as_dcm()
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=xyz;return T

def evaluate(out,bagpath):
    out=Path(out)
    diagnostics=[json.loads(x) for x in (out/'diagnostics.jsonl').read_text().splitlines()]
    published=[json.loads(x) for x in (out/'published.jsonl').read_text().splitlines()]
    expected=[x for x in diagnostics if x['status']!='lost']
    if len(published)!=len(expected) or len(published)<2:
        raise RuntimeError('Published pose count differs from accepted estimates (or fewer than 2 poses)')
    for a,b in zip(expected,published):
        if a['stamp']!=b['stamp'] or b['frame']!='vo_world':raise RuntimeError('Incorrect pose stamp/frame/order')
        with np.load(out/'frames'/('%05d.npz'%a['index'])) as f:
            if not np.allclose(matrix(b['position'],b['quaternion']),f['T'],atol=1e-7):
                raise RuntimeError('Published pose differs from geometry output')
    with rosbag.Bag(str(out/'poses.bag')) as bag:
        if bag.get_message_count('/vo/pose')!=len(expected):raise RuntimeError('Output bag mismatch')
    ground={}
    with rosbag.Bag(str(bagpath)) as bag:
        for _,m,_ in bag.read_messages(topics=['/ground_truth/pose']):
            p=m.pose.position;q=m.pose.orientation
            ground[m.header.stamp.to_sec()]=matrix([p.x,p.y,p.z],[q.x,q.y,q.z,q.w])
    G0=ground[published[0]['stamp']];gt=[];errors=[]
    for row in published:
        g=np.linalg.inv(G0)@ground[row['stamp']];gt.append(g)
        errors.append(float(np.linalg.norm(g[:3,3]-row['position'])))
    np.savez_compressed(out/'ground_truth.npz',T=np.asarray(gt),stamps=[x['stamp'] for x in published])
    report=dict(processed=len(diagnostics),published=len(published),lost=len(diagnostics)-len(published),
                tracking_fraction=len(published)/len(diagnostics),
                position_rmse_m=float(np.sqrt(np.mean(np.square(errors)))),max_position_error_m=max(errors),
                median_processing_ms=float(np.median([x['processing_s'] for x in diagnostics])*1000),
                alignment='First accepted camera pose only (SE3). No scale fitting, no full-trajectory alignment.',
                ros_output_verified=True,algorithm='Frame-to-frame RGB-D ORB + PnP; no bundle adjustment/loop closure')
    (out/'report.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    import sys
    print(json.dumps(evaluate(sys.argv[1],sys.argv[2]),indent=2))
