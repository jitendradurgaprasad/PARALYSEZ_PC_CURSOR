# Import OpenCV for camera access and image processing
import cv2

# Import MediaPipe for hand tracking
import mediapipe as mp

# Import PyAutoGUI to control mouse cursor
import pyautogui

# Import time module for calibration timing
import time


# This enables safety feature:
# If mouse moves to top-left corner, program stops automatically
pyautogui.FAILSAFE = True


# Get screen resolution of the laptop
screen_w, screen_h = pyautogui.size()


# Initialize MediaPipe Hands module
mp_hands = mp.solutions.hands

# Configure hand tracking parameters
hands = mp_hands.Hands(
    static_image_mode=False,        # False means continuous video tracking
    max_num_hands=1,                # Detect only one hand
    min_detection_confidence=0.7,   # Minimum confidence to detect hand
    min_tracking_confidence=0.7     # Minimum confidence to continue tracking
)

# Utility to draw hand landmarks on screen
mp_draw = mp.solutions.drawing_utils


# Open laptop camera (0 means default webcam)
cap = cv2.VideoCapture(0)


# These variables store center (neutral) position after calibration
neutral_x = None
neutral_y = None

# Dead zone size around neutral position
dead_zone = 30

# Boolean to check if calibration is completed
calibrated = False

# Stores starting time of calibration
calibration_start = None


# Speed control variables
acceleration = 0.14     # Sensitivity of cursor movement
max_speed = 40        # Maximum allowed cursor speed per frame


# Function to check if all four fingers are up (used for recalibration)
def all_fingers_up(hand_landmarks):
    tips = [8, 12, 16, 20]  # Index, middle, ring, pinky tips
    count = 0

    for tip in tips:
        # If fingertip is above its lower joint → finger is up
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1

    return count == 4



# Main loop runs continuously
while True:

    # Read frame from camera
    success, frame = cap.read()

    if not success:
        break

    # Flip image horizontally (mirror effect)
    frame = cv2.flip(frame, 1)

    # Get frame height and width
    h, w, _ = frame.shape


    # Convert image from BGR to RGB (MediaPipe requires RGB)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process frame to detect hands/
    results = hands.process(rgb)


    # If hand is detected
    if results.multi_hand_landmarks:


        for hand_landmarks in results.multi_hand_landmarks:

            # Draw hand skeleton on screen
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get index finger tip (landmark 8)
            index_tip = hand_landmarks.landmark[8]

            # Convert normalized coordinates (0–1) to pixel coordinates
            x = int(index_tip.x * w)
            y = int(index_tip.y * h)


            # ---------------- CALIBRATION PHASE ----------------
            if not calibrated:

                # Start timer if not started
                if calibration_start is None:
                    calibration_start = time.time()

                # Calculate elapsed time
                elapsed = time.time() - calibration_start
                remaining = int(5 - elapsed)

                # Show countdown on screen
                cv2.putText(frame, f"Calibrating: {remaining}",
                            (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 2)

                # After 5 seconds, set neutral position
                if elapsed >= 5:
                    neutral_x = x
                    neutral_y = y
                    calibrated = True
                    print("Calibration Complete")

                continue


            # ---------------- RECALIBRATION ----------------
            if all_fingers_up(hand_landmarks):

                # Reset everything
                calibrated = False
                calibration_start = None
                neutral_x = None
                neutral_y = None

                print("Recalibration Triggered")
                continue


            # ---------------- DRAW DEAD ZONE ----------------
            cv2.rectangle(frame,
                          (neutral_x - dead_zone, neutral_y - dead_zone),
                          (neutral_x + dead_zone, neutral_y + dead_zone),
                          (0, 255, 0), 2)


            # ---------------- AXIAL OVERFLOW ----------------
            if x > neutral_x + dead_zone:
                overflow_x = x - (neutral_x + dead_zone)
            elif x < neutral_x - dead_zone:
                overflow_x = x - (neutral_x - dead_zone)
            else:
                overflow_x = 0

            if y > neutral_y + dead_zone:
                overflow_y = y - (neutral_y + dead_zone)
            elif y < neutral_y - dead_zone:
                overflow_y = y - (neutral_y - dead_zone)
            else:
                overflow_y = 0


            # ---------------- SPEED SCALING ----------------
            dx = overflow_x * acceleration
            dy = overflow_y * acceleration

            # Limit maximum speed
            dx = max(min(dx, max_speed), -max_speed)
            dy = max(min(dy, max_speed), -max_speed)

            # Get current mouse position
            current_mouse_x, current_mouse_y = pyautogui.position()

            # Add movement
            new_x = current_mouse_x + dx
            new_y = current_mouse_y + dy

            # Move cursor
            pyautogui.moveTo(new_x, new_y)


    # Show camera window
    cv2.imshow("Axial Finger Mouse", frame)

    # Exit when ESC key is pressed
    if cv2.waitKey(1) & 0xFF == 27:
        break


# Release camera and close windows
cap.release()
cv2.destroyAllWindows()