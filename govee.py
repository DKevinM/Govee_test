import requests

API_KEY = os.getenv("GOVEE_API_KEY")
DEVICE = "32:47:DD:6E:C4:86:6B:6E"
MODEL = "H610A"

# === Define AQHI thresholds and corresponding RGB colors ===
def get_color_for_aqhi(aqhi):
    if aqhi <= 3:
        return {"r": 0, "g": 255, "b": 0}       # Green
    elif aqhi <= 6:
        return {"r": 255, "g": 255, "b": 0}     # Yellow
    elif aqhi <= 9:
        return {"r": 255, "g": 165, "b": 0}     # Orange
    else:
        return {"r": 255, "g": 0, "b": 0}       # Red

# === Control function ===
def set_light_color(aqhi_value):
    color = get_color_for_aqhi(aqhi_value)
    url = "https://developer-api.govee.com/v1/devices/control"
    headers = {
        "Govee-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "device": DEVICE,
        "model": MODEL,
        "cmd": {
            "name": "color",
            "value": color
        }
    }

    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"✅ Light color set for AQHI {aqhi_value}: {color}")
    else:
        print(f"❌ Failed to set color: {response.status_code}, {response.text}")

# === Example usage ===
if __name__ == "__main__":
    aqhi_value = 7  # Replace this with live AQHI later
    set_light_color(aqhi_value)
