import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

pyautogui.FAILSAFE = True

screen_w, screen_h = pyautogui.size()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

dead_zone = 40
speed = 15
edge_margin = 15

calibration_time = 5
calibrated = False
calibration_start = None
calibration_points = []
neutral_point = None

click_ready = True


def pinky_up(landmarks):
    return landmarks[20].y < landmarks[18].y


while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        hand = result.multi_hand_landmarks[0]
        landmarks = hand.landmark

        index_tip = (int(landmarks[8].x * w),
                     int(landmarks[8].y * h))

        # -------- CALIBRATION --------
        if not calibrated:
            if calibration_start is None:
                calibration_start = time.time()

            elapsed = time.time() - calibration_start
            remaining = int(calibration_time - elapsed)

            if elapsed < calibration_time:
                calibration_points.append(index_tip)

                cv2.putText(frame,
                            f"Calibrating... Hold steady ({remaining})",
                            (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2)
            else:
                avg_x = int(np.mean([p[0] for p in calibration_points]))
                avg_y = int(np.mean([p[1] for p in calibration_points]))
                neutral_point = (avg_x, avg_y)
                calibrated = True

        # -------- CONTROL --------
        else:
            dx = index_tip[0] - neutral_point[0]
            dy = index_tip[1] - neutral_point[1]

            # Draw neutral bounding box
            top_left = (neutral_point[0] - dead_zone,
                        neutral_point[1] - dead_zone)
            bottom_right = (neutral_point[0] + dead_zone,
                            neutral_point[1] + dead_zone)

            cv2.rectangle(frame, top_left, bottom_right,
                          (255, 0, 0), 2)

            # -------- CLICK MODE --------
            if pinky_up(landmarks):

                cv2.putText(frame,
                            "CLICK MODE",
                            (30, 80),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 255),
                            2)

                # Cursor paused

                # If index moves downward beyond box
                if dy > dead_zone and click_ready:
                    pyautogui.click()
                    click_ready = False

                # Reset click readiness when finger returns to neutral
                if abs(dy) < dead_zone:
                    click_ready = True

            # -------- MOVEMENT MODE --------
            else:
                move_x = 0
                move_y = 0

                if abs(dx) > dead_zone:
                    move_x = speed if dx > 0 else -speed

                if abs(dy) > dead_zone:
                    move_y = speed if dy > 0 else -speed

                current_x, current_y = pyautogui.position()

                new_x = current_x + move_x
                new_y = current_y + move_y

                new_x = max(edge_margin, min(screen_w - edge_margin, new_x))
                new_y = max(edge_margin, min(screen_h - edge_margin, new_y))

                pyautogui.moveTo(new_x, new_y)

            cv2.circle(frame, neutral_point, 8, (0, 255, 0), -1)

        cv2.circle(frame, index_tip, 8, (0, 0, 255), -1)

    cv2.imshow("Finger Cursor Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
