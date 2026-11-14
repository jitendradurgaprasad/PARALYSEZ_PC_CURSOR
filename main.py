"""PARALYSEZ: control the mouse with hand or face movements."""

from __future__ import annotations

import argparse
import math
import sys
import time
from collections import deque


CALIBRATION_SECONDS = 3.0
DEAD_ZONE = 30
MAX_SPEED = 80
ACCELERATION = 0.30
SMOOTHING = 0.70
CLICK_COOLDOWN = 0.45
SCROLL_COOLDOWN = 0.45


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control your mouse with hand or face movements.",
        epilog="Examples: python main.py --mode hand | python main.py --mode face",
    )
    parser.add_argument("--mode", choices=("hand", "face"), help="tracking mode (asks if omitted)")
    parser.add_argument("--camera", type=int, default=0, help="camera device index (default: 0)")
    return parser.parse_args()


def choose_mode(mode: str | None) -> str:
    if mode:
        return mode
    if not sys.stdin.isatty():
        raise SystemExit("Choose a mode with --mode hand or --mode face.")
    print("PARALYSEZ mouse control\n1. Hand tracking\n2. Face tracking")
    while True:
        choice = input("Choose 1 or 2: ").strip()
        if choice in ("1", "2"):
            return "hand" if choice == "1" else "face"
        print("Enter 1 for hand tracking or 2 for face tracking.")


