from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import numpy as np
from ultralytics import YOLO

@dataclass
class TrackedPedestrian:
    track_id: int
    bbox: tuple[float,float,float,float]
    confidence: float
    def to_dict(self)->dict[str,Any]:
        return asdict(self)

class AutomaticPedestrianTracker:
    """Upstream raw-frame person detector + tracker; not the intent model."""
    def __init__(self, model_path='yolo11n.pt', tracker_config='botsort.yaml', conf=0.10, iou=0.70, imgsz=640, device='cpu'):
        self.model_path=str(model_path); self.tracker_config=str(tracker_config)
        self.conf=float(conf); self.iou=float(iou); self.imgsz=int(imgsz); self.device=str(device)
        self.model=YOLO(self.model_path)

    def reset(self):
        if hasattr(self.model,'predictor'):
            self.model.predictor=None

    def track_frame(self, frame:np.ndarray)->list[TrackedPedestrian]:
        if not isinstance(frame,np.ndarray) or frame.ndim!=3 or frame.shape[2]!=3:
            raise ValueError(f'Expected BGR frame (H,W,3), got {getattr(frame,"shape",None)}')
        results=self.model.track(source=frame,persist=True,tracker=self.tracker_config,classes=[0],conf=self.conf,iou=self.iou,imgsz=self.imgsz,device=self.device,verbose=False)
        if not results or results[0].boxes is None or len(results[0].boxes)==0:
            return []
        b=results[0].boxes
        xyxy=b.xyxy.detach().cpu().numpy(); conf=b.conf.detach().cpu().numpy()
        ids=np.full(len(xyxy),-1,dtype=np.int64) if b.id is None else b.id.detach().cpu().numpy().astype(np.int64)
        return [TrackedPedestrian(int(tid),tuple(float(v) for v in box),float(score)) for box,score,tid in zip(xyxy,conf,ids)]
