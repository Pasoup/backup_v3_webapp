"""
test_resolution.py — probe both cameras for supported resolutions.

Run from the backend folder:
    python test_resolution.py

For each resolution it reports:
  - What the driver actually settled on
  - Whether the frame has real content (non-black)
  - Estimated FPS over a short burst
"""

import cv2
import time

CAM_INDICES = [0, 2]           # ← change if your cameras are at different indices

# Common resolutions to probe, ordered high → low
RESOLUTIONS = [
    (2592, 1944),
    (2048, 1536),
    (1920, 1080),
    (1920, 1440),
    (1600, 1200),
    (1280, 960),
    (1280, 720),
    (1024, 768),
    (800,  600),
    (640,  480),
]


def probe_camera(index: int):
    print(f"\n{'='*60}")
    print(f"  Camera index {index}")
    print(f"{'='*60}")
    print(f"  {'Requested':>12}  {'Actual':>12}  {'Frames?':>8}  {'~FPS':>6}  {'Brightness':>10}")
    print(f"  {'-'*60}")

    for req_w, req_h in RESOLUTIONS:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print(f"  Could not open camera at index {index}")
            return

        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  req_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, req_h)

        got_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        got_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Warm-up: drain buffer for up to 1 s
        ret, frame = False, None
        deadline = time.time() + 1.0
        while time.time() < deadline:
            ret, frame = cap.read()
            if ret and frame is not None and frame.shape[0] > 0:
                break
            time.sleep(0.03)

        if not ret or frame is None:
            print(f"  {req_w}×{req_h:>4}  →  {got_w}×{got_h:>4}  {'NO FRAMES':>8}")
            cap.release()
            time.sleep(0.2)
            continue

        brightness = frame.mean()

        # FPS estimate: count how many frames arrive in 0.5 s
        count = 0
        t0 = time.time()
        while time.time() - t0 < 0.5:
            r, _ = cap.read()
            if r:
                count += 1
        fps = count / 0.5

        match = "✓" if (got_w == req_w and got_h == req_h) else "~"
        print(f"  {req_w}×{req_h:>4}  →  {got_w}×{got_h:>4}  {match:>8}  {fps:>5.1f}  {brightness:>10.1f}")

        cap.release()
        time.sleep(0.3)          # let DirectShow release cleanly


if __name__ == "__main__":
    print("Probing cameras — this will take about 30 seconds…")
    for idx in CAM_INDICES:
        probe_camera(idx)
    print("\nDone.  Update calibration.json with the highest resolution that shows ✓ on both cameras.")
