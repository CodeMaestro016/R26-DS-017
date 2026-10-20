#!/usr/bin/env python3
"""Option B: CARLA camera -> YOLO+ByteTrack -> per-track pose+ensemble -> action.
Requires multi_ped_common.py from the multi-pedestrian package.
"""
import argparse
from multi_ped_common import run

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--host',default='127.0.0.1')
    ap.add_argument('--port',type=int,default=2000)
    ap.add_argument('--seconds',type=float,default=90)
    ap.add_argument('--yolo-url',default='http://127.0.0.1:8094/track')
    args=ap.parse_args()
    run(mode='B',host=args.host,port=args.port,seconds=args.seconds,yolo_url=args.yolo_url)
