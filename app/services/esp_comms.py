import os
import requests
from app.models.models import Goal

# Where your ESP32 is on your LAN; override via env if you want
# ESP32_BASE_URL = os.getenv("ESP32_BASE_URL", "http://192.168.4.77")
ESP32_BASE_URL = os.getenv("ESP32_BASE_URL", "http://192.168.4.78")

def push_goals_to_esp(goals: list[Goal]) -> None:
    """
    Push new goals to the ESP32 over WiFi.

    The ESP32 expects one goal per POST to /add with a raw text body.
    For points, we append the integer to the end of the text, e.g.
      "Walk the dog 5"
    so the firmware's parseGoalLine() logic can extract it.
    """
    if not goals:
        return

    for g in goals:
        print("‼️‼️‼️Received as: ", g)
        # Build the text exactly how the ESP expects it
        text = g['goal_text'].strip()
        pts = g['points']

        print(pts)

        if pts is not None:
            try:
                pts_int = int(pts)
            except (TypeError, ValueError):
                pts_int = None
        else:
            pts_int = None

        if pts_int and pts_int > 0:
            payload = f"{text} {pts_int}"
        else:
            payload = text

        if not payload:
            continue

        try:
            resp = requests.post(
                f"{ESP32_BASE_URL}/add",
                data=payload,
                timeout=1.5,  # short so Twilio webhook doesn’t hang
            )
            if resp.status_code != 200:
                print(f"⚠️ ESP push failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            # Don't break Twilio flow if ESP is offline
            print(f"⚠️ Error pushing goal to ESP: {e}")