def draw_text(cv2, frame, text: str, y: int, color=(255, 255, 255)) -> None:
    cv2.putText(frame, text, (18, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)


def run(mode: str, camera_index: int) -> None:
    try:
        import cv2
        import mediapipe as mp
        import pyautogui
    except ImportError as exc:
        raise SystemExit(
            f"Missing dependency: {exc.name}. Install the project requirements with: python -m pip install -r requirements.txt"
        ) from exc

    if not hasattr(mp, "solutions"):
        raise SystemExit(
            "This project needs MediaPipe 0.10.21. Reinstall the pinned packages with: "
            "python -m pip install --force-reinstall -r requirements.txt"
        )

    # Keep PyAutoGUI's corner fail-safe enabled so users can stop cursor control quickly.
    pyautogui.FAILSAFE = True
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        cap.release()
        raise SystemExit(f"Could not open camera {camera_index}. Check the camera or try --camera 1.")

    screen_w, screen_h = pyautogui.size()
    neutral: tuple[float, float] | None = None
    calibration_samples: deque[tuple[float, float]] = deque()
    calibration_started: float | None = None
    previous_dx = previous_dy = 0.0
    last_click = last_scroll = 0.0

    hand_tracker = face_tracker = None
    if mode == "hand":
        hand_tracker = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        hand_connections = mp.solutions.hands.HAND_CONNECTIONS
        draw_hand = mp.solutions.drawing_utils.draw_landmarks
    else:
        face_tracker = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )

    print(f"Starting {mode} control. Hold still to calibrate. Press Q or Esc to quit; press C to recalibrate.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                raise SystemExit("The camera stopped sending frames.")
            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            point = None
            landmarks = None
            action = ""

            if mode == "hand":
                result = hand_tracker.process(rgb)
                if result.multi_hand_landmarks:
                    landmarks = result.multi_hand_landmarks[0]
                    draw_hand(frame, landmarks, hand_connections)
                    point = (landmarks.landmark[8].x * width, landmarks.landmark[8].y * height)
                    pinky = landmarks.landmark[20]
                    cv2.circle(frame, (int(point[0]), int(point[1])), 7, (0, 255, 0), -1)
                    cv2.circle(frame, (int(pinky.x * width), int(pinky.y * height)), 7, (255, 100, 0), -1)
            else:
                result = face_tracker.process(rgb)
                if result.multi_face_landmarks:
                    landmarks = result.multi_face_landmarks[0]
                    nose = landmarks.landmark[1]
                    point = (nose.x * width, nose.y * height)
                    cv2.circle(frame, (int(point[0]), int(point[1])), 7, (0, 255, 0), -1)

            now = time.monotonic()
            if point is None:
                calibration_started = None
                calibration_samples.clear()
                previous_dx = previous_dy = 0.0
                draw_text(cv2, frame, "No hand/face detected - show it to the camera", 32, (0, 180, 255))
            elif neutral is None:
                if calibration_started is None:
                    calibration_started = now
                calibration_samples.append(point)
                remaining = max(0, math.ceil(CALIBRATION_SECONDS - (now - calibration_started)))
                draw_text(cv2, frame, f"Calibrating: hold still ({remaining})", 32, (0, 180, 255))
                if now - calibration_started >= CALIBRATION_SECONDS:
                    neutral = (
                        sum(p[0] for p in calibration_samples) / len(calibration_samples),
                        sum(p[1] for p in calibration_samples) / len(calibration_samples),
                    )
                    calibration_samples.clear()
                    print("Calibration complete.")
            else:
                nx, ny = neutral
                cv2.rectangle(frame, (int(nx - DEAD_ZONE), int(ny - DEAD_ZONE)),
                              (int(nx + DEAD_ZONE), int(ny + DEAD_ZONE)), (0, 200, 0), 2)
                x, y = point
                gesture_mode = False

                if mode == "hand":
                    # All four fingers up recalibrates. Pinky up selects gesture actions.
                    fingers_up = all(
                        landmarks.landmark[tip].y < landmarks.landmark[tip - 2].y
                        for tip in (8, 12, 16, 20)
                    )
                    pinky_up = landmarks.landmark[20].y < landmarks.landmark[18].y
                    if fingers_up:
                        neutral = None
                        calibration_started = None
                        calibration_samples.clear()
                        previous_dx = previous_dy = 0.0
                        action = "Recalibrating"
                    elif pinky_up:
                        gesture_mode = True
                        action = "Gesture mode"
                        if y > ny + DEAD_ZONE and now - last_click >= CLICK_COOLDOWN:
                            pyautogui.click(button="left")
                            last_click, action = now, "Left click"
                        elif y < ny - DEAD_ZONE and now - last_click >= CLICK_COOLDOWN:
                            pyautogui.click(button="right")
                            last_click, action = now, "Right click"
                        elif x < nx - DEAD_ZONE and now - last_scroll >= SCROLL_COOLDOWN:
                            pyautogui.scroll(3)
                            last_scroll, action = now, "Scroll up"
                        elif x > nx + DEAD_ZONE and now - last_scroll >= SCROLL_COOLDOWN:
                            pyautogui.scroll(-3)
                            last_scroll, action = now, "Scroll down"
                else:
                    # Open mouth enables scroll mode; eye closures trigger the actions.
                    left_eye = abs(landmarks.landmark[159].y - landmarks.landmark[145].y)
                    right_eye = abs(landmarks.landmark[386].y - landmarks.landmark[374].y)
                    mouth = abs(landmarks.landmark[13].y - landmarks.landmark[14].y)
                    scroll_mode = mouth > 0.06
                    gesture_mode = True
                    if scroll_mode:
                        action = "Scroll mode: close left eye up / right eye down"
                        if left_eye < 0.015 and now - last_scroll >= SCROLL_COOLDOWN:
                            pyautogui.scroll(3)
                            last_scroll, action = now, "Scroll up"
                        elif right_eye < 0.015 and now - last_scroll >= SCROLL_COOLDOWN:
                            pyautogui.scroll(-3)
                            last_scroll, action = now, "Scroll down"
                    elif left_eye < 0.015 and now - last_click >= CLICK_COOLDOWN:
                        pyautogui.click(button="left")
                        last_click, action = now, "Left click"
                    elif right_eye < 0.015 and now - last_click >= CLICK_COOLDOWN:
                        pyautogui.click(button="right")
                        last_click, action = now, "Right click"

                if neutral is not None and not gesture_mode:
                    offset_x, offset_y = x - nx, y - ny
                    overflow_x = offset_x - DEAD_ZONE if offset_x > DEAD_ZONE else (
                        offset_x + DEAD_ZONE if offset_x < -DEAD_ZONE else 0
                    )
                    overflow_y = offset_y - DEAD_ZONE if offset_y > DEAD_ZONE else (
                        offset_y + DEAD_ZONE if offset_y < -DEAD_ZONE else 0
                    )
                    dx = max(-MAX_SPEED, min(MAX_SPEED, overflow_x * ACCELERATION))
                    dy = max(-MAX_SPEED, min(MAX_SPEED, overflow_y * ACCELERATION))
                    dx = SMOOTHING * previous_dx + (1 - SMOOTHING) * dx
                    dy = SMOOTHING * previous_dy + (1 - SMOOTHING) * dy
                    previous_dx, previous_dy = dx, dy
                    mouse_x, mouse_y = pyautogui.position()
                    pyautogui.moveTo(max(0, min(screen_w - 1, mouse_x + dx)),
                                     max(0, min(screen_h - 1, mouse_y + dy)))
                    action = "Move cursor"
                if action:
                    draw_text(cv2, frame, action, 32, (0, 230, 230))
                draw_text(cv2, frame, "C: recalibrate  |  Q / Esc: quit", height - 18)

            cv2.imshow(f"PARALYSEZ - {mode.title()} Control", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if key == ord("c"):
                neutral = None
                calibration_started = None
                calibration_samples.clear()
                previous_dx = previous_dy = 0.0
    except pyautogui.FailSafeException:
        print("Stopped by PyAutoGUI fail-safe (mouse reached the top-left screen corner).")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if hand_tracker is not None:
            hand_tracker.close()
        if face_tracker is not None:
            face_tracker.close()


def main() -> None:
    args = parse_args()
    run(choose_mode(args.mode), args.camera)


if __name__ == "__main__":
    main()
