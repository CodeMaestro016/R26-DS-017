from __future__ import annotations

import argparse
import math
import queue
from pathlib import Path

import carla
import cv2
import numpy as np


WIDTH = 800
HEIGHT = 600
FOV = 90.0
DT = 0.05


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=2000)
    p.add_argument("--map", dest="map_name", default="Town03")
    p.add_argument("--frames", type=int, default=180)
    p.add_argument(
        "--output",
        default="outputs/carla/carla_occluded_pedestrian_smoke.mp4",
    )
    p.add_argument("--no-display", action="store_true")
    return p.parse_args()


def offset(transform, forward, right, up=0.0):
    f = transform.get_forward_vector()
    r = transform.get_right_vector()
    return carla.Location(
        x=transform.location.x + f.x * forward + r.x * right,
        y=transform.location.y + f.y * forward + r.y * right,
        z=transform.location.z + up,
    )


def find_first(lib, ids, fallback_filter):
    for blueprint_id in ids:
        try:
            return lib.find(blueprint_id)
        except RuntimeError:
            pass

    matches = list(lib.filter(fallback_filter))
    if not matches:
        raise RuntimeError(f"No blueprint matches {fallback_filter}")
    return matches[0]


def spawn_ego(world, bp):
    for transform in world.get_map().get_spawn_points():
        actor = world.try_spawn_actor(bp, transform)
        if actor is not None:
            actor.set_simulate_physics(False)
            return actor
    raise RuntimeError("Could not spawn ego vehicle.")


def spawn_static(world, bp, transform):
    transform.location.z += 0.25
    actor = world.try_spawn_actor(bp, transform)
    if actor is None:
        transform.location.x += 0.5
        transform.location.z += 0.25
        actor = world.try_spawn_actor(bp, transform)
    if actor is None:
        raise RuntimeError(f"Could not spawn {bp.id}")
    actor.set_simulate_physics(False)
    return actor


def to_bgr(image):
    data = np.frombuffer(image.raw_data, dtype=np.uint8)
    return data.reshape(image.height, image.width, 4)[:, :, :3].copy()


def camera_matrix():
    focal = WIDTH / (2.0 * math.tan(math.radians(FOV) / 2.0))
    k = np.eye(3, dtype=np.float64)
    k[0, 0] = focal
    k[1, 1] = focal
    k[0, 2] = WIDTH / 2.0
    k[1, 2] = HEIGHT / 2.0
    return k


def project_bbox(actor, camera, k):
    vertices = actor.bounding_box.get_world_vertices(actor.get_transform())
    w2c = np.asarray(camera.get_transform().get_inverse_matrix())
    points = []

    for v in vertices:
        p = w2c @ np.array([v.x, v.y, v.z, 1.0])
        p = np.array([p[1], -p[2], p[0]], dtype=np.float64)
        if p[2] <= 0.1:
            continue
        q = k @ p
        points.append((q[0] / q[2], q[1] / q[2]))

    if len(points) < 2:
        return None

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x1 = int(np.clip(np.floor(min(xs)), 0, WIDTH - 1))
    y1 = int(np.clip(np.floor(min(ys)), 0, HEIGHT - 1))
    x2 = int(np.clip(np.ceil(max(xs)), 1, WIDTH))
    y2 = int(np.clip(np.ceil(max(ys)), 1, HEIGHT))

    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def overlap_ratio(target, occluder):
    if target is None or occluder is None:
        return 0.0
    tx1, ty1, tx2, ty2 = target
    ox1, oy1, ox2, oy2 = occluder
    iw = max(0, min(tx2, ox2) - max(tx1, ox1))
    ih = max(0, min(ty2, oy2) - max(ty1, oy1))
    return float(iw * ih / max((tx2 - tx1) * (ty2 - ty1), 1))


def occ_label(value):
    if value >= 0.50:
        return "HIGH"
    if value >= 0.15:
        return "MEDIUM"
    return "LOW"


def draw_box(frame, box, label, color):
    if box is None:
        return
    x1, y1, x2, y2 = box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        frame, label, (x1, max(18, y1 - 7)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA
    )


