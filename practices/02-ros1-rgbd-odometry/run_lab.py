#!/usr/bin/env python3
import argparse,json,os,signal,subprocess,sys,time,xmlrpc.client,yaml
from pathlib import Path
import rosbag
from tools.inspect_bag import inspect
from tools.evaluate import evaluate

def main():
    p=argparse.ArgumentParser();p.add_argument('bag',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--config',type=Path,default=Path('/lab/config.yaml'));p.add_argument('--node',type=Path)
    p.add_argument('--rate',type=float,default=.25);a=p.parse_args()
    if a.rate<=0:p.error('rate must be positive')
    report=inspect(a.bag)
    if not report['rgbd_ready']:p.error('RGB-D input required. Missing: '+', '.join(report['missing']))
    if a.out.exists():p.error('Choose a new output directory; previous attempts are preserved')
    a.out.mkdir(parents=True);a.out=a.out.resolve();a.bag=a.bag.resolve()
    with rosbag.Bag(str(a.bag)) as bag: expected=bag.get_message_count('/camera/rgb/image_raw')
    master=xmlrpc.client.ServerProxy('http://127.0.0.1:11311')
    try: master.getPid('/lab_probe')
    except OSError: pass
    else:raise RuntimeError('Use a fresh docker compose run container; ROS master already exists')
    procs=[];logs=[];started=time.monotonic()
    def start(cmd,name):
        f=open(a.out/(name+'.log'),'w');logs.append(f)
        proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        procs.append(proc);return proc
    def stop(proc):
        if proc.poll() is None:
            os.killpg(proc.pid,signal.SIGINT)
            try:proc.wait(10)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGTERM);proc.wait(5)
    try:
        start(['roscore'],'roscore');deadline=time.monotonic()+30
        while True:
            try:
                if master.getPid('/lab')[0]==1:break
            except OSError:pass
            if time.monotonic()>deadline:raise RuntimeError('roscore timeout')
            time.sleep(.1)
        master.setParam('/lab','/use_sim_time',True)
        recorder=start([sys.executable,'tools/record_poses.py',str(a.out)],'recorder')
        cmd=[sys.executable,str(a.node)] if a.node else ['rosrun','rgbd_vo_lab','student_node.py']
        node=start(cmd+['_out:='+str(a.out),'_config:='+str(a.config.resolve())],'student')
        deadline=time.monotonic()+25
        while True:
            if node.poll() is not None:raise RuntimeError('Node exited: inspect student.log (TODOs completed?)')
            pubs,subs,_=master.getSystemState('/lab')[2];pubs=dict(pubs);subs=dict(subs)
            if all(k in subs for k in report['topics'] if k.startswith('/camera/')) and '/vo/pose' in pubs and '/vo/pose' in subs:break
            if time.monotonic()>deadline:raise RuntimeError('Missing RGB-D subscriptions or /vo/pose publisher')
            time.sleep(.1)
        player=start(['rosbag','play','--clock','--delay=1','--wait-for-subscribers',
                      '-r',str(a.rate),str(a.bag),'--topics',
                      '/camera/rgb/image_raw','/camera/depth/image_raw',
                      '/camera/rgb/camera_info'],'player')
        player.wait(timeout=report['duration_s']/a.rate+60)
        if player.returncode:raise RuntimeError('rosbag playback failed')
        deadline=time.monotonic()+30
        while True:
            received=a.out/'received.txt'
            if received.exists() and received.read_text().strip()==str(expected):break
            if node.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Not all RGB-D frames received')
            time.sleep(.1)
        # Wait for completed geometry AND actual ROS delivery, not a fixed sleep.
        stride=int(yaml.safe_load(a.config.read_text())['frame_stride'])
        required=(expected+stride-1)//stride;deadline=time.monotonic()+30
        while True:
            try:
                diag=[json.loads(x) for x in (a.out/'diagnostics.jsonl').read_text().splitlines()]
                rows=[json.loads(x) for x in (a.out/'published.jsonl').read_text().splitlines()]
                if len(diag)==required and len(rows)==sum(x['status']!='lost' for x in diag):break
            except (FileNotFoundError,json.JSONDecodeError):pass
            if node.poll() is not None or recorder.poll() is not None or time.monotonic()>deadline:
                raise RuntimeError('Callbacks or pose publication did not finish; inspect student.log')
            time.sleep(.1)
        stop(node);stop(recorder)
        result=evaluate(a.out,a.bag);result['wall_seconds']=time.monotonic()-started
        result['input_frames']=expected;result['play_rate']=a.rate
        (a.out/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    finally:
        for proc in reversed(procs):stop(proc)
        for f in logs:f.close()

if __name__=='__main__':main()
