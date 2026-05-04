import os
import requests
from typing import List, Tuple
import time

LAST_FILE = "last_aqhi.txt"

def has_changed(station, new_val):
    filename = f"last_{station}.txt"

    try:
        with open(filename, "r") as f:
            old = f.read().strip()
    except:
        old = None

    if str(new_val) != old:
        with open(filename, "w") as f:
            f.write(str(new_val))
        return True

    return False
    

GOVEE_CONTROL_URL = "https://developer-api.govee.com/v1/devices/control"

DEVICES = [
    ("32:47:DD:6E:C4:86:6B:6E", "H610A", "Light Bar", "Genesee", os.getenv("GOVEE_API_KEY")),
    ("1D:B0:D8:BF:C5:C6:35:1D", "H6173", "Edmonton East", "Edmonton East", os.getenv("GOVEE_API_KEY_2")),
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


def get_current_aqhi(station: str):
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


def govee_put(device: str, model: str, cmd_name: str, cmd_value, api_key):
    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "device": device,
        "model": model,
        "cmd": {"name": cmd_name, "value": cmd_value}
    }
    return requests.put(GOVEE_CONTROL_URL, headers=headers, json=payload, timeout=20)



def set_power(device, model, api_key, on=True):
    return govee_put(device, model, "turn", "on" if on else "off", api_key)

def set_brightness(device, model, api_key, pct: int):
    pct = max(1, min(int(pct), 100))
    return govee_put(device, model, "brightness", pct, api_key)

def set_color_rgb(device, model, api_key, rgb: dict):
    return govee_put(device, model, "color", rgb, api_key)



def brightness_for_aqhi(aqhi) -> int:
    try:
        v = float(aqhi)
    except Exception:
        return 40
    if v >= 7:  
        return 100
    if v >= 4:
        return 70
    return 50

# ── Main updater: updates ALL devices listed above ─────────────
def set_all_lights_from_aqhi(force=False):

    for device, model, name, station, api_key in DEVICES:

        if not api_key:
            print(f"{name}: API key missing — skipping")
            continue

        aqhi = get_current_aqhi(station)

        if aqhi is None:
            print(f"{name}: AQHI not found for {station}")
            continue

        safe_station = station.replace(" ", "_")
        
        if not force:
            if not has_changed(safe_station, aqhi):
                print(f"{name}: AQHI unchanged ({aqhi}) — skipping")
                continue
        else:
            print(f"{name}: FORCE update → AQHI {aqhi}")

        hex_color = aqhi_to_hex(aqhi)
        rgb = hex_to_rgb(hex_color)
        bri = brightness_for_aqhi(aqhi)

        print(f"{name} ({station}) → AQHI {aqhi} → {hex_color}")

        r0 = set_power(device, model, api_key, True)
        print(f"{name} power:", r0.status_code, r0.text)
        time.sleep(1)

        r1 = set_color_rgb(device, model, api_key, rgb)
        print(f"{name} color:", r1.status_code, r1.text)
        time.sleep(1)

        r2 = set_brightness(device, model, api_key, bri)
        print(f"{name} bright:", r2.status_code, r2.text)

    
# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    force = os.getenv("FORCE_UPDATE", "false").lower() == "true"
    print("FORCE MODE:", force)
    set_all_lights_from_aqhi(force=force)