def text(frame, value, y):
    cv2.putText(
        frame, value, (15, y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.57, (0, 0, 0), 4, cv2.LINE_AA
    )
    cv2.putText(
        frame, value, (15, y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.57, (255, 255, 255), 2, cv2.LINE_AA
    )


def main():
    cfg = args()
    client = carla.Client(cfg.host, cfg.port)
    client.set_timeout(30.0)

    print("=" * 78)
    print("CARLA OCCLUDED-PEDESTRIAN SCENE SMOKE TEST")
    print("=" * 78)
    print("Client:", client.get_client_version())
    print("Server:", client.get_server_version())

    world = client.get_world()
    current = world.get_map().name.split("/")[-1]

    if cfg.map_name and current != cfg.map_name:
        print(f"Loading {cfg.map_name} (current: {current})...")
        world = client.load_world(cfg.map_name)

    print("Map   :", world.get_map().name)

    original_settings = world.get_settings()
    actors = []
    camera_queue = queue.Queue()
    writer = None
    camera = None

    try:
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = DT
        settings.no_rendering_mode = False
        world.apply_settings(settings)

        lib = world.get_blueprint_library()

        ego_bp = find_first(
            lib,
            ["vehicle.tesla.model3", "vehicle.lincoln.mkz_2020"],
            "vehicle.*",
        )
        ego = spawn_ego(world, ego_bp)
        actors.append(ego)
        base = ego.get_transform()

        van_bp = find_first(
            lib,
            [
                "vehicle.mercedes.sprinter",
                "vehicle.volkswagen.t2",
                "vehicle.ford.ambulance",
            ],
            "vehicle.*",
        )
        van = spawn_static(
            world,
            van_bp,
            carla.Transform(
                offset(base, 13.0, 2.0),
                base.rotation,
            ),
        )
        actors.append(van)

        walker_bp = find_first(
            lib,
            [],
            "walker.pedestrian.*",
        )
        walker_rotation = carla.Rotation(yaw=base.rotation.yaw + 90.0)
        walker = spawn_static(
            world,
            walker_bp,
            carla.Transform(
                offset(base, 17.0, 2.0),
                walker_rotation,
            ),
        )
        actors.append(walker)

        camera_bp = lib.find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", str(WIDTH))
        camera_bp.set_attribute("image_size_y", str(HEIGHT))
        camera_bp.set_attribute("fov", str(FOV))
        camera_bp.set_attribute("sensor_tick", str(DT))

        camera = world.spawn_actor(
            camera_bp,
            carla.Transform(carla.Location(x=1.5, z=1.8)),
            attach_to=ego,
            attachment_type=carla.AttachmentType.Rigid,
        )
        actors.append(camera)
        camera.listen(camera_queue.put)

        world.get_spectator().set_transform(
            carla.Transform(
                offset(base, -6.0, 0.0, 8.0),
                carla.Rotation(pitch=-25.0, yaw=base.rotation.yaw),
            )
        )

        output = Path(cfg.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            str(output),
            cv2.VideoWriter_fourcc(*"mp4v"),
            1.0 / DT,
            (WIDTH, HEIGHT),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not create {output}")

        k = camera_matrix()

        for _ in range(5):
            world.tick()
            camera_queue.get(timeout=10.0)

        print("Ego ID      :", ego.id)
        print("Van ID      :", van.id)
        print("Walker ID   :", walker.id)
        print("Camera ID   :", camera.id)
        print("Press q or ESC to stop.")

        completed = 0

        for index in range(cfg.frames):
            progress = 0.0 if index < 35 else min((index - 35) / 105.0, 1.0)
            right_offset = 2.0 - 6.0 * progress

            walker.set_transform(
                carla.Transform(
                    offset(base, 17.0, right_offset),
                    walker_rotation,
                )
            )

            world.tick()
            image = camera_queue.get(timeout=10.0)
            frame = to_bgr(image)

            walker_box = project_bbox(walker, camera, k)
            van_box = project_bbox(van, camera, k)
            ratio = overlap_ratio(walker_box, van_box)

            draw_box(frame, van_box, "PARKED OCCLUDER", (255, 160, 0))
            draw_box(frame, walker_box, "TARGET PEDESTRIAN", (0, 255, 0))
            text(frame, "CARLA controlled occluded-pedestrian scene", 28)
            text(frame, f"Frame {index + 1}/{cfg.frames} | Walker ID {walker.id}", 55)
            text(
                frame,
                f"BBox overlap proxy {ratio:.3f} | Occlusion {occ_label(ratio)}",
                82,
            )
            text(frame, "Smoke test only: intent model is not connected yet", 109)

            writer.write(frame)
            completed += 1

            if not cfg.no_display:
                cv2.imshow("CARLA scene smoke test", frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break

        print()
        print("=" * 78)
        print("CARLA SCENE SMOKE TEST COMPLETE")
        print("=" * 78)
        print("Frames:", completed)
        print("Output:", output)
        print("Status: PASSED")
        print("=" * 78)

    finally:
        if camera is not None:
            try:
                camera.stop()
            except RuntimeError:
                pass

        if writer is not None:
            writer.release()

        cv2.destroyAllWindows()

        for actor in reversed(actors):
            try:
                if actor.is_alive:
                    actor.destroy()
            except RuntimeError:
                pass

        world.apply_settings(original_settings)


if __name__ == "__main__":
    main()
