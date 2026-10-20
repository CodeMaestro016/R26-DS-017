# -*- coding: utf-8 -*-
"""Shared experimental multi-pedestrian CARLA runner. Requires existing project modules.
Run inside the same CARLA Python environment as carla_live_demo.py.
This is research/demo code, NOT a validated autonomous-driving controller.
"""
from __future__ import print_function
import argparse, csv, json, math, os, time, urllib.request
from collections import deque
import numpy as np
import carla
import carla_live_demo as base
from scenario_suite import ScenarioSpec

# Five spaced interactions rather than a crowd at the first junction.
# Each event is activated when the ego approaches, not at simulation start.
EVENTS = [
    (35, [('committed', -3.5, 1), ('committed', 3.5, -1)]),
    (85, [('distracted', 0.0, 1)]),
    (135, [('jaywalk', 0.0, -1)]),
    (190, [('aggressive', -3.0, 1), ('aggressive', 3.0, 1)]),
    (245, [('waiting', -3.0, 1), ('hesitant', 3.0, -1)]),
]
LABELS = base.LABELS


def _xy_distance(a, b):
    return math.hypot(a.x-b.x, a.y-b.y)


def _ahead(waypoint, meters):
    current = waypoint
    for _ in range(int(meters / 2.0)):
        nxt = current.next(2.0)
        if not nxt:
            return None
        matching = [p for p in nxt
                    if p.road_id == current.road_id and p.lane_id == current.lane_id]
        current = matching[0] if matching else nxt[0]
    return current


