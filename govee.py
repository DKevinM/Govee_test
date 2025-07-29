import os
import requests

API_KEY = os.getenv("GOVEE_API_KEY")
DEVICE = "32:47:DD:6E:C4:86:6B:6E"
MODEL = "H610A"

def hex_to_rgb(hex_color):
    """Convert HEX color (#rrggbb) to Govee-compatible RGB dict"""
    hex_color = hex_color.lstrip("#")
    return {
        "r": int(hex_color[0:2], 16),
        "g": int(hex_color[2:4], 16),
        "b": int(hex_color[4:6], 16)
    }


def aqhi_to_hex(aqhi):
    aqhi_map = {
        "1": "#01cbff",
        "2": "#0099cb",
        "3": "#016797",
        "4": "#fffe03",
        "5": "#ffcb00",
        "6": "#ff9835",
        "7": "#fd6866",
        "8": "#fe0002",
        "9": "#cc0001",
        "10": "#9a0100",
        "10+": "#640100"
    }

    try:
        aqhi_val = int(float(aqhi))
        return aqhi_map.get(str(min(aqhi_val, 10)), "#D3D3D3") if aqhi_val <= 10 else aqhi_map["10+"]
    except:
        return "#D3D3D3"  # Gray fallback


import requests

def get_current_aqhi(station="Strathcona County"):
    url = "https://data.environment.alberta.ca/EdwServices/aqhi/odata/CommunityAqhis?$format=json"
    try:
        response = requests.get(url)
        data = response.json()
        for entry in data["value"]:
            if entry["CommunityName"] == station:
                return entry["Aqhi"]
        return None
    except Exception as e:
        print("Failed to fetch AQHI:", e)
        return None



# === Control function ===
def set_light_from_aqhi():
    aqhi = get_current_aqhi()
    if aqhi is None:
        print("⚠️ AQHI not found.")
        return

    print(f"🌫️ Current AQHI: {aqhi}")
    hex_color = aqhi_to_hex(aqhi)
    rgb = hex_to_rgb(hex_color)

    print(f"🎨 Using color {hex_color} → RGB {rgb}")

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
            "value": rgb
        }
    }

    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("✅ Light updated successfully.")
    else:
        print(f"❌ Failed to update light: {response.status_code}\n{response.text}")


if __name__ == "__main__":
    set_light_from_aqhi()


## test
if __name__ == "__main__":
    TEST_MODE = True  # Set to False to use live data

    if TEST_MODE:
        test_aqhi = 1
        set_light_from_aqhi(test_aqhi)
    else:
        set_light_from_aqhi()  # No override → uses live AQHI
