"""IoT: simulates a wearable/ESP32 sending nightly sleep readings. Usage: python sensor_simulator.py URL API_KEY"""
import json, random, sys, time, urllib.request
url, key = sys.argv[1].rstrip("/"), sys.argv[2]
for night in range(1, 8):
    hours = round(random.uniform(5, 8.5), 1)
    req = urllib.request.Request(url + "/api/iot/sleep", json.dumps({"sleep_hours": hours}).encode(),
                                 {"Content-Type": "application/json", "X-API-Key": key})
    print(f"Night {night}: {hours}h ->", urllib.request.urlopen(req).read().decode().strip())
    time.sleep(0.5)
