# PARALYSEZ PC Cursor Control

Control your computer's mouse using a webcam. Choose **hand tracking** or **face tracking**. The app mirrors the camera preview, calibrates a neutral position, and displays the active mode and actions on screen.

## Features

- Smooth cursor movement from the index fingertip or the center of your nose.
- A three-second neutral-position calibration and a dead zone to reduce accidental movement.
- Hand gestures for left and right click, scrolling, and recalibration.
- Face gestures for clicks and scrolling.
- On-screen camera preview, keyboard controls, and safe camera cleanup when you quit.

## Requirements

- Windows, macOS, or Linux with Python 3.10–3.12.
- A working webcam.
- Camera access permission for the terminal or Python application.

Install the packages in a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Start the app

Choose a mode explicitly:

```bash
python main.py --mode hand
python main.py --mode face
```

Or run `python main.py` in a terminal and choose a mode from the menu. If your webcam is not the default camera, select another device index, for example `python main.py --mode hand --camera 1`.

## Controls and gestures

### Hand tracking

1. Show one hand to the camera and hold the index finger still while the three-second calibration completes.
2. Move the index fingertip relative to the green neutral box to move the pointer.
3. Raise the pinky to enter gesture mode. With the pinky raised, move the index finger below the box for a left click, above it for a right click, left of it to scroll up, or right of it to scroll down.
4. Raise all four fingers (index, middle, ring, and pinky) to start calibration again.

### Face tracking

1. Look toward the camera and hold still while the three-second calibration completes.
2. Move your nose relative to the green neutral box to move the pointer.
3. Close the left eye to left-click or close the right eye to right-click.
4. Open your mouth to enter scroll mode. Close the left eye to scroll up, or close the right eye to scroll down.

Eye and mouth detection can vary with lighting, camera position, and individual faces. Keep your face well lit and centered in the preview.

### Keyboard and emergency stop

- Press **C** in the camera window to recalibrate.
- Press **Q** or **Esc** to quit.
- Move the mouse to the top-left corner of the screen to trigger PyAutoGUI's emergency fail-safe.

## Troubleshooting

- **Missing dependency:** activate the virtual environment and run `python -m pip install -r requirements.txt`.
- **Camera won't open:** close other apps using the webcam, check OS camera permission, or try `--camera 1`.
- **Pointer is too sensitive:** change `ACCELERATION`, `MAX_SPEED`, or `DEAD_ZONE` near the top of `main.py`.
- **Import or installation issue:** use a supported 64-bit Python version (3.10–3.12) and reinstall the pinned requirements in a fresh virtual environment. This project pins MediaPipe 0.10.21 because newer MediaPipe releases removed the API it uses.

## Project files

- `main.py` — app menu, webcam tracking, calibration, gestures, and cursor control.
- `requirements.txt` — Python dependencies.
- `hand_tracking_cursor_control.py` and `face_gestures_cursor_control.py` — small launchers kept for convenience; use `main.py` for options.
