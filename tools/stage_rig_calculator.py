#!/usr/bin/env python3
"""
stage_rig_calculator.py - engineering calculator for a live-theatre capture
and projection system built around a real-time engine.

It answers the questions that decide whether such a system works at all,
before any money is spent:

  1. CAMERAS    - required focal length and field of view to cover the volume,
                  and the resulting body height in pixels near and far.
  2. EXPOSURE   - the shutter limit imposed by motion blur, and the scene
                  illuminance that limit demands.
  3. NETWORK    - per-camera and aggregate bandwidth, checked against common links.
  4. PROJECTION - screen luminance for a given surface, gain and projector output.
  5. LATENCY    - end-to-end budget from movement to projected image.

No dependencies beyond the Python standard library.

Written for the theatre production "Queen Anne" and released under the MIT
licence as part of the Live Stage Toolkit.

Examples
--------
    python3 stage_rig_calculator.py --width 7 --depth 6 --rig-height 4.5 \
        --performers 4 --cameras 6 --preset imx250 --fps 60

    python3 stage_rig_calculator.py --width 10 --depth 10 --rig-height 6 \
        --cameras 8 --projectors 2 --projector-lumens 12000

    python3 stage_rig_calculator.py --selftest
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Sensors. Global shutter unless stated otherwise.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Sensor:
    name: str
    width_px: int
    height_px: int
    pixel_um: float
    global_shutter: bool
    nir_capable: bool
    note: str = ""

    @property
    def width_mm(self) -> float:
        return self.width_px * self.pixel_um / 1000.0

    @property
    def height_mm(self) -> float:
        return self.height_px * self.pixel_um / 1000.0

    @property
    def megapixels(self) -> float:
        return self.width_px * self.height_px / 1e6


SENSORS: dict[str, Sensor] = {
    "imx287": Sensor("Sony IMX287 (1/2.9in, GS)", 720, 540, 6.9, True, True,
                     "large pixels, excellent low light, low resolution"),
    "imx273": Sensor("Sony IMX273 (1/2.9in, GS)", 1440, 1080, 3.45, True, True,
                     "1.6 MP, fits gigabit Ethernet at 60 fps"),
    "imx392": Sensor("Sony IMX392 (1/2.3in, GS)", 1920, 1200, 3.45, True, True,
                     "2.3 MP machine vision workhorse, high frame rate"),
    "imx250": Sensor("Sony IMX250 (2/3in, GS)", 2448, 2048, 3.45, True, True,
                     "5 MP global shutter, good for large volumes"),
    "imx541": Sensor("Sony IMX541 (1.1in, GS)", 5320, 3032, 2.74, True, False,
                     "20 MP, excessive for mocap, needs 10 GbE"),
    "imx676": Sensor("Sony IMX676 STARVIS 2 (RS)", 4056, 3040, 2.0, False, True,
                     "WARNING: rolling shutter, will band under PWM lighting"),
}

DEFAULT_SENSOR = "imx392"

# --------------------------------------------------------------------------- #
# Physical assumptions. Override on the command line where they matter.
# --------------------------------------------------------------------------- #

PERSON_HEIGHT_M = 1.80        # nominal performer height
HAND_SPEED_MS = 6.0           # peak hand velocity in dance
MAX_BLUR_PX = 2.0             # blur budget for stable tracking
MIN_PERSON_PX = 250           # working threshold for markerless tracking
GOOD_PERSON_PX = 400          # comfortable level
INCIDENT_METER_CONSTANT = 250.0   # C in the incident-light exposure equation
TARGET_SCREEN_NITS = 48.0     # cinema reference screen luminance


# --------------------------------------------------------------------------- #
# 1. Camera geometry
# --------------------------------------------------------------------------- #

def required_fov_deg(span_m: float, distance_m: float) -> float:
    """Angle of view needed to fit span_m at distance_m."""
    return 2.0 * math.degrees(math.atan((span_m / 2.0) / distance_m))


def focal_from_fov(sensor_dim_mm: float, fov_deg: float) -> float:
    """Focal length giving fov_deg across sensor_dim_mm."""
    return (sensor_dim_mm / 2.0) / math.tan(math.radians(fov_deg) / 2.0)


def px_per_meter(focal_mm: float, distance_m: float, pixel_um: float) -> float:
    """Pixels per metre on subject at a given distance."""
    return (focal_mm / 1000.0) / (distance_m * pixel_um / 1e6)


def camera_geometry(width: float, depth: float, rig_height: float,
                    inset: float, sensor: Sensor, coverage_margin: float) -> dict:
    """
    Cameras in the corners of the volume at rig_height, set back by inset
    metres, aimed at the centre of the volume at waist height.
    """
    aim_height = 1.0
    cam_x, cam_y = -inset, -inset
    center_x, center_y = width / 2.0, depth / 2.0

    dist_center = math.sqrt((center_x - cam_x) ** 2 + (center_y - cam_y) ** 2 +
                            (rig_height - aim_height) ** 2)
    far_x, far_y = width + inset, depth + inset
    dist_far = math.sqrt((far_x - cam_x) ** 2 + (far_y - cam_y) ** 2 +
                         (rig_height - aim_height) ** 2)
    dist_near = math.sqrt(cam_x ** 2 + cam_y ** 2 + (rig_height - aim_height) ** 2)

    diagonal = math.sqrt(width ** 2 + depth ** 2) * coverage_margin
    h_fov = required_fov_deg(diagonal, dist_center)

    v_span = (PERSON_HEIGHT_M + 0.8) * coverage_margin
    v_fov_needed = required_fov_deg(v_span, dist_near)

    focal = min(focal_from_fov(sensor.width_mm, h_fov),
                focal_from_fov(sensor.height_mm, v_fov_needed))

    actual_h_fov = 2.0 * math.degrees(math.atan((sensor.width_mm / 2.0) / focal))
    actual_v_fov = 2.0 * math.degrees(math.atan((sensor.height_mm / 2.0) / focal))

    ppm_near = px_per_meter(focal, dist_near, sensor.pixel_um)
    ppm_far = px_per_meter(focal, dist_far, sensor.pixel_um)

    return {
        "distance_center_m": round(dist_center, 2),
        "distance_near_m": round(dist_near, 2),
        "distance_far_m": round(dist_far, 2),
        "required_horizontal_fov_deg": round(h_fov, 1),
        "recommended_focal_mm": round(focal, 1),
        "actual_horizontal_fov_deg": round(actual_h_fov, 1),
        "actual_vertical_fov_deg": round(actual_v_fov, 1),
        "person_px_near": round(ppm_near * PERSON_HEIGHT_M),
        "person_px_far": round(ppm_far * PERSON_HEIGHT_M),
        "px_per_meter_far": round(ppm_far, 1),
    }


# --------------------------------------------------------------------------- #
# 2. Exposure and light
# --------------------------------------------------------------------------- #

def exposure_budget(focal_mm: float, distance_far_m: float, pixel_um: float,
                    f_number: float, iso: float) -> dict:
    """
    Shutter limit from motion blur, and the illuminance that limit demands.

    Incident-light exposure equation:  E = (N^2 * C) / (t * S)
    """
    ppm = px_per_meter(focal_mm, distance_far_m, pixel_um)
    hand_px_per_s = HAND_SPEED_MS * ppm
    max_exposure_s = MAX_BLUR_PX / hand_px_per_s if hand_px_per_s > 0 else 0.0

    required_lux = ((f_number ** 2 * INCIDENT_METER_CONSTANT) / (max_exposure_s * iso)
                    if max_exposure_s > 0 and iso > 0 else float("inf"))

    return {
        "hand_motion_px_per_s": round(hand_px_per_s),
        "max_exposure_ms": round(max_exposure_s * 1000.0, 2),
        "f_number": f_number,
        "sensor_iso_equivalent": iso,
        "required_scene_illuminance_lux": round(required_lux),
        "typical_dark_stage_lux": "10-50",
        "verdict": ("LIGHT SUFFICIENT" if required_lux <= 50 else
                    "LIGHT DEFICIT - add infrared illumination or faster glass"),
    }


# --------------------------------------------------------------------------- #
# 3. Network
# --------------------------------------------------------------------------- #

def network_load(sensor: Sensor, fps: int, cameras: int, bit_depth: int,
                 compressed: bool, compression_ratio: float) -> dict:
    per_cam_bps = sensor.width_px * sensor.height_px * bit_depth * fps
    if compressed:
        per_cam_bps /= compression_ratio
    total_bps = per_cam_bps * cameras

    per_cam_gbps = per_cam_bps / 1e9
    total_gbps = total_bps / 1e9

    if per_cam_gbps > 0.95:
        link = "EXCEEDS 1 GbE per camera - needs 2.5/5/10 GbE, lower rate, or compression"
    elif per_cam_gbps > 0.7:
        link = "1 GbE above 70 percent - drop risk, leave headroom"
    else:
        link = "1 GbE per camera is sufficient"

    if total_gbps > 9.0:
        uplink = "10 GbE uplink saturated - use 25 GbE or two network cards"
    elif total_gbps > 0.95:
        uplink = "server uplink must be 10 GbE"
    else:
        uplink = "1 GbE uplink is sufficient"

    return {
        "per_camera_gbps": round(per_cam_gbps, 3),
        "total_gbps": round(total_gbps, 3),
        "per_camera_link_verdict": link,
        "server_uplink_verdict": uplink,
        "compressed": compressed,
        "compression_ratio": compression_ratio if compressed else 1.0,
    }


# --------------------------------------------------------------------------- #
# 4. Projection
# --------------------------------------------------------------------------- #

def projection_budget(screen_width_m: float, screen_height_m: float,
                      projectors: int, lumens_each: float, screen_gain: float,
                      blend_overlap: float) -> dict:
    """
    Screen luminance under a Lambertian model, which is a conservative floor.

        E [lux]     = total lumens / area
        L [cd/m^2]  = E * gain / pi

    Metallized scrims are directional and will read brighter on axis than this
    model predicts. Treat the result as a lower bound and confirm with a sample.
    """
    area = screen_width_m * screen_height_m
    effective_lumens = projectors * lumens_each * (1.0 - blend_overlap)
    illuminance = effective_lumens / area if area > 0 else 0.0
    luminance = illuminance * screen_gain / math.pi

    return {
        "screen_area_m2": round(area, 2),
        "effective_lumens": round(effective_lumens),
        "screen_illuminance_lux": round(illuminance),
        "screen_luminance_nits_lambertian": round(luminance, 1),
        "target_nits": TARGET_SCREEN_NITS,
        "headroom_ratio": round(luminance / TARGET_SCREEN_NITS, 2) if TARGET_SCREEN_NITS else 0,
        "verdict": ("BRIGHTNESS SUFFICIENT" if luminance >= TARGET_SCREEN_NITS * 0.6 else
                    "TOO DIM - raise output, shrink the surface, or choose higher gain"),
        "note": "Lambertian lower bound. Metallized scrim reads brighter on axis.",
    }


# --------------------------------------------------------------------------- #
# 5. Latency
# --------------------------------------------------------------------------- #

def latency_budget(fps: int, inference_ms: float, render_fps: int,
                   compressed: bool) -> dict:
    capture_ms = 1000.0 / fps
    encode_ms = 1000.0 / fps if compressed else 0.0
    network_ms = 5.0
    render_ms = 2000.0 / render_fps
    projector_ms = 16.0

    total = capture_ms + encode_ms + inference_ms + network_ms + render_ms + projector_ms
    return {
        "capture_ms": round(capture_ms, 1),
        "encode_ms": round(encode_ms, 1),
        "inference_ms": round(inference_ms, 1),
        "network_ms": network_ms,
        "render_ms": round(render_ms, 1),
        "projector_ms": projector_ms,
        "total_ms": round(total, 1),
        "verdict": ("EXCELLENT - tight synchrony achievable" if total < 100 else
                    "ACCEPTABLE - needs prediction and latency-aware choreography"
                    if total < 200 else
                    "CRITICAL - trailing aesthetics only, no precise accents"),
    }


# --------------------------------------------------------------------------- #

def analyse(args: argparse.Namespace) -> dict:
    sensor = SENSORS[args.preset]
    geom = camera_geometry(args.width, args.depth, args.rig_height,
                           args.inset, sensor, args.coverage_margin)
    exposure = exposure_budget(geom["recommended_focal_mm"], geom["distance_far_m"],
                               sensor.pixel_um, args.f_number, args.iso)
    net = network_load(sensor, args.fps, args.cameras, args.bit_depth,
                       args.compressed, args.compression_ratio)
    proj = projection_budget(args.screen_width, args.screen_height, args.projectors,
                             args.projector_lumens, args.screen_gain, args.blend_overlap)
    lat = latency_budget(args.fps, args.inference_ms, args.render_fps, args.compressed)

    quality = geom["person_px_far"]
    if quality >= GOOD_PERSON_PX:
        quality_verdict = "subject resolution comfortable"
    elif quality >= MIN_PERSON_PX:
        quality_verdict = "subject resolution minimally sufficient"
    else:
        quality_verdict = "SUBJECT RESOLUTION TOO LOW - bigger sensor or tighter zones"

    return {
        "input": {
            "volume_m": f"{args.width} x {args.depth}",
            "rig_height_m": args.rig_height,
            "performers": args.performers,
            "cameras_planned": args.cameras,
            "cameras_recommended_min": max(4, 2 * args.performers),
            "sensor": sensor.name,
            "sensor_note": sensor.note,
            "global_shutter": sensor.global_shutter,
            "fps": args.fps,
        },
        "geometry": geom,
        "geometry_verdict": quality_verdict,
        "exposure": exposure,
        "network": net,
        "projection": proj,
        "latency": lat,
    }


def print_report(r: dict) -> None:
    def section(title: str) -> None:
        print()
        print(title)
        print("-" * len(title))

    inp = r["input"]
    print(f"VOLUME {inp['volume_m']} m, grid {inp['rig_height_m']} m, "
          f"{inp['performers']} performers, {inp['cameras_planned']} cameras")
    print(f"Sensor: {inp['sensor']} - {inp['sensor_note']}")
    print(f"Global shutter: {'YES' if inp['global_shutter'] else 'NO - PWM BANDING RISK'}")
    if inp["cameras_planned"] < inp["cameras_recommended_min"]:
        print(f"!! Too few cameras: {inp['performers']} performers need at least "
              f"{inp['cameras_recommended_min']} for occlusion")

    section("1. GEOMETRY AND OPTICS")
    g = r["geometry"]
    print(f"Distance near / centre / far: "
          f"{g['distance_near_m']} / {g['distance_center_m']} / {g['distance_far_m']} m")
    print(f"Required horizontal FOV: {g['required_horizontal_fov_deg']} deg")
    print(f"Recommended focal length: {g['recommended_focal_mm']} mm "
          f"({g['actual_horizontal_fov_deg']} x {g['actual_vertical_fov_deg']} deg)")
    print(f"Body height in pixels: near {g['person_px_near']}, far {g['person_px_far']}")
    print(f"VERDICT: {r['geometry_verdict']}")

    section("2. EXPOSURE AND LIGHT")
    e = r["exposure"]
    print(f"Hand motion in frame: {e['hand_motion_px_per_s']} px/s")
    print(f"Maximum exposure for {MAX_BLUR_PX} px blur: {e['max_exposure_ms']} ms")
    print(f"At f/{e['f_number']} and ISO {e['sensor_iso_equivalent']}: "
          f"{e['required_scene_illuminance_lux']} lux required")
    print(f"Typical dark stage: {e['typical_dark_stage_lux']} lux")
    print(f"VERDICT: {e['verdict']}")

    section("3. NETWORK")
    n = r["network"]
    mode = f"compressed 1:{n['compression_ratio']:g}" if n["compressed"] else "uncompressed"
    print(f"Per camera: {n['per_camera_gbps']} Gbit/s ({mode})")
    print(f"Aggregate: {n['total_gbps']} Gbit/s")
    print(f"Camera link: {n['per_camera_link_verdict']}")
    print(f"Server uplink: {n['server_uplink_verdict']}")

    section("4. PROJECTION")
    p = r["projection"]
    print(f"Screen area: {p['screen_area_m2']} m2")
    print(f"Effective output: {p['effective_lumens']} lm -> "
          f"{p['screen_illuminance_lux']} lux on the surface")
    print(f"Luminance: {p['screen_luminance_nits_lambertian']} cd/m2 "
          f"against {p['target_nits']} target (headroom x{p['headroom_ratio']})")
    print(f"VERDICT: {p['verdict']}")
    print(f"Note: {p['note']}")

    section("5. END-TO-END LATENCY")
    l = r["latency"]
    print(f"capture {l['capture_ms']} + encode {l['encode_ms']} + inference {l['inference_ms']} "
          f"+ network {l['network_ms']} + render {l['render_ms']} + projector {l['projector_ms']}")
    print(f"TOTAL: {l['total_ms']} ms - {l['verdict']}")
    print()


def selftest() -> int:
    ns = argparse.Namespace(
        width=7.0, depth=7.0, rig_height=4.5, inset=0.5, performers=4, cameras=4,
        preset="imx392", fps=60, bit_depth=8, compressed=False, compression_ratio=20.0,
        f_number=1.4, iso=800.0, coverage_margin=1.1,
        screen_width=7.0, screen_height=4.0, projectors=2, projector_lumens=10000.0,
        screen_gain=0.15, blend_overlap=0.15, inference_ms=100.0, render_fps=60,
    )
    r = analyse(ns)

    g = r["geometry"]
    assert 3.0 < g["recommended_focal_mm"] < 12.0, g["recommended_focal_mm"]
    assert g["person_px_far"] < g["person_px_near"]
    assert g["distance_far_m"] > g["distance_center_m"] > g["distance_near_m"]

    e = r["exposure"]
    assert e["max_exposure_ms"] > 0
    assert e["required_scene_illuminance_lux"] > 50, "a dark stage must show a deficit"

    n = r["network"]
    assert n["per_camera_gbps"] > 1.0, n["per_camera_gbps"]
    assert "EXCEEDS" in n["per_camera_link_verdict"]

    ns.compressed = True
    r2 = analyse(ns)
    assert r2["network"]["per_camera_gbps"] < 0.1
    assert r2["latency"]["total_ms"] > r["latency"]["total_ms"], "compression must add latency"

    p = r["projection"]
    assert p["screen_area_m2"] == 28.0
    assert p["screen_luminance_nits_lambertian"] > 0

    ns.compressed = False
    ns.performers = 1
    r3 = analyse(ns)
    assert r3["input"]["cameras_recommended_min"] == 4

    print(json.dumps(r["geometry"], indent=2))
    print("SELFTEST OK")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Engineering calculator for stage capture and projection systems")
    p.add_argument("--width", type=float, default=7.0, help="capture area width, m")
    p.add_argument("--depth", type=float, default=7.0, help="capture area depth, m")
    p.add_argument("--rig-height", type=float, default=4.5, help="grid height, m")
    p.add_argument("--inset", type=float, default=0.5, help="camera setback beyond the area, m")
    p.add_argument("--performers", type=int, default=4, help="simultaneous performers")
    p.add_argument("--cameras", type=int, default=4, help="planned camera count")
    p.add_argument("--preset", choices=sorted(SENSORS), default=DEFAULT_SENSOR)
    p.add_argument("--fps", type=int, default=60)
    p.add_argument("--bit-depth", type=int, default=8)
    p.add_argument("--compressed", action="store_true", help="cameras with onboard H.264/H.265")
    p.add_argument("--compression-ratio", type=float, default=20.0)
    p.add_argument("--f-number", type=float, default=1.4, help="lens aperture")
    p.add_argument("--iso", type=float, default=800.0, help="equivalent sensitivity")
    p.add_argument("--coverage-margin", type=float, default=1.1, help="coverage safety factor")
    p.add_argument("--screen-width", type=float, default=7.0)
    p.add_argument("--screen-height", type=float, default=4.0)
    p.add_argument("--projectors", type=int, default=2)
    p.add_argument("--projector-lumens", type=float, default=10000.0)
    p.add_argument("--screen-gain", type=float, default=0.15,
                   help="0.15 metallized scrim, 1.0 white matte screen")
    p.add_argument("--blend-overlap", type=float, default=0.15, help="edge blend overlap fraction")
    p.add_argument("--inference-ms", type=float, default=100.0, help="mocap inference latency")
    p.add_argument("--render-fps", type=int, default=60)
    p.add_argument("--json", metavar="PATH", help="write the report to a JSON file")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()

    if args.selftest:
        return selftest()

    report = analyse(args)
    print_report(report)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"Report written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
