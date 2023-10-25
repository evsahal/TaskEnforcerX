import os
import time
import cv2
import numpy as np
from ppadb.client import Client as AdbClient


def calibrate(device_emu):
    print("calibrate")
    #template_image = cv2.imread(r"C:\Users\91974\OneDrive\Documents\Project\Evony\images\evony\tmp\lv6_boss_540p.png")
    #template_image = cv2.imread(r"C:\Users\91974\OneDrive\Documents\Project\Evony\images\evony\tmp\b17_test1.png")
    template_image = cv2.imread(r"C:\Users\91974\OneDrive\Documents\Project\TaskEnforcerX\images\evony\540p\monsters\lv18_boss_540p.png")
    ss_count = 60
    ss_delay = 0.1
    ss_list = []
    print(f"capturing ss {ss_count} times...")
    for _ in range(ss_count):
        ss_list.append(cv2.imdecode(np.frombuffer(device_emu.screencap(), np.uint8), cv2.IMREAD_COLOR))
        time.sleep(ss_delay)
    calibr = {'start': 0.65, 'end': 0.95}
    calibr_iterations = int((calibr['end'] - calibr['start']) / 0.01) + 2
    thresholds = []
    for index, ss in enumerate(ss_list):
        for i in range(calibr_iterations):
            threshold = round(calibr['start'] + i * 0.01, 2)
            # print(threshold)
            result = cv2.matchTemplate(ss, template_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val <= threshold:
                thresholds.append(round(threshold - 0.01, 2))
                print(f"{index + 1}: threshold point : {round(threshold - 0.01, 2)}")
                break
    print(f"ss matches: {len(thresholds)}/{ss_count}")
    print(f"minimum threshold: {min(thresholds)}")

try:
    emulator_port = 5685  # your port here
    os.system(f'adb connect 127.0.0.1:{emulator_port}')  # make sure you have set adb to your system env path
    client = AdbClient(host="127.0.0.1", port=5037)
    device_emu = client.device(f"127.0.0.1:{emulator_port}")
    calibrate(device_emu)
except Exception as e:
    print(e)
