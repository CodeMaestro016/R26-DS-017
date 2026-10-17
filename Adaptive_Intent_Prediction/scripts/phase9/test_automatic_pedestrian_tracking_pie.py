from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
import cv2, numpy as np, pandas as pd
from utils.annotation_loader import AnnotationLoader
from utils.image_loader import ImageLoader
from utils.automatic_pedestrian_tracker import AutomaticPedestrianTracker

FRAME_ROOT=Path('datasets/processed/frames'); ANN=Path('datasets/processed/metadata/annotations.csv'); TEST=Path('datasets/processed/metadata/test.csv'); OUT=Path('outputs/phase9/automatic_tracking')

def parse_args():
    p=argparse.ArgumentParser(); p.add_argument('--sequence-index',type=int,default=28); p.add_argument('--dataset-set',default='set01'); p.add_argument('--model',default='yolo11n.pt'); p.add_argument('--tracker',default='botsort.yaml'); p.add_argument('--conf',type=float,default=.10); p.add_argument('--imgsz',type=int,default=640); return p.parse_args()

def first(row,names):
    for n in names:
        if n in row.index:return row[n]
    raise KeyError(names)

def frames_of(v):
    s=str(v).replace(',','|').replace(' ','|'); return [int(x) for x in s.split('|') if x]

def iou(a,b):
    ax1,ay1,ax2,ay2=a; bx1,by1,bx2,by2=b; ix1=max(ax1,bx1);iy1=max(ay1,by1);ix2=min(ax2,bx2);iy2=min(ay2,by2); iw=max(0.,ix2-ix1);ih=max(0.,iy2-iy1); inter=iw*ih; aa=max(0.,ax2-ax1)*max(0.,ay2-ay1);bb=max(0.,bx2-bx1)*max(0.,by2-by1);u=aa+bb-inter; return 0. if u<=0 else inter/u

def draw(frame,box,label,color):
    x1,y1,x2,y2=[int(round(x)) for x in box]; cv2.rectangle(frame,(x1,y1),(x2,y2),color,2); cv2.putText(frame,label,(x1,max(20,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.45,color,1,cv2.LINE_AA)

def main():
    a=parse_args(); print('='*100); print('PHASE 9.4A - AUTOMATIC PARTIALLY-OCCLUDED PEDESTRIAN DETECTION + TRACKING'); print('='*100)
    m=pd.read_csv(TEST).reset_index(drop=True); row=m.iloc[a.sequence_index]; video=str(first(row,['video','video_id'])); pid=str(first(row,['pedestrian_id','id','pedestrian'])); frames=frames_of(first(row,['frames','frame_numbers','sequence_frames']))
    if len(frames)!=30: raise ValueError(f'Expected 30 frames, got {len(frames)}')
    il=ImageLoader(str(FRAME_ROOT)); al=AnnotationLoader(str(ANN)); tr=AutomaticPedestrianTracker(a.model,a.tracker,a.conf,.70,a.imgsz,'cpu'); tr.reset(); OUT.mkdir(parents=True,exist_ok=True)
    video_out=OUT/f'pie_auto_tracking_sequence_{a.sequence_index}.mp4'; csv_out=OUT/f'pie_auto_tracking_sequence_{a.sequence_index}.csv'; js_out=OUT/f'pie_auto_tracking_sequence_{a.sequence_index}_summary.json'
    print('Model:',a.model,'| Tracker:',a.tracker,'| Device: CPU'); print('PIE target ID:',pid,'(evaluation reference only)'); print('IMPORTANT: PIE bbox/ID is NOT passed to YOLO/BoT-SORT; it is used after inference only for scoring.\n')
    writer=None; rows=[]; ids=[]
    for step,fn in enumerate(frames,1):
        frame=il.load_frame(video=video,frame_number=fn,dataset_set=a.dataset_set)
        if writer is None:
            h,w=frame.shape[:2]; writer=cv2.VideoWriter(str(video_out),cv2.VideoWriter_fourcc(*'mp4v'),10.0,(w,h))
        gt=al.get_annotation(video=video,frame=fn,pedestrian_id=pid)
        if gt is None: raise RuntimeError(f'Missing PIE annotation frame {fn}')
        gtb=tuple(float(gt[k]) for k in ('x1','y1','x2','y2')); dets=tr.track_frame(frame); best=None; bi=0.
        for d in dets:
            q=iou(d.bbox,gtb)
            if q>bi: bi=q; best=d
        tid=None if best is None or bi<=0 else best.track_id; ids.append(tid if bi>=.10 and tid is not None and tid>=0 else None)
        conf=float('nan') if best is None else best.confidence; occ=str(gt['occlusion'])
        rows.append({'step':step,'frame':fn,'reference_occlusion':occ,'automatic_person_count':len(dets),'best_iou':bi,'matched_auto_track_id':tid,'matched_confidence':conf,'match_iou_0_10':int(bi>=.10),'match_iou_0_30':int(bi>=.30),'match_iou_0_50':int(bi>=.50)})
        vis=frame.copy(); draw(vis,gtb,f'PIE REF {pid} occ={occ}',(255,0,0))
        if best is not None: draw(vis,best.bbox,f'AUTO ID={best.track_id} conf={best.confidence:.2f} IoU={bi:.2f}',(0,255,0))
        writer.write(vis); print(f'Frame {step:02d}/30 | source={fn} | ref_occ={occ:5s} | persons={len(dets):2d} | best_IoU={bi:.3f} | auto_track={tid}')
    writer.release(); df=pd.DataFrame(rows); df.to_csv(csv_out,index=False)
    rec10=float(df.match_iou_0_10.mean());rec30=float(df.match_iou_0_30.mean());rec50=float(df.match_iou_0_50.mean());mean_iou=float(df.best_iou.mean()); pos=[x for x in ids if x is not None]
    mode=None; frac=0.; longest=0
    if pos:
        mode,count=Counter(pos).most_common(1)[0]; frac=count/len(pos); cur=0
        for x in ids:
            cur=cur+1 if x==mode else 0; longest=max(longest,cur)
    summary={'phase':'9.4A','model':a.model,'tracker':a.tracker,'device':'cpu','sequence_index':a.sequence_index,'video':video,'reference_target':pid,'annotation_used_as_detector_input':False,'recall_iou_0_10':rec10,'recall_iou_0_30':rec30,'recall_iou_0_50':rec50,'mean_best_iou':mean_iou,'dominant_auto_track_id':mode,'dominant_id_fraction':frac,'longest_dominant_id_run':longest,'video_output':str(video_out),'csv_output':str(csv_out)}; js_out.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('\n'+'-'*100);print('AUTOMATIC DETECTION / TRACKING SUMMARY');print('-'*100);print(f'Recall @ IoU>=0.10 : {rec10:.4f}');print(f'Recall @ IoU>=0.30 : {rec30:.4f}');print(f'Recall @ IoU>=0.50 : {rec50:.4f}');print(f'Mean best IoU      : {mean_iou:.4f}');print('Dominant auto ID   :',mode);print(f'Dominant ID fraction: {frac:.4f}');print(f'Longest ID run     : {longest}/30');print('\nOutputs:');print(csv_out);print(js_out);print(video_out);print('\nAutomatic occlusion-state estimation is the next step.');print('Status: PASSED');print('='*100)

if __name__=='__main__': main()
