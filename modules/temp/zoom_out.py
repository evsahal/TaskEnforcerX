import threading

from ppadb.client import Client as AdbClient
import os
import time


def swipe(device, x1, y1, x2, y2):
    device.shell(f'input touchscreen swipe {x1} {y1} {x2} {y2} 300')

port = 5665  # your port number here
# os.system(f'adb connect 127.0.0.1:{emulator_port}')
client = AdbClient(host="127.0.0.1", port=5037)
client.remote_connect("127.0.0.1", port)
device_emu = client.device("127.0.0.1:" + str(port))

# Simulate touch events for zoom out
#device_emu.shell('input touchscreen swipe 500 500 200 200 100')
#device_emu.shell('input touchscreen swipe 500 500 800 800 100')

thread1 = threading.Thread(target=swipe, args=(device_emu, 500, 500, 200, 200))

thread2 = threading.Thread(target=swipe, args=(device_emu, 500, 500, 800, 800))

# Start the threads (i.e., execute the swipes)
thread1.start()
thread2.start()

# Wait for both threads to finish
thread1.join()
thread2.join()