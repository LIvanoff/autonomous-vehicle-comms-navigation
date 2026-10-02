#!/usr/bin/env python3
"""One command runs a fresh ROS master, student node, recorder and rosbag play."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import xmlrpc.client
import rosbag
from preview import render_bag


def stamps(path, topic):
    with rosbag.Bag(str(path)) as bag:
        return Counter(msg.header.stamp.to_nsec() for _, msg, _ in bag.read_messages(topics=[topic]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('bag'); parser.add_argument('--out', required=True)
    parser.add_argument('--config', default='config.yaml'); parser.add_argument('--rate', type=float, default=.5)
    parser.add_argument('--node', default='student_node.py'); parser.add_argument('--no-preview', action='store_true')
    args = parser.parse_args()
    if args.rate <= 0: parser.error('rate must be positive')
    source = Path(args.bag).resolve(); out = Path(args.out).resolve()
    if not source.is_file(): parser.error('Input bag does not exist')
    if out.exists(): parser.error('Output already exists; choose a new --out to preserve previous attempts')
    out.mkdir(parents=True)
    procs = []; handles = []
    env = dict(os.environ, ROS_MASTER_URI='http://127.0.0.1:11311', ROS_HOSTNAME='localhost')
    master = xmlrpc.client.ServerProxy(env['ROS_MASTER_URI'])
    try:
        master.getPid('/cloud_lab_probe')
    except OSError:
        pass
    else:
        parser.error('An existing ROS master is running. Use a fresh docker compose run --rm lab ...')
    def start(command, name):
        log = open(out/(name+'.log'), 'w'); handles.append(log)
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        procs.append(proc); return proc
    def stop(proc):
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGINT)
            try: proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM); proc.wait(timeout=5)
    try:
        core = start(['roscore'], 'roscore')
        deadline = time.monotonic()+25
        while True:
            try:
                if master.getPid('/cloud_lab')[0] == 1: break
            except OSError: pass
            if time.monotonic()>deadline: raise RuntimeError('roscore did not start')
            time.sleep(.1)
        master.setParam('/cloud_lab', '/use_sim_time', True)
        recorder = start([sys.executable, 'record_output.py', str(out/'corrected.bag')], 'recorder')
        node = start([sys.executable, args.node, '--config', args.config], 'student')
        deadline = time.monotonic()+25
        while True:
            if node.poll() is not None: raise RuntimeError('Student node stopped; see student.log')
            if recorder.poll() is not None: raise RuntimeError('Recorder stopped; see recorder.log')
            state = master.getSystemState('/cloud_lab')[2]
            pubs, subs = dict(state[0]), dict(state[1])
            if '/points_raw' in subs and '/points_corrected' in pubs and '/points_corrected' in subs: break
            if time.monotonic()>deadline: raise RuntimeError('Required publishers/subscribers are missing')
            time.sleep(.1)
        player = start(['rosbag', 'play', '--clock', '--delay=2', '-r', str(args.rate), str(source)], 'player')
        with rosbag.Bag(str(source)) as bag: duration = bag.get_end_time()-bag.get_start_time()
        player.wait(timeout=duration/args.rate+60)
        if player.returncode: raise RuntimeError('rosbag play failed; see player.log')
        expected = stamps(source, '/points_raw')
        # Give callbacks time to drain, then close output before opening it for validation.
        time.sleep(3)
        if node.poll() is not None: raise RuntimeError('Student node exited during replay')
        stop(node); time.sleep(.5); stop(recorder)
        actual = stamps(out/'corrected.bag', '/points_corrected')
        result = {'input_messages': sum(expected.values()), 'output_messages': sum(actual.values()),
                  'same_stamps_and_counts': expected == actual}
        (out/'run_check.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
        if not expected or expected != actual: raise RuntimeError('Missing/extra clouds or changed stamps; reduce --rate if callbacks are slow')
        if not args.no_preview: render_bag(out/'corrected.bag', out/'preview', '/points_corrected')
    finally:
        for proc in reversed(procs): stop(proc)
        for log in handles: log.close()


if __name__ == '__main__': main()