def _crosswalk_waypoint(world, origin, minimum=24.0, maximum=75.0):
    """Find an actual mapped zebra intersecting the ego route; return a route waypoint."""
    m = world.get_map()
    points = m.get_crosswalks() if hasattr(m, 'get_crosswalks') else []
    polygons, polygon = [], []
    for pt in points:
        if polygon and _xy_distance(pt, polygon[0]) < 0.15:
            if len(polygon) >= 3:
                polygons.append(polygon[:])
            polygon = []
        else:
            polygon.append(pt)
    if len(polygon) >= 3:
        polygons.append(polygon)

    def distance_to_polygon(loc, poly):
        # Inside a polygon means the lane centre passes through the zebra.
        inside = False
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            if ((a.y > loc.y) != (b.y > loc.y)):
                x_intersect = (b.x-a.x)*(loc.y-a.y)/(b.y-a.y) + a.x
                if loc.x < x_intersect:
                    inside = not inside
        if inside:
            return 0.0
        best = float('inf')
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            dx, dy = b.x-a.x, b.y-a.y
            t = max(0.0, min(1.0, ((loc.x-a.x)*dx+(loc.y-a.y)*dy) /
                             max(dx*dx+dy*dy, 1e-9)))
            best = min(best, math.hypot(loc.x-(a.x+t*dx), loc.y-(a.y+t*dy)))
        return best

    matches = []
    for d in range(int(minimum), int(maximum)+1):
        route_wp = _ahead(origin, float(d))
        if route_wp is None:
            break
        loc = route_wp.transform.location
        for idx, poly in enumerate(polygons):
            gap = distance_to_polygon(loc, poly)
            if gap <= 1.0:
                matches.append((idx, d, route_wp, gap))
    if not matches:
        return None, None
    # Group consecutive samples of the same zebra; choose the crossing closest
    # to the nominal second-event distance rather than an adjacent intersection.
    by_polygon = {}
    for idx, d, wp, gap in matches:
        by_polygon.setdefault(idx, []).append((d, wp, gap))
    target = 85.0 if minimum >= 70 else (minimum+maximum)/2.0
    chosen = min(by_polygon.values(), key=lambda items:
                 abs(sum(x[0] for x in items)/len(items)-target))
    # Use the centre of the mapped zebra along the ego's own lane.
    d, wp, gap = chosen[len(chosen)//2]
    return float(d), wp


class RealisticWalker(object):
    """Human-scale, stateful pedestrian controller using CARLA WalkerControl."""
    def __init__(self, ped, behavior, start, finish, delay=0.0):
        self.ped, self.behavior, self.start, self.finish = ped, behavior, start, finish
        self.delay, self.elapsed = delay, 0.0
        self.active, self.done = False, False
        self.speed = 0.0
        self.origin = None
        self.stage = 0
        self.stage_time = 0.0
        self.heading = carla.Vector3D(1.0, 0.0, 0.0)
        self.cross = carla.Vector3D(0.0, 1.0, 0.0)

    def start_behavior(self):
        self.active = True
        self.origin = self.ped.get_location()
        dx = self.finish.x - self.origin.x
        dy = self.finish.y - self.origin.y
        norm = max(math.hypot(dx, dy), 0.001)
        self.heading = carla.Vector3D(dx/norm, dy/norm, 0.0)
        self.cross = carla.Vector3D(-dy/norm, dx/norm, 0.0)
        try:
            self.ped.set_simulate_physics(True)
        except Exception:
            pass
        print('PEDESTRIAN START: %s delay=%.1fs' % (self.behavior, self.delay))

    def _point(self, forward, lateral=0.0):
        return carla.Location(
            x=self.origin.x + forward*self.heading.x + lateral*self.cross.x,
            y=self.origin.y + forward*self.heading.y + lateral*self.cross.y,
            z=self.origin.z)

    def update(self, ego, dt):
        if not self.active or self.done or not self.ped.is_alive:
            return
        dt = min(max(float(dt), 0.0), 0.15)
        self.elapsed += dt
        if self.elapsed < self.delay:
            self.ped.apply_control(carla.WalkerControl(direction=self.heading, speed=0.0))
            return
        self.stage_time += dt
        loc = self.ped.get_location()
        behavior = self.behavior

        if behavior == 'waiting':
            # Not planning to cross: stay on sidewalk.
            target, desired = self.origin, 0.0
        elif behavior == 'hesitant':
            # Approach curb, freeze, retreat. Never cross the roadway.
            # The first 0.65 m is an approach only; no forward crossing goal.
            phases = [(0.65, 0.55, 2.2), (0.65, 0.0, 2.0),
                      (-0.35, 0.50, 2.1), (-0.35, 0.0, 2.4)]
            if self.stage >= len(phases):
                # One-time hesitation complete: remain at the retreated position.
                target, desired = self._point(-0.35), 0.0
            else:
                forward, desired, duration = phases[self.stage]
                target = self._point(forward)
                if self.stage_time >= duration:
                    self.stage += 1
                    self.stage_time = 0.0
        elif behavior == 'aggressive':
            # Restless movements along the sidewalk, not a perpetual sprint
            # and not an automatic road crossing.
            phases = [(0.0, -1.3, 1.45, 2.0), (0.0, -1.3, 0.0, 0.7),
                      (0.0, 1.1, 1.6, 2.6), (0.0, 1.1, 0.0, 0.8),
                      (0.0, -0.5, 1.35, 1.7)]
            forward, lateral, desired, duration = phases[self.stage % len(phases)]
            target = self._point(forward, lateral)
            if self.stage_time >= duration:
                self.stage += 1
                self.stage_time = 0.0
        elif behavior == 'distracted':
            # Crossing is possible, but with intermittent slowdowns.
            # Walking motion alone cannot visually prove phone use.
            phase = self.elapsed % 8.5
            desired = 0.55 if phase < 1.8 else (1.0 if phase < 5.5 else 0.65)
            target = self.finish
        elif behavior == 'jaywalk':
            # Crossing outside the zebra: classification depends on location,
            # not speed alone.
            target, desired = self.finish, 1.4
        else:  # committed
            target, desired = self.finish, 1.25

        dx, dy = target.x-loc.x, target.y-loc.y
        dist = math.hypot(dx, dy)
        if behavior in ('committed', 'distracted', 'jaywalk') and dist < 0.8:
            self.done = True
            desired = 0.0
            print('PEDESTRIAN COMPLETED: %s' % behavior)
        elif behavior in ('hesitant', 'aggressive') and dist < 0.17:
            desired = 0.0

        acceleration = 1.2 if desired > self.speed else 1.8
        step = acceleration * dt
        self.speed += max(-step, min(step, desired-self.speed))
        direction = carla.Vector3D(dx/dist, dy/dist, 0.0) if dist > 0.02 else self.heading
        self.ped.apply_control(carla.WalkerControl(direction=direction, speed=self.speed))

def _spawn_groups(world, actors, vehicle):
    origin=world.get_map().get_waypoint(vehicle.get_location(),project_to_road=True)
    cw_distance,cw_wp=_crosswalk_waypoint(world,origin)
    if cw_wp is not None:
        print('REAL MAPPED CROSSWALK selected at route %.1fm' % cw_distance)
        first_wp=cw_wp
    else:
        print('WARNING: No mapped zebra crossing along first 75m; first event is an ordinary crossing.')
        first_wp=_ahead(origin,35.0)
    # Separate pedestrians at the same crossing, both starting on the sidewalk.
    planned=[('crosswalk',first_wp,[('committed',-1.0,1,0.0),('committed',1.1,1,1.8)])]
    for d,behavior in [(85,'distracted'),(135,'jaywalk'),(190,'aggressive'),(245,'hesitant')]:
        wp=_ahead(origin,d)
        if behavior == 'distracted':
            # Event 2: use the existing mapped zebra, not the arbitrary 85m point.
            # Keep the original ego spawn, route, camera, and other events untouched.
            zebra_distance, zebra_wp = _crosswalk_waypoint(world, origin, minimum=72.0, maximum=125.0)
            if zebra_wp is not None:
                wp=zebra_wp
                print('EVENT 2: distracted pedestrian aligned with REAL zebra at %.1fm' % zebra_distance)
            else:
                print('WARNING: no mapped zebra for event 2 between 72m and 125m; retaining original 85m location.')
        if wp is not None:
            if behavior=='aggressive':
                members=[('aggressive',-1.4,1,0),('aggressive',1.4,1,0)]
            elif behavior=='hesitant':
                members=[('waiting',-2.0,1,0),('hesitant',1.5,1,2.0)]
            elif behavior=='distracted':
                # Event 2 only: one crossing child and two people on the same sidewalk.
                # Waiting stays put; hesitant approaches the curb then retreats.
                members=[('distracted',0.0,1,0.0),
                         ('waiting',-3.5,1,0.0),
                         ('hesitant',3.5,1,1.0)]
            else:
                members=[(behavior,0.0,1,0.0)]
            planned.append((str(d)+'m',wp,members))
    groups=[]
    for event_name,wp,members in planned:
        if wp is None: continue
        right=wp.transform.get_right_vector(); forward=wp.transform.get_forward_vector()
        center=wp.transform.location; half=max(1.8,wp.lane_width/2.0)
        group=[]
        for j,(behavior,along,side,delay) in enumerate(members):
            side_distance=half+(2.1 if behavior in ('aggressive','waiting') else 1.0)
            start=carla.Location(x=center.x+forward.x*along+right.x*side*side_distance,
                                 y=center.y+forward.y*along+right.y*side*side_distance,z=center.z+0.7)
            finish=carla.Location(x=center.x+forward.x*along-right.x*side*(half+1.5),
                                  y=center.y+forward.y*along-right.y*side*(half+1.5),z=center.z+0.7)
            spec=ScenarioSpec(id='realistic_%s_%d'%(event_name,j),behavior=behavior,
                 description='Realistic sequential pedestrian interaction',ego_cruise_kmh=20.0,
                 preferred_gender='female' if j%2 else 'male',
                 preferred_age='child' if behavior=='distracted' else 'adult',
                 scenario_seed_offset=101+j*31)
            geom={'start':start,'finish':finish,'center':start,'waypoint':wp,
                  'road_forward':forward,'road_right':right,
                  'real_crosswalk':(event_name=='crosswalk' and cw_wp is not None) or
                  (event_name=='85m' and behavior=='distracted' and zebra_wp is not None)}
            try:
                ped,actual,yaw=base.spawn_pedestrian(world,actors,geom,spec)
                # CARLA's blueprint library determines appearance; age/gender preferences
                # depend on whether base.spawn_pedestrian supports those filters.
                ctrl=RealisticWalker(ped,behavior,actual,finish,delay)
                group.append((ped,ctrl,spec))
            except Exception as exc:
                print('Spawn failed %s: %s'%(behavior,exc))
        groups.append((event_name,wp,group))
        print('EVENT %s: %d walkers'%(event_name,len(group)))
    return groups


def _update_events(groups,vehicle,activated,dt):
    ego=vehicle.get_location()
    for name,wp,group in groups:
        if not group: continue
        distances=[_xy_distance(ego,ped.get_location()) for ped,_,_ in group if ped.is_alive]
        if not distances: continue
        if name not in activated and min(distances)<27.0:
            activated.add(name)
            print('EVENT ACTIVATED %s'%name)
            for ped,ctrl,spec in group:
                if ped.is_alive: ctrl.start_behavior()
        if name in activated:
            for ped,ctrl,spec in group:
                if ped.is_alive: ctrl.update(ego,dt)


def _scenario_safety(groups,vehicle,activated):
    """Ground-truth safety override for the *simulation*; ML still runs normally.
    Release the brake once the pedestrian clears the driving corridor.
    """
    ego=vehicle.get_location()
    transform=vehicle.get_transform()
    forward=transform.get_forward_vector(); right=transform.get_right_vector()
    highest='MAINTAIN'; priority={'MAINTAIN':0,'SLOW_DOWN':1,'STOP':2}
    for name,wp,group in groups:
        if name not in activated: continue
        for ped,ctrl,spec in group:
            if not ped.is_alive or ctrl.done: continue
            delta=ped.get_location()-ego
            longitudinal=delta.x*forward.x+delta.y*forward.y
            lateral=abs(delta.x*right.x+delta.y*right.y)
            # Only brake for pedestrians ahead and near the current lane.
            # Waiting/arguing on the pavement must not block the vehicle forever.
            if spec.behavior in ('waiting','aggressive'): continue
            # Event 2 hesitant walker only approaches/retreats at the curb;
            # it must not hold the ego vehicle at STOP indefinitely.
            if name == '85m' and spec.behavior == 'hesitant': continue
            if -2.5 < longitudinal < 12.0 and lateral < 3.4:
                action='STOP'
            elif 0.0 < longitudinal < 25.0 and lateral < 6.0:
                action='SLOW_DOWN'
            else: action='MAINTAIN'
            if priority[action]>priority[highest]: highest=action
    return highest

def _camera_rgb(image):
    array = np.frombuffer(image.raw_data, dtype=np.uint8).reshape(image.height,image.width,4)
    return array[:,:,:3][:,:,::-1].copy()


def _crop(rgb, box):
    x1,y1,x2,y2 = [int(v) for v in box]
    # Include limbs that tight YOLO boxes often truncate.
    pad_x=int((x2-x1)*0.12); pad_y=int((y2-y1)*0.10)
    x1-=pad_x; x2+=pad_x; y1-=pad_y; y2+=pad_y
    x1=max(0,x1); y1=max(0,y1); x2=min(rgb.shape[1],x2); y2=min(rgb.shape[0],y2)
    if x2-x1 < 30 or y2-y1 < 30:
        return None
    return rgb[y1:y2,x1:x2].copy()


def _project_box(ped, camera):
    try:
        vertices = ped.bounding_box.get_world_vertices(ped.get_transform())
        pts = [base.project_point(v,camera) for v in vertices]
        pts = [p for p in pts if p is not None]
        if len(pts)<4: return None
        return [min(p[0] for p in pts),min(p[1] for p in pts),
                max(p[0] for p in pts),max(p[1] for p in pts)]
    except Exception:
        return None


def _detections_a(groups, vehicle, camera, rgb):
    out=[]
    for _,_,group in groups:
        for ped,_,spec in group:
            if not ped.is_alive: continue
            box=_project_box(ped,camera)
            if box is None: continue
            distance=_xy_distance(vehicle.get_location(),ped.get_location())
            if distance>65: continue
            out.append(dict(id=str(ped.id), box=box, distance=distance, actor=ped, spec=spec))
    return out


def _detections_b(rgb, url):
    # YOLO/ByteTrack runs under Python 3.12 in a separate HTTP process.
    import io
    from PIL import Image
    output=io.BytesIO()
    Image.fromarray(rgb).save(output,format='JPEG',quality=78)
    req=urllib.request.Request(url,data=output.getvalue(),headers={'Content-Type':'image/jpeg'},method='POST')
    with urllib.request.urlopen(req,timeout=8) as response:
        tracks=json.loads(response.read().decode('utf-8'))['tracks']
    focal=(rgb.shape[1]/2.0)/math.tan(math.radians(base.CAMERA_FOV/2.0))
    for item in tracks:
        box=item['box']; height=max(1.0,box[3]-box[1])
        # Approximate monocular distance; not CARLA ground truth or metric depth.
        item['distance']=min(100.0,1.7*focal/height)
        item['actor']=None
        item['spec']=None
        item['id']=str(item['id'])
    return tracks


class StableTrackIDs(object):
    """Short-gap image-space association across ByteTrack ID switches.
    Not a re-identification model; ambiguous overlaps can still be wrong.
    """
    def __init__(self):
        self.active={}; self.counter=0; self.switches=0

    def assign(self, detections, frame):
        used=set()
        for d in detections:
            box=d['box']; cx=(box[0]+box[2])*0.5; cy=(box[1]+box[3])*0.5
            h=max(1.0,box[3]-box[1]); raw=d['id']
            best=None; best_score=1e9
            for stable,t in self.active.items():
                if stable in used or frame-t['frame']>12: continue
                dist=math.hypot(cx-t['cx'],cy-t['cy'])
                scale=max(h,t['h'],1.0)
                if dist>0.75*scale: continue
                penalty=0.0 if raw==t['raw'] else 0.15*scale
                score=dist+penalty
                if score<best_score: best,best_score=stable,score
            if best is None:
                self.counter+=1; best='s%d'%self.counter
            elif raw!=self.active[best]['raw']:
                self.switches+=1
                print('TRACK REASSOC stable=%s old_yolo=%s new_yolo=%s' %
                      (best,self.active[best]['raw'],raw))
            self.active[best]={'cx':cx,'cy':cy,'h':h,'raw':raw,'frame':frame}
            used.add(best); d['raw_id']=raw; d['id']=best
        for k in list(self.active):
            if frame-self.active[k]['frame']>60: del self.active[k]
        return detections


def _ground_truth_match(groups, detection, camera):
    """Evaluation only: match YOLO image box to simulated actor projection."""
    box=detection['box']; cx=(box[0]+box[2])*0.5; cy=(box[1]+box[3])*0.5
    best=None; distance=1e9
    for _,_,group in groups:
        for ped,ctrl,spec in group:
            if not ped.is_alive: continue
            pb=_project_box(ped,camera)
            if pb is None: continue
            pcx=(pb[0]+pb[2])*0.5; pcy=(pb[1]+pb[3])*0.5
            delta=math.hypot(cx-pcx,cy-pcy)
            if delta<distance:
                distance=delta; best=(str(ped.id),spec.behavior,delta)
    if best and distance < max(35.0,(box[3]-box[1])*0.6): return best
    return None


def _context(world, vehicle, detection, crosswalks):
    if detection['actor'] is not None:
        return base.get_context(world,vehicle,detection['actor'],crosswalks,spec=detection['spec'])
    # Unknown from monocular camera; neutral/missing proxies are NOT measured context.
    return {'traffic_light_state':-1.0,'vehicle_distance_norm':min(1.0,detection['distance']/50.0),
            'crosswalk_presence':0.0,'road_width_norm':0.33,'pedestrian_density':0.0,
            'distance_to_curb_norm':1.0}


def _in_path(vehicle, detection, image_width):
    box=detection['box']; center=(box[0]+box[2])/2.0
    # A conservative central-image corridor heuristic; not trajectory prediction.
    return abs(center-image_width/2.0) < image_width*0.30


def update_spectator_follow(world, vehicle):
    """Move CARLAUE4 spectator to a chase view behind the ego vehicle."""
    transform = vehicle.get_transform()
    forward = transform.get_forward_vector()
    location = transform.location
    chase_location = carla.Location(
        x=location.x - 7.0 * forward.x,
        y=location.y - 7.0 * forward.y,
        z=location.z + 3.0,
    )
    chase_rotation = carla.Rotation(
        pitch=-12.0, yaw=transform.rotation.yaw, roll=0.0
    )
    world.get_spectator().set_transform(carla.Transform(chase_location, chase_rotation))


def run(mode, host, port, seconds, yolo_url):
    client=carla.Client(host,port); client.set_timeout(60.0)
    world=client.get_world(); original=world.get_settings()
    actors=base.ActorManager(); trackers={}; history={}; predictions={}; last_seen={}; stable_ids=StableTrackIDs()
    evaluation=[]
    agent=base.RuleBasedAgent()
    settings=world.get_settings(); settings.synchronous_mode=True
    settings.fixed_delta_seconds=base.FIXED_DELTA_SECONDS
    world.apply_settings(settings)
    try:
        base.clear_stale_actors(world)
        vehicle=base.spawn_vehicle(world,actors,1)
        update_spectator_follow(world, vehicle)
        camera=base.attach_camera(world,actors,vehicle)
        buffer=base.CameraBuffer(); camera.listen(buffer.callback)
        groups=_spawn_groups(world,actors,vehicle)
        crosswalks=world.get_map().get_crosswalks() if hasattr(world.get_map(),'get_crosswalks') else []
        base.start_web_stream_server()
        base.SHARED.update_status(phase='running',scenario_id='dynamic_multi_ped_'+mode,
                                  message='Multi-pedestrian mode '+mode, pedestrians=[])
        last_frame=-1; action='MAINTAIN'; previous_logged_action=None; activated=set(); clear_frames=0
        stride=1  # collect every simulation frame; 30 samples needed per pedestrian
        for frame in range(int(seconds/base.FIXED_DELTA_SECONDS)):
            if base._STOP_REQUESTED.is_set(): break
            _update_events(groups, vehicle, activated, base.FIXED_DELTA_SECONDS)
            steer=base.compute_steer(world,vehicle)
            base.drive_vehicle(vehicle,20.0,action=action,steer=steer)
            world.tick()
            applied_control = vehicle.get_control()
            print('VEHICLE_CONTROL t=%.2fs input_action=%s steer=%.3f throttle=%.3f brake=%.3f' % (
                frame*base.FIXED_DELTA_SECONDS, action, applied_control.steer,
                applied_control.throttle, applied_control.brake), flush=True)
            update_spectator_follow(world, vehicle)
            if frame%stride: continue
            image=buffer.last_image
            if image is None or image.frame==last_frame: continue
            last_frame=image.frame; rgb=_camera_rgb(image)
            try:
                detections=(_detections_a(groups,vehicle,camera,rgb) if mode=='A'
                            else _detections_b(rgb,yolo_url))
            except Exception as exc:
                print('Detection error: %s' % exc); detections=[]
            if mode=='B': detections=stable_ids.assign(detections,frame)
            current=[]; ttc_candidates=[]; priority={'MAINTAIN':0,'SLOW_DOWN':1,'STOP':2}
            velocity=vehicle.get_velocity(); speed_kmh=math.hypot(velocity.x,velocity.y)*3.6
            for d in detections:
                tid=d['id']; crop=_crop(rgb,d['box'])
                gt=_ground_truth_match(groups,d,camera) if mode=='B' else None
                if crop is None: continue
                if tid not in trackers:
                    trackers[tid]=base.LiveML(); history[tid]=deque(maxlen=8)
                last_seen[tid]=frame
                context=_context(world,vehicle,d,crosswalks)
                features,landmarks=trackers[tid].process(crop,frame,context)
                hist=history[tid]; hist.append((frame,d['distance']))
                closing=None
                if len(hist)>=2:
                    dt=(hist[-1][0]-hist[0][0])*base.FIXED_DELTA_SECONDS
                    if dt>0: closing=(hist[0][1]-hist[-1][1])/dt
                ml=trackers[tid]
                if ml.last_prediction_frame==frame and ml.last_prediction is not None:
                    predictions[tid]=ml.last_prediction
                    print('  ML PREDICTION id=%s state=%s confidence=%s' % (
                        tid, base.LABELS.get(ml.last_prediction.get('mental_state')),
                        ml.last_prediction.get('confidence')))
                pred=predictions.get(tid)
                if gt and pred and ml.last_prediction_frame==frame:
                    evaluation.append({'frame':frame,'time_s':round(frame*base.FIXED_DELTA_SECONDS,2),
                                       'stable_id':tid,'yolo_id':d.get('raw_id',tid),
                                       'actor_id':gt[0],'ground_truth':gt[1],
                                       'prediction':LABELS.get(pred.get('mental_state'),'Unknown'),
                                       'confidence':pred.get('confidence'),
                                       'pose_ok':ml.pose_ok,'pose_fail':ml.pose_fail,
                                       'match_pixel_error':round(gt[2],1)})
                if frame % 20 == 0 and pred is None:
                    print('  ML WARMUP id=%s samples=%d/%d pose_ok=%d pose_fail=%d crop=%s' % (
                        tid, len(ml.features), base.WINDOW_SIZE, ml.pose_ok, ml.pose_fail, ml.crop_size_str()))
                state=pred.get('mental_state') if pred else None
                confidence=pred.get('confidence') if pred else None
                # No fabricated class/confidence when insufficient model data.
                decision=None; ped_action='MAINTAIN'
                if state is not None:
                    decision=agent.decide(features,state,confidence=confidence,
                                          vehicle_speed_kmh=speed_kmh,distance_m=d['distance'],
                                          closing_speed_ms=closing)
                    ped_action=decision['action']
                # Conservative physical safety fallback even before 30-frame prediction.
                if _in_path(vehicle,d,rgb.shape[1]):
                    stop_dist=(speed_kmh/3.6)**2/(2*base.MAX_DECEL_MPS2)+base.SAFETY_MARGIN_M
                    if d['distance'] < stop_dist+2.0: ped_action='STOP'
                    elif d['distance']<max(15.0,stop_dist+8.0) and priority[ped_action]<1:
                        ped_action='SLOW_DOWN'
                else:
                    # Do not stop for pedestrians clearly outside image-space driving corridor.
                    ped_action='MAINTAIN'
                # Collect TTC for each pedestrian in the driving corridor.
                # Only finite, nonnegative TTCs are comparable.
                ttc = decision.get('ttc') if decision is not None else None
                if (ttc is not None and math.isfinite(ttc) and ttc >= 0
                        and _in_path(vehicle, d, rgb.shape[1])):
                    ttc_candidates.append((ttc, tid, ped_action))
                current.append({'id':tid,'state':LABELS.get(state) if state is not None else None,
                                'confidence':confidence,'distance_m':round(d['distance'],2),
                                'action':ped_action,'ttc_s':decision.get('ttc') if decision and math.isfinite(decision['ttc']) else None,
                                'box':d['box'],'ground_truth':gt[1] if gt else None,'reason':decision.get('reason') if decision else None})
                if decision is None:
                    print('RULE_AGENT t=%.2fs id=%s state=N/A TTC=N/A level=N/A rule_action=N/A effective_ped_action=%s reason=ML_prediction_not_ready distance=%.2fm closing_speed=%s' % (
                        frame*base.FIXED_DELTA_SECONDS, tid, ped_action, d['distance'],
                        ('%.2fm/s' % closing) if closing is not None else 'N/A'), flush=True)
                if decision is not None:
                    ttc_value = decision.get('ttc')
                    ttc_text = ('%.2fs' % ttc_value) if ttc_value is not None and math.isfinite(ttc_value) else 'N/A'
                    print('RULE_AGENT t=%.2fs id=%s state=%s TTC=%s level=%s rule_action=%s effective_ped_action=%s reason=%s' % (
                        frame*base.FIXED_DELTA_SECONDS, tid, decision.get('state_name'),
                        ttc_text, decision.get('ttc_level'), decision.get('action'),
                        ped_action, decision.get('reason')), flush=True)
            for tid in list(trackers):
                if frame-last_seen.get(tid,frame)>60:
                    del trackers[tid]; history.pop(tid,None); predictions.pop(tid,None); last_seen.pop(tid,None)
            
            scenario_action='DISABLED'
            if ttc_candidates:
                min_ttc, selected_id, action = min(ttc_candidates, key=lambda item: item[0])
            else:
                
                action = 'MAINTAIN'
                for ped_info in current:
                    if priority[ped_info['action']] > priority[action]:
                        action = ped_info['action']
                min_ttc, selected_id = None, None
            if True:
                print('CONTROL_DECISION t=%.2fs speed=%.2fkm/h selected_id=%s min_ttc=%s scenario_override=%s final_action=%s' % (
                    frame*base.FIXED_DELTA_SECONDS, speed_kmh, selected_id,
                    ('%.2fs' % min_ttc) if min_ttc is not None else 'N/A', scenario_action, action), flush=True)
                previous_logged_action = action
            base.SHARED.update_status(elapsed_s=frame*base.FIXED_DELTA_SECONDS,
                                      action=action,pedestrians=current,pedestrian_count=len(current),
                                      message='Mode %s: %s visible, action %s' % (mode,len(current),action))
            if frame%20==0:
                print('t=%.1f mode=%s visible=%d action=%s %s' %
                      (frame*base.FIXED_DELTA_SECONDS,mode,len(current),action,
                       [(p['id'],p['state'],p['action']) for p in current]))
        # Save per-frame matched predictions and a frame-level confusion matrix.
        if evaluation:
            with open('mental_state_evaluation.csv','w') as f:
                writer=csv.DictWriter(f,fieldnames=list(evaluation[0].keys()))
                writer.writeheader(); writer.writerows(evaluation)
            names=['Waiting','Hesitant','Committed','Distracted','Aggressive','Jaywalk']
            matrix={gt:{pr:0 for pr in names} for gt in names}
            for row in evaluation:
                gt=row['ground_truth'].capitalize(); pr=row['prediction']
                if gt in matrix and pr in matrix[gt]: matrix[gt][pr]+=1
            with open('mental_state_confusion.csv','w') as f:
                writer=csv.writer(f); writer.writerow(['GT / predicted']+names)
                for gt in names: writer.writerow([gt]+[matrix[gt][pr] for pr in names])
            correct=sum(r['ground_truth'].lower()==r['prediction'].lower() for r in evaluation)
            print('EVALUATION: %d/%d matched prediction frames correct (%.1f%%); ID reassociations=%d' %
                  (correct,len(evaluation),100.0*correct/len(evaluation),stable_ids.switches))
            print('Saved mental_state_evaluation.csv and mental_state_confusion.csv')
        else:
            print('EVALUATION: no matched predictions; check pose/tracking before claiming accuracy.')
        base.SHARED.update_status(phase='finished',finished=True,action='STOP')
        base.drive_vehicle(vehicle,0.0,action='STOP',steer=0.0)
    finally:
        for tracker in trackers.values():
            try: tracker.close()
            except Exception: pass
        actors.cleanup()
        world.apply_settings(original)


def cli(mode):
    parser=argparse.ArgumentParser(description='CARLA multi-pedestrian %s' % mode)
    parser.add_argument('--host',default='localhost'); parser.add_argument('--port',type=int,default=2000)
    parser.add_argument('--seconds',type=float,default=45.0)
    parser.add_argument('--yolo-url',default='http://127.0.0.1:8094/track')
    args=parser.parse_args()
    run(mode,args.host,args.port,args.seconds,args.yolo_url)
