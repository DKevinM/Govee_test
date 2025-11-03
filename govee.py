import os
import requests
from typing import List, Tuple

API_KEY = os.getenv("GOVEE_API_KEY")
HEADERS = {"Govee-API-Key": API_KEY, "Content-Type": "application/json"}
GOVEE_CONTROL_URL = "https://developer-api.govee.com/v1/devices/control"

DEVICES: List[Tuple[str, str, str]] = [
    ("32:47:DD:6E:C4:86:6B:6E", "H610A", "Light Bar"),
    ("B2:1E:98:17:3C:2C:7B:5A", "H6008", "Bulb"),
]

def hex_to_rgb(hex_color: str) -> dict:
    s = hex_color.lstrip("#")
    return {"r": int(s[0:2], 16), "g": int(s[2:4], 16), "b": int(s[4:6], 16)}


def aqhi_to_hex(aqhi) -> str:
    palette = {
        "1": "#01cbff","2": "#0099cb","3": "#016797",
        "4": "#fffe03","5": "#ffcb00","6": "#ff9835",
        "7": "#fd6866","8": "#fe0002","9": "#cc0001",
        "10": "#9a0100","10+": "#640100"
    }
    try:
        v = int(float(aqhi))
        return palette.get(str(min(v, 10)), "#D3D3D3") if v <= 10 else palette["10+"]
    except Exception:
        return "#D3D3D3"  # Gray fallback


def get_current_aqhi(station: str = "Edmonton"):
    url = "https://data.environment.alberta.ca/EdwServices/aqhi/odata/CommunityAqhis?$format=json"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        for entry in r.json().get("value", []):
            if entry.get("CommunityName") == station:
                return entry.get("Aqhi")
    except Exception as e:
        print("Failed to fetch AQHI:", e)
    return None


def govee_put(device: str, model: str, cmd_name: str, cmd_value):
    payload = {"device": device, "model": model, "cmd": {"name": cmd_name, "value": cmd_value}}
    return requests.put(GOVEE_CONTROL_URL, headers=HEADERS, json=payload, timeout=20)

def set_power(device: str, model: str, on=True):
    return govee_put(device, model, "turn", "on" if on else "off")

def set_brightness(device: str, model: str, pct: int):
    pct = max(1, min(int(pct), 100))
    return govee_put(device, model, "brightness", pct)

def set_color_rgb(device: str, model: str, rgb: dict):
    return govee_put(device, model, "color", rgb)

def brightness_for_aqhi(aqhi) -> int:
    try:
        v = float(aqhi)
    except Exception:
        return 40
    if v >= 7:  # high/very high
        return 100
    if v >= 4:
        return 70
    return 50

# ── Main updater: updates ALL devices listed above ─────────────
def set_all_lights_from_aqhi(station="Edmonton"):
    aqhi = get_current_aqhi(station)
    if aqhi is None:
        print("AQHI not found.")
        return

    hex_color = aqhi_to_hex(aqhi)
    rgb = hex_to_rgb(hex_color)
    bri = brightness_for_aqhi(aqhi)
    print(f"AQHI({station}): {aqhi} → {hex_color} → RGB {rgb} | Brightness {bri}%")

    all_ok = True
    for device, model, name in DEVICES:
        try:
            set_power(device, model, True)
            r1 = set_color_rgb(device, model, rgb)
            r2 = set_brightness(device, model, bri)
            if r1.status_code == 200 and r2.status_code == 200:
                print(f"  ✅ {name} ({model}) updated")
            else:
                all_ok = False
                print(f"  ❌ {name}: color {r1.status_code}, bright {r2.status_code}")
                if r1.text: print("     resp:", r1.text)
                if r2.text: print("     resp:", r2.text)
        except Exception as e:
            all_ok = False
            print(f"  ❌ {name} error: {e}")

    if all_ok:
        print("✨ All lights updated.")

# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    # Uncomment ONE of these blocks

    # --- Normal live mode ---
    # set_all_lights_from_aqhi("Edmonton")

    # --- Manual color test mode ---
    print(" Manual color test")
        # "1": "#01cbff","2": "#0099cb","3": "#016797",
        # "4": "#fffe03","5": "#ffcb00","6": "#ff9835",
        # "7": "#fd6866","8": "#fe0002","9": "#cc0001",
        # "10": "#9a0100","10+": "#640100"
    manual_hex = "#01cbff"  # pick your color here (#RRGGBB)
    rgb = hex_to_rgb(manual_hex)
    print(f" Testing color {manual_hex} → RGB {rgb}")
    for device, model, name in DEVICES:
        set_power(device, model, True)
        set_color_rgb(device, model, rgb)
        set_brightness(device, model, 80)
        print(f"  ✅ {name} set to {manual_hex}")
