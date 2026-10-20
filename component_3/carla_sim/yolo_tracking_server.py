#!/usr/bin/env python3
"""YOLO + ByteTrack HTTP bridge.
"""
import argparse
import threading
import numpy as np
import cv2
from flask import Flask, request, jsonify
from ultralytics import YOLO

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--weights', default='yolo11n.pt')
    ap.add_argument('--host', default='0.0.0.0')
    ap.add_argument('--port', type=int, default=8094)
    ap.add_argument('--conf', type=float, default=0.25)
    args=ap.parse_args()
    model=YOLO(args.weights)
    lock=threading.Lock()
    app=Flask(__name__)
    @app.route('/health')
    def health():
        return jsonify({'ok':True,'weights':args.weights})
    @app.route('/track',methods=['POST'])
    def track():
        raw=request.get_data()
        if not raw:
            return jsonify({'error':'empty image'}),400
        arr=np.frombuffer(raw,dtype=np.uint8)
        image=cv2.imdecode(arr,cv2.IMREAD_COLOR)
        if image is None:
            return jsonify({'error':'invalid image'}),400
        with lock:
            result=model.track(image, persist=True, tracker='bytetrack.yaml',
                               classes=[0], conf=args.conf, verbose=False)[0]
        detections=[]
        boxes=result.boxes
        if boxes is not None and boxes.id is not None:
            xyxy=boxes.xyxy.cpu().numpy()
            ids=boxes.id.int().cpu().tolist()
            confs=boxes.conf.cpu().tolist()
            for xy,track_id,score in zip(xyxy,ids,confs):
                bbox=[int(round(float(v))) for v in xy]
                detections.append({'id':int(track_id),'track_id':int(track_id),
                                   'box':bbox,'bbox':bbox,'confidence':float(score),
                                   'class_id':0,'label':'person'})
        return jsonify({'detections':detections,'tracks':detections,
                        'image_width':image.shape[1],'image_height':image.shape[0]})
    print('YOLO ByteTrack ready: http://127.0.0.1:%d/track'%args.port,flush=True)
    app.run(host=args.host,port=args.port,threaded=False,use_reloader=False)
if __name__=='__main__':
    main()
