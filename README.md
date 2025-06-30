# 20-20-20 Eye Break Reminder Tool

An eye health application that follows the 20-20-20 rule: Every 20 minutes, look at something 20 feet away for at least 20 seconds.

## Features

- Uses your webcam to track whether you're looking at the screen
- Only counts continuous screen time (resets when you look away)
- Sends notifications when it's time to take a break
- Runs in the background with minimal resource usage

## Requirements

- Python 3.10+
- Webcam
- macOS (primary support, other platforms may work)

## Installation

1. Clone this repository
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Make sure your virtual environment is activated, then run:

```bash
python main.py
```

The app will run in the background and monitor your eye activity. When you've been looking at the screen for 20 minutes, it will notify you to take a break.

## Privacy

This application does not store or transmit any video data. All processing is done locally on your computer.

## Configuration

You can modify the settings in `config.json` to customize:
- Screen time duration before breaks
- Break duration
- Off-screen detection threshold
- Notification preferences 