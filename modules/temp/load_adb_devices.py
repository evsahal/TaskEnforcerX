import threading

from ppadb.client import Client as AdbClient
import os
import time


port = 5665  # your port number here
client = AdbClient(host="127.0.0.1", port=5037)
#client.remote_connect("127.0.0.1", port)
#device_emu = client.device("127.0.0.1:" + str(port))
devices = client.devices()
for device in devices:
    print(device.serial.split(":"))

