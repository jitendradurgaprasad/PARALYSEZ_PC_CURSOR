import cv2
import mediapipe as mp
import pyautogui
import time

pyautogui.FAILSAFE = False

screen_w, screen_h = pyautogui.size()

mp_face = mp.solutions.face_mesh
face = mp_face.FaceMesh(refine_landmarks=True)

cap = cv2.VideoCapture(0)

# -------- CALIBRATION --------
neutral_x = None
neutral_y = None
dead_zone = 25

calibrated = False
calibration_start = None

# -------- SMOOTH CURSOR ENGINE (same as hand code) --------
acceleration = 0.35
max_speed = 80
smooth_factor = 0.7

prev_dx = 0
prev_dy = 0

# -------- COOLDOWNS --------
click_cooldown = 0.5
scroll_cooldown = 0.5

last_click_time = 0
last_scroll_time = 0


while True:

    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame,1)

    h,w,_ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face.process(rgb)

    if results.multi_face_landmarks:

        face_landmarks = results.multi_face_landmarks[0]

        # ---------- NOSE ----------
        nose = face_landmarks.landmark[1]

        x = int(nose.x * w)
        y = int(nose.y * h)

        # Draw central nose dot
        cv2.circle(frame,(x,y),6,(0,255,0),-1)

        # ---------- CALIBRATION ----------
        if not calibrated:

            if calibration_start is None:
                calibration_start = time.time()

            elapsed = time.time() - calibration_start
            remaining = int(5 - elapsed)

            cv2.putText(frame,f"Calibrating: {remaining}",
                        (40,50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,(0,0,255),2)

            if elapsed >= 5:

                neutral_x = x
                neutral_y = y
                calibrated = True

            cv2.imshow("Face Cursor",frame)
            cv2.waitKey(1)
            continue

        # ---------- DRAW DEAD ZONE ----------
        cv2.rectangle(frame,
                      (neutral_x-dead_zone, neutral_y-dead_zone),
                      (neutral_x+dead_zone, neutral_y+dead_zone),
                      (0,255,0),2)

        # ---------- SMOOTH CURSOR MOVEMENT ----------
        overflow_x = x - neutral_x
        overflow_y = y - neutral_y

        dx = overflow_x * acceleration
        dy = overflow_y * acceleration

        dx = max(min(dx,max_speed), -max_speed)
        dy = max(min(dy,max_speed), -max_speed)

        dx = smooth_factor * prev_dx + (1-smooth_factor)*dx
        dy = smooth_factor * prev_dy + (1-smooth_factor)*dy

        prev_dx = dx
        prev_dy = dy

        mouse_x,mouse_y = pyautogui.position()

        pyautogui.moveTo(mouse_x + dx, mouse_y + dy)

        # ---------- EYE DETECTION ----------
        left_eye_top = face_landmarks.landmark[159]
        left_eye_bottom = face_landmarks.landmark[145]

        right_eye_top = face_landmarks.landmark[386]
        right_eye_bottom = face_landmarks.landmark[374]

        left_eye_dist = abs(left_eye_top.y - left_eye_bottom.y)
        right_eye_dist = abs(right_eye_top.y - right_eye_bottom.y)

        # ---------- MOUTH ----------
        mouth_top = face_landmarks.landmark[13]
        mouth_bottom = face_landmarks.landmark[14]

        mouth_dist = abs(mouth_top.y - mouth_bottom.y)

        scroll_mode = mouth_dist > 0.06

        current_time = time.time()

        # ---------- GESTURE ACTIONS ----------
        if scroll_mode:

            cv2.putText(frame,"SCROLL MODE",
                        (40,90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,(255,0,0),2)

            if left_eye_dist < 0.015 and (current_time-last_scroll_time>scroll_cooldown):
                pyautogui.scroll(200)
                last_scroll_time = current_time

            if right_eye_dist < 0.015 and (current_time-last_scroll_time>scroll_cooldown):
                pyautogui.scroll(-200)
                last_scroll_time = current_time

        else:

            if left_eye_dist < 0.015 and (current_time-last_click_time>click_cooldown):
                pyautogui.click(button="left")
                last_click_time = current_time

            if right_eye_dist < 0.015 and (current_time-last_click_time>click_cooldown):
                pyautogui.click(button="right")
                last_click_time = current_time


    cv2.imshow("Face Cursor Control",frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()