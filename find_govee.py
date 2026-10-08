
import os
import requests

API_URL = "https://developer-api.govee.com/v1/devices"

API_KEYS = {
    "Account 1": os.getenv("GOVEE_API_KEY"),
    "Account 2": os.getenv("GOVEE_API_KEY_2"),
}

for account, api_key in API_KEYS.items():

    if not api_key:
        print(f"{account}: No API key configured")
        continue

    response = requests.get(
        API_URL,
        headers={"Govee-API-Key": api_key},
        timeout=20
    )

    print(f"\n{account}: HTTP {response.status_code}")
    response.raise_for_status()

    devices = response.json().get("data", {}).get("devices", [])

    for device in devices:
        print("--------------------------")
        print("Name:", device.get("deviceName"))
        print("MAC:", device.get("device"))
        print("Model:", device.get("model"))
        print("Controllable:", device.get("controllable"))
