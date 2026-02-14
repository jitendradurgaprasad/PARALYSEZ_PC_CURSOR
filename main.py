import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# Screen size
screen_w, screen_h = pyautogui.size()

# Mediapipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

prev_x, prev_y = 0, 0
steady_start = None
click_cooldown = 0
scroll_cooldown = 0

def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        landmarks = hand_landmarks.landmark

        # Get fingertip coordinates
        index_tip = (int(landmarks[8].x * w), int(landmarks[8].y * h))
        thumb_tip = (int(landmarks[4].x * w), int(landmarks[4].y * h))
        middle_tip = (int(landmarks[12].x * w), int(landmarks[12].y * h))
        ring_tip = (int(landmarks[16].x * w), int(landmarks[16].y * h))

        # -------- Cursor Control (Index finger) --------
        screen_x = np.interp(index_tip[0], [0, w], [0, screen_w])
        screen_y = np.interp(index_tip[1], [0, h], [0, screen_h])

        # Smoothing
        smooth_factor = 5
        curr_x = prev_x + (screen_x - prev_x) / smooth_factor
        curr_y = prev_y + (screen_y - prev_y) / smooth_factor

        pyautogui.moveTo(curr_x, curr_y)
        prev_x, prev_y = curr_x, curr_y

        # -------- Thumb + Index = Left Click --------
        if distance(index_tip, thumb_tip) < 35:
            if time.time() - click_cooldown > 1:
                pyautogui.click()
                click_cooldown = time.time()

        # -------- Tiny Movement Hold = Left Click --------
        movement = distance((curr_x, curr_y), (screen_x, screen_y))

        if movement < 5:
            if steady_start is None:
                steady_start = time.time()
            elif time.time() - steady_start > 1.2:
                if time.time() - click_cooldown > 1:
                    pyautogui.click()
                    click_cooldown = time.time()
                    steady_start = None
        else:
            steady_start = None

        # -------- Middle + Index = Scroll Down --------
        if distance(middle_tip, index_tip) < 35:
            if time.time() - scroll_cooldown > 1:
                pyautogui.scroll(-300)
                scroll_cooldown = time.time()

        # -------- Middle + Ring = Scroll Up --------
        if distance(middle_tip, ring_tip) < 35:
            if time.time() - scroll_cooldown > 1:
                pyautogui.scroll(300)
                scroll_cooldown = time.time()

    cv2.imshow("Finger Cursor Control", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
