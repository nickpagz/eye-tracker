# 📝 Product Requirements Document (PRD)

## Project Title
**20-20-20 Eye Break Reminder Tool**

---

## Purpose
The purpose of this application is to promote eye health by enforcing the **20-20-20 rule**: Every 20 minutes, users should look at something 20 feet away for at least 20 seconds. The tool uses the **computer's built-in webcam** to track whether the user is **actively looking at the screen** and enforces the rule based on actual behavior rather than a static timer.

---

## Goals
- Use **eye tracking** to detect when the user is continuously looking at the screen.
- Trigger a **notification** if the user has looked at the screen for 20 uninterrupted minutes.
- Reset the timer if the user **looks away** for a meaningful break (e.g., >10 seconds).
- Run **lightweight and unobtrusively** in the background.

---

## Key Features

### ✅ Eye Tracking
- Detect presence of a face using webcam.
- Identify eye landmarks and determine if user is looking generally **toward the screen**.
- Track **continuous gaze duration**.

### ⏱️ Timer Logic
- Start a 20-minute countdown only when gaze is detected.
- Pause/reset countdown if the user looks away for more than a set threshold (default: 10 seconds).
- Optional: Configurable gaze duration threshold (e.g., alert after 15 minutes instead of 20).

### 🔔 Notifications
- Trigger a **visual notification or modal** encouraging the user to look away for 20 seconds.
- Optional: Play a sound or use native macOS notifications (`osascript` or `plyer`).
- Optional: Countdown timer UI during the 20-second break.

### 📈 Session Logging (Optional)
- Log data like session duration, number of breaks, gaze time vs. break time.
- Save logs in JSON or CSV format.

---

## Non-Goals
- No need for biometric eye movement precision or gaze calibration.
- Does not need to track exact 20-foot distance—just estimate that the user is **not** looking at the screen.

---

## Platform
- **Primary**: macOS (with built-in webcam).
- **Secondary** (future): Cross-platform (Linux, Windows).

---

## Technical Stack

### Languages & Frameworks
- **Python 3.10+**
- **OpenCV** – Webcam access & image capture.
- **MediaPipe** – Face & eye landmark tracking.
- **Tkinter or Plyer** – Lightweight UI & notifications.
- **Optional**: PyQt for GUI, `matplotlib` or `pandas` for logging/visualization.

### Dependencies
```bash
pip install opencv-python mediapipe plyer
```

---

## Architecture Overview

### Main Modules

| Module | Description |
|--------|-------------|
| `camera.py` | Initializes webcam and captures frames. |
| `eye_tracker.py` | Uses MediaPipe to extract eye/face landmarks and determine gaze direction. |
| `gaze_timer.py` | Tracks time spent looking at screen. Handles breaks and resets. |
| `notifier.py` | Handles break reminders via system popups or GUI alerts. |
| `logger.py` *(optional)* | Records gaze sessions and break events to a file. |
| `main.py` | Ties it all together – orchestrates frame capture, gaze detection, timer updates, and notifications. |

---

## Eye Detection Logic

1. Use MediaPipe’s Face Mesh to extract facial landmarks.
2. Use eye and iris landmarks to determine rough gaze direction.
   - Eyes looking center = "screen-focused"
   - Eyes or head turned away = "off-screen"
3. Use logic thresholds:
   - If screen-focused for > 20 mins → trigger break.
   - If user looks away > 10 sec → reset screen time counter.

---

## UX & UI

- **Tray Icon** (Optional): Minimal icon showing app status.
- **Popup/Modal Notification**: When a break is due, show a popup:
  ```
  Time for a break!
  Look 20 feet away for 20 seconds.
  ```
- **Countdown Timer**: Optional countdown UI for 20-second break.

---

## Future Features (Stretch Goals)
- Blink rate detection to gauge fatigue.
- Head pose estimation for more reliable off-screen detection.
- Integration with productivity tools (e.g., pausing videos or muting notifications).
- Gamification: Earn badges for consistent breaks.

---

## Configuration (Optional `config.json`)
```json
{
  "max_screen_time_minutes": 20,
  "min_break_duration_seconds": 20,
  "off_screen_threshold_seconds": 10,
  "use_sound_notifications": true
}
```

---

## Milestones

| Milestone | Deliverable |
|-----------|-------------|
| M1 | Webcam feed + Face detection working |
| M2 | Eye tracking + screen gaze detection logic |
| M3 | Timer tracking based on gaze status |
| M4 | Notifications and alerts |
| M5 | (Optional) Logging & session tracking |
| M6 | Packaged app (with tray icon or installer) |

---

## Risks & Considerations
- **Privacy**: Webcam usage might concern users. Assure that no video is stored or uploaded.
- **Performance**: Must run efficiently in background with minimal CPU usage.
- **False Positives**: Gaze estimation may occasionally misfire—tune thresholds and allow user customization.

---

## Example Use Case
> Alice is coding for 3 hours. The tool detects that she's looked at her screen without any significant break for 20 minutes. It notifies her with a popup: “Time to look away!” She turns her head to the side and stares out the window for 30 seconds. The app resets the timer and resumes tracking. Alice ends her workday with healthy eyes. 👀
