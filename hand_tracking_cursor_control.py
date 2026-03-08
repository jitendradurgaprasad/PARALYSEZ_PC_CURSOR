import cv2
import mediapipe as mp
import pyautogui
import time

pyautogui.FAILSAFE = False
screen_w, screen_h = pyautogui.size()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)


# Calibration
neutral_x = None
neutral_y = None
dead_zone = 30
calibrated = False
calibration_start = None

# Smooth movement
acceleration = 0.30
max_speed = 80
smooth_factor = 0.7

prev_dx = 0
prev_dy = 0

# Cooldowns
scroll_cooldown = 0.4
click_cooldown = 0.4
last_scroll_time = 0
last_click_time = 0


def all_fingers_up(hand_landmarks):
    tips = [8, 12, 16, 20]
    count = 0
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1
    return count == 4


def pinky_up(hand_landmarks):
    return hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y


while True:

    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            index_tip = hand_landmarks.landmark[8]
            pinky_tip = hand_landmarks.landmark[20]

            x = int(index_tip.x * w)
            y = int(index_tip.y * h)

            # ---- DRAW ONLY INDEX + PINKY ----
            cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)
            cv2.circle(frame,
                       (int(pinky_tip.x * w), int(pinky_tip.y * h)),
                       8, (255, 0, 0), -1)

            # ---------------- CALIBRATION ----------------
            if not calibrated:

                if calibration_start is None:
                    calibration_start = time.time()

                elapsed = time.time() - calibration_start
                remaining = int(5 - elapsed)

                cv2.putText(frame, f"Calibrating: {remaining}",
                            (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 2)

                if elapsed >= 5:
                    neutral_x = x
                    neutral_y = y
                    calibrated = True

                continue

            # Recalibration
            if all_fingers_up(hand_landmarks):
                calibrated = False
                calibration_start = None
                neutral_x = None
                neutral_y = None
                continue

            # Draw dead zone
            cv2.rectangle(frame,
                          (neutral_x - dead_zone, neutral_y - dead_zone),
                          (neutral_x + dead_zone, neutral_y + dead_zone),
                          (0, 255, 0), 2)

            current_time = time.time()

            # ---------------- ACTION MODE ----------------
            if pinky_up(hand_landmarks):

                # BELOW box → LEFT CLICK
                if y > neutral_y + dead_zone and (current_time - last_click_time > click_cooldown):
                    pyautogui.click(button='left')
                    last_click_time = current_time

                # ABOVE box → RIGHT CLICK
                elif y < neutral_y - dead_zone and (current_time - last_click_time > click_cooldown):
                    pyautogui.click(button='right')
                    last_click_time = current_time

                # CROSS LEFT → SCROLL UP
                elif x < neutral_x - dead_zone and (current_time - last_scroll_time > scroll_cooldown):
                    pyautogui.scroll(200)
                    last_scroll_time = current_time

                # CROSS RIGHT → SCROLL DOWN
                elif x > neutral_x + dead_zone and (current_time - last_scroll_time > scroll_cooldown):
                    pyautogui.scroll(-200)
                    last_scroll_time = current_time

                continue

            # ---------------- NORMAL CURSOR MODE ----------------
            overflow_x = x - neutral_x
            overflow_y = y - neutral_y

            dx = overflow_x * acceleration
            dy = overflow_y * acceleration

            dx = max(min(dx, max_speed), -max_speed)
            dy = max(min(dy, max_speed), -max_speed)

            # Smooth movement using weighted averaging
            dx = smooth_factor * prev_dx + (1 - smooth_factor) * dx
            dy = smooth_factor * prev_dy + (1 - smooth_factor) * dy

            prev_dx = dx
            prev_dy = dy

            mouse_x, mouse_y = pyautogui.position()
            pyautogui.moveTo(mouse_x + dx, mouse_y + dy)

    cv2.imshow("Axial Finger Mouse", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()