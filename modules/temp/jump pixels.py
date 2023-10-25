import os
import os
import time
import cv2
import numpy as np
from ppadb.client import Client as AdbClient

try:
    emulator_port = 5665  # your port here
    client = AdbClient(host="127.0.0.1", port=5037)
    client.remote_connect("127.0.0.1", emulator_port)
    device_emu = client.device(f"127.0.0.1:{emulator_port}")
    device_emu.shell(f'wm overscan 00,00,00,00')

except Exception as e:
    print(e)
    print("Some issue")

