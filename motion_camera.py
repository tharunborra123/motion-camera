"""
Motion-Based Security Camera
----------------------------
Detects movement using background subtraction (OpenCV MOG2), then saves
timestamped screenshots (and optional video clips) only when something moves.
Every event is logged to a CSV file.

Usage:
    python motion_camera.py                      # default webcam
    python motion_camera.py --source video.mp4   # test on a video file
    python motion_camera.py --record             # also save short clips
    python motion_camera.py --min-area 3000      # ignore smaller movements

Press 'q' in the preview window to quit.
"""

import argparse
import csv
import os
import time
from datetime import datetime

import cv2


def parse_args():
    p = argparse.ArgumentParser(description="Motion-based security camera")
    p.add_argument("--source", default="0", help="Webcam index (0) or video file path")
    p.add_argument("--min-area", type=int, default=1500,
                   help="Minimum contour area to count as motion (higher = less sensitive)")
    p.add_argument("--cooldown", type=float, default=3.0,
                   help="Seconds between saved screenshots")
    p.add_argument("--out", default="motion_events", help="Output folder")
    p.add_argument("--record", action="store_true", help="Record short video clips on motion")
    p.add_argument("--clip-tail", type=float, default=3.0,
                   help="Keep recording this many seconds after motion stops")
    p.add_argument("--no-preview", action="store_true", help="Run without a preview window")
    return p.parse_args()


def main():
    args = parse_args()

    os.makedirs(os.path.join(args.out, "images"), exist_ok=True)
    os.makedirs(os.path.join(args.out, "clips"), exist_ok=True)
    log_path = os.path.join(args.out, "events.csv")

    # Create the log file with a header if it doesn't exist yet
    if not os.path.exists(log_path):
        with open(log_path, "w", newline="") as f:
            csv.writer(f).writerow(["timestamp", "image_file", "motion_regions", "largest_area"])

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open video source: {args.source}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 0 else 20.0

    # MOG2 learns the static background and flags anything that changes
    subtractor = cv2.createBackgroundSubtractorMOG2(
        history=500, varThreshold=50, detectShadows=True
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    warmup_frames = 30          # let the model learn the background first
    frame_count = 0
    last_save = 0.0
    last_motion = 0.0
    writer = None
    events = 0

    print("Camera started. Press 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break  # end of video file or camera error

        # Resize for speed and consistent min-area behaviour
        h, w = frame.shape[:2]
        scale = 640 / w
        frame = cv2.resize(frame, (640, int(h * scale)))

        # Preprocess: grayscale + blur removes noise
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Foreground mask: white = moving, grey (127) = shadow, black = background
        mask = subtractor.apply(gray)
        frame_count += 1
        if frame_count <= warmup_frames:
            continue

        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)  # drop shadows
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)       # remove specks
        mask = cv2.dilate(mask, kernel, iterations=2)               # fill gaps

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        regions = 0
        largest = 0
        for c in contours:
            area = cv2.contourArea(c)
            if area < args.min_area:
                continue
            regions += 1
            largest = max(largest, int(area))
            x, y, bw, bh = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)

        now = time.time()
        motion = regions > 0
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Overlay status and timestamp
        status = "MOTION DETECTED" if motion else "Monitoring"
        color = (0, 0, 255) if motion else (0, 200, 0)
        cv2.putText(frame, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, stamp, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        if motion:
            last_motion = now

            # Save a screenshot (respecting the cooldown) and log it
            if now - last_save >= args.cooldown:
                fname = datetime.now().strftime("motion_%Y%m%d_%H%M%S.jpg")
                cv2.imwrite(os.path.join(args.out, "images", fname), frame)
                with open(log_path, "a", newline="") as f:
                    csv.writer(f).writerow([stamp, fname, regions, largest])
                last_save = now
                events += 1
                print(f"[{stamp}] Motion event #{events} saved: {fname}")

            # Start a clip if recording is enabled
            if args.record and writer is None:
                clip = datetime.now().strftime("clip_%Y%m%d_%H%M%S.mp4")
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(
                    os.path.join(args.out, "clips", clip), fourcc, fps,
                    (frame.shape[1], frame.shape[0]),
                )

        # Write frames while recording; stop after motion has been quiet for a while
        if writer is not None:
            writer.write(frame)
            if now - last_motion > args.clip_tail:
                writer.release()
                writer = None

        if not args.no_preview:
            cv2.imshow("Motion Camera (q to quit)", frame)
            cv2.imshow("Mask", mask)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if writer is not None:
        writer.release()
    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. {events} motion event(s) logged to {log_path}")


if __name__ == "__main__":
    main()
