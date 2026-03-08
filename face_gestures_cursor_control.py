import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# Screen size
screen_w, screen_h = pyautogui.size()

# MediaPipe Face Mesh setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cam = cv2.VideoCapture(0)

# Blink detection threshold
blink_threshold = 0.015
click_cooldown = 1
last_click_time = 0

def eye_aspect_ratio(landmarks, left, right):
    return abs(landmarks[left].y - landmarks[right].y)

while True:
    ret, frame = cam.read()
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = face_mesh.process(rgb_frame)

    if output.multi_face_landmarks:
        landmarks = output.multi_face_landmarks[0].landmark

        # Nose tip landmark (for cursor movement)
        nose = landmarks[1]
        screen_x = screen_w * nose.x
        screen_y = screen_h * nose.y
        pyautogui.moveTo(screen_x, screen_y)

        # Left eye blink detection
        left_eye = eye_aspect_ratio(landmarks, 159, 145)

        # Right eye blink detection
        right_eye = eye_aspect_ratio(landmarks, 386, 374)

        current_time = time.time()

        if left_eye < blink_threshold and current_time - last_click_time > click_cooldown:
            pyautogui.click()
            last_click_time = current_time

        if right_eye < blink_threshold and current_time - last_click_time > click_cooldown:
            pyautogui.rightClick()
            last_click_time = current_time

    cv2.imshow("Face Mouse Control", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cam.release()
cv2.destroyAllWindows()