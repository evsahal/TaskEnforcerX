import os
import time
import cv2
import numpy as np
from ppadb.client import Client as AdbClient

try:
    emulator_port = 5685  # your port here
    client = AdbClient(host="127.0.0.1", port=5037)
    print("Here?1")
    client.remote_connect("127.0.0.1", emulator_port)
    print("Here?2")
    device_emu = client.device(f"127.0.0.1:{emulator_port}")
    swipe_coordinates = {1: '450 370 120 535', 2: '53 380 450 580', 3: '120 535 450 370', 4: '450 580 53 380'}

    for i in range(5):
        device_emu.shell(f'input swipe ' + swipe_coordinates[2] + ' 1000')
    for i in range(5):
        device_emu.shell(f'input swipe ' + swipe_coordinates[4] + ' 1000')
    print("Done")

except Exception as e:
    print(e)
    print("Some issue")