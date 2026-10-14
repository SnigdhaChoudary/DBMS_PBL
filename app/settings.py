"""Remembers the user's zoom level between runs (stored in the user's home folder)."""
import json
import os

PATH = os.path.join(os.path.expanduser("~"), ".smart_parking_settings.json")
ZOOM_LEVELS = (80, 90, 100, 110, 125, 140, 160, 180, 200)
DEFAULT_ZOOM = 100


def load_zoom():
    try:
        with open(PATH, "r", encoding="utf-8") as fh:
            value = int(json.load(fh).get("zoom", DEFAULT_ZOOM))
        return value if value in ZOOM_LEVELS else DEFAULT_ZOOM
    except (OSError, ValueError, TypeError):
        return DEFAULT_ZOOM


def save_zoom(percent):
    try:
        with open(PATH, "w", encoding="utf-8") as fh:
            json.dump({"zoom": int(percent)}, fh)
    except OSError:
        pass  # a read-only home folder must never stop the program
