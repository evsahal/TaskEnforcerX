#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import re
from time import sleep
from datetime import datetime, timedelta
import numpy as np
import cv2
from modules import ImageRecognitionUtils as img, GeneralUtils as g_util
from .Query import *
from modules import DatabaseUtils as dbUtils
import pytesseract
import os
from .ConfigurationThread import *


def locateWorldMap(self, img_lib_path):
    alliance_city_return = cv2.imread(img_lib_path + '/other/alliance_city_return_btn.png')
    world_map_return = cv2.imread(img_lib_path + '/other/world_map_return_btn.png')
    world_map_btn = cv2.imread(img_lib_path + '/other/world_map.png')
    construct_btn = cv2.imread(img_lib_path + '/other/construct_ideal_land.png')
    while True:
        src_img = self.capture_screen(ads=True)
        if img.check_template_match(src_img, alliance_city_return):
            if img.check_template_match(src_img, world_map_btn):
                return True
            if img.check_template_match(src_img, construct_btn):
                tap_cords = img.get_template_coordinates(src_img, alliance_city_return)
                self.device_emu.shell(f'input tap ' + str(tap_cords[1]) + ' ' + str(tap_cords[2]))
                sleep(3)
        if img.check_template_match(src_img, world_map_return):
            tap_cords = img.get_template_coordinates(src_img, world_map_return)
            self.device_emu.shell(f'input tap ' + str(tap_cords[1]) + ' ' + str(tap_cords[2]))
            sleep(3)
            # continue will again check the worldmap_btn
            continue
        # above conditions didn't meet, so press back and loop again
        self.device_emu.shell('input keyevent KEYCODE_BACK')
        sleep(1)


def attemptCustomCords(self, img_lib_path, cords):
    if not cords:
        # Custom Cords not set, hence skip
        return False
    # Validate X and Y Cords
    if not cords['x'].isnumeric() or not cords['y'].isnumeric():
        self.invokeDeviceConsole("Skipping custom coordinates option due to invalid coordinates provided.")
        return False
    if not (1 <= int(cords['x']) <= 1200) or not (1 <= int(cords['y']) <= 1200):
        self.invokeDeviceConsole("Skipping custom coordinates option due to invalid coordinates provided.")
        return False
    sleep(1)
    src_img = self.capture_screen()
    magnifying_glass = img.get_template_coordinates(src_img, cv2.imread(img_lib_path + 'other/magnifying_glass.png'))
    if magnifying_glass[0]:
        self.invokeDeviceConsole("Navigating to custom coordinates.")
        self.device_emu.shell(f'input tap ' + str(magnifying_glass[1]) + ' ' + str(magnifying_glass[2]))
        sleep(1)
        src_img = self.capture_screen()
        # Setting X cords
        cords_search_x = img.get_template_coordinates(src_img, cv2.imread(img_lib_path + 'other/cords_search_x.png'))
        self.device_emu.shell(f'input tap ' + str(cords_search_x[1] + 20) + ' ' + str(cords_search_x[2]))
        sleep(1)
        for i in range(5):
            self.device_emu.shell('input keyevent KEYCODE_DEL')
        self.device_emu.shell(f"input text {cords['x']}")
        self.device_emu.shell('input keyevent KEYCODE_ENTER')

        # Setting Y cords
        cords_search_y = img.get_template_coordinates(src_img, cv2.imread(img_lib_path + 'other/cords_search_y.png'))
        self.device_emu.shell(f'input tap ' + str(cords_search_y[1] + 20) + ' ' + str(cords_search_y[2]))
        sleep(1)
        for i in range(5):
            self.device_emu.shell('input keyevent KEYCODE_DEL')
        self.device_emu.shell(f"input text {cords['y']}")
        self.device_emu.shell('input keyevent KEYCODE_ENTER')
        # Hit Go
        cords_search_go = img.get_template_coordinates(src_img, cv2.imread(img_lib_path + 'other/cords_search_go.png'))
        self.device_emu.shell(f'input tap ' + str(cords_search_go[1] + 20) + ' ' + str(cords_search_go[2]))
        return True


def scanMapSS(self, scan_list, src_img, controls, img_lib_path, old_loc):
    matched_loc = []
    for item in scan_list:
        template_match = cv2.matchTemplate(src_img, item['img'], cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        # Find the best match location
        while self.is_running:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(template_match)
            if max_val >= threshold:
                if max_loc not in matched_loc:
                    center_x = int(max_loc[0] + 0.5 * item['img'].shape[1])
                    center_y = int(max_loc[1] + 0.5 * item['img'].shape[0])
                    self.device_emu.shell(f'input tap ' + str(center_x) + ' ' + str(
                        center_y + 0))  # +20 to avoid wrong clicks on some cases(get base area)
                    time.sleep(1)
                    # Verify screen/cords didnt moved on the item tap
                    old_cord_img = get_map_cords_img(src_img, img_lib_path)
                    ss_cap = self.capture_screen()
                    new_cord_img = get_map_cords_img(ss_cap, img_lib_path)
                    if old_cord_img[0] and new_cord_img[0]:
                        if not img.check_image_match(old_cord_img[1], new_cord_img[1]):
                            #print("Location changed :: ",max_loc)  # Location changed ::  (62, 280) (138, 644) (277, 49) (117, 786)
                            self.invokeDeviceConsole("Location changed after the selection")
                            # self.device_emu.shell('input keyevent KEYCODE_BACK')
                            # Undo the selection, click on options btn twice to remove the selection
                            options_img = cv2.imread(img_lib_path + 'other/options_btn.png')
                            options_btn = img.get_template_coordinates(ss_cap, options_img)
                            if options_btn[0]:
                                # print("Options Btn Found, ", options_btn)
                                self.invokeDeviceConsole("Updating the new location")
                                self.device_emu.shell(f'input tap ' + str(options_btn[1]) + ' ' + str(options_btn[2]))
                                sleep(1)
                                self.device_emu.shell(f'input tap ' + str(options_btn[1]) + ' ' + str(options_btn[2]))
                                sleep(1)
                                return False, matched_loc
                        # TODO verify already matched cords are skipped when screen is moved
                    matched_loc.append(max_loc)
                    # print("Locations :: ",matched_loc)  # Locations ::  [(219, 280)] [(211, 644)] [(278, 121)] [(210, 780)]
                    share_info = False, None
                    # Type Boss Scan
                    if item['type'] == 'boss_scan':
                        share_info = bossScan(self, item, controls, center_x, center_y, scan_list, img_lib_path)
                    # Type Normal monster Scan
                    elif item['type'] == 'monster_scan':
                        share_info = monsterScan(self, item, controls, center_x, center_y, scan_list,
                                                 img_lib_path)
                    # Type Scoutables Scan
                    elif item['type'] == 'scoutables_scan':
                        share_info = scoutablesScan(self, item, controls, center_x, center_y, scan_list,
                                                    img_lib_path)
                    # Type Tile Scan
                    elif item['type'] == 'tile_scan':
                        share_info = tileScan(self, item, controls, center_x, center_y, scan_list, img_lib_path)
                    # TODO skip the cords sharing when its already matched before
                    # Share based on the option selected
                    confirm_share_img = cv2.imread(img_lib_path + 'other/confirm_share.png')
                    if controls['share_collective'] and share_info[0]:
                        # TODO sharing to collective
                        self.device_emu.shell('input keyevent KEYCODE_BACK')
                        # print("Sharing to collective")
                    elif controls['share_whisper'] and share_info[0]:
                        # print("Sharing to whisper")
                        self.invokeDeviceConsole("Sharing to whisper")
                        share_window_info = share_info[1]
                        self.device_emu.shell(
                            f'input tap ' + str(share_window_info[1][1] + share_window_info[3]) + ' ' + str(
                                share_window_info[1][2] + share_window_info[2] + 150))
                        sleep(1)
                        share_window = self.capture_screen()
                        confirm_share = img.get_template_coordinates(share_window, confirm_share_img)
                        if confirm_share[0]:
                            self.device_emu.shell(
                                f'input tap ' + str(confirm_share[1]) + ' ' + str(confirm_share[2]))
                    elif controls['share_ac'] and share_info[0]:
                        # print("Sharing to ac")
                        self.invokeDeviceConsole("Sharing to alliance chat")
                        share_window_info = share_info[1]
                        self.device_emu.shell(
                            f'input tap ' + str(share_window_info[1][1] + share_window_info[3]) + ' ' + str(
                                share_window_info[1][2] + share_window_info[2] + 50))
                        sleep(1)
                        share_window = self.capture_screen()
                        confirm_share = img.get_template_coordinates(share_window, confirm_share_img)
                        if confirm_share[0]:
                            self.device_emu.shell(
                                f'input tap ' + str(confirm_share[1]) + ' ' + str(confirm_share[2]))
                # Set the matched region to a low value, so it won't be matched again
                template_match[
                max_loc[1] - item['img'].shape[0] // 2:max_loc[1] + item['img'].shape[0] // 2,
                max_loc[0] - item['img'].shape[1] // 2:max_loc[0] + item['img'].shape[1] // 2] = -1
            else:
                break
    return True, None


def get_map_cords_img(src_img, img_lib_path):
    mag_glass_img = cv2.imread(img_lib_path + 'other/magnifying_glass.png')
    w, h = mag_glass_img.shape[:-1]
    cords = img.get_template_match_coordinates(src_img, mag_glass_img)
    if cords[0]:
        # Change roi numeric values(5/180) to dynamic when multiple res is set.(present: 540p)
        roi = src_img[cords[2]:cords[2] + h + 5, cords[1]:cords[1] + 180].copy()
        return True, roi
    return False, None


def getShareWindowDetails(share_window, img_lib_path):
    cord_template = cv2.imread(img_lib_path + 'other/share_cord_text.png')
    share_cords = img.get_template_match_coordinates(share_window, cord_template)
    share_cords_w, share_cords_h = cord_template.shape[:-1]
    # cropping the share cordinate portion
    cords_img = share_window[share_cords[2]:share_cords[2] + share_cords_w,
                share_cords[1] + share_cords_h:share_cords[1] + (share_cords_h * 2)]
    # Green text to black and rest to white
    # Convert the image to HSV color space
    hsv = cv2.cvtColor(cords_img, cv2.COLOR_BGR2HSV)
    # Define the lower and upper thresholds for the green color
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    # Create a mask for the green color
    mask = cv2.inRange(hsv, lower_green, upper_green)
    # Replace the green color with black
    result = cv2.bitwise_and(cords_img, cords_img, mask=mask)
    result[mask > 0] = (0, 0, 0)
    # Replace the remaining pixels with white
    result[mask == 0] = (255, 255, 255)

    # Apply median filtering for noise reduction
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    denoised_image = cv2.medianBlur(gray, ksize=1)

    pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
    cords_txt = pytesseract.image_to_string(denoised_image,
                                            config='--psm 6 --oem 3 -c tessedit_char_whitelist=:0123456789').replace(
        "\n", "")
    # print(cords_txt)
    # cv2.imwrite(r'images/evony/tmp/cords_img.png', cords_img)
    # cv2.imwrite(r'images/evony/tmp/cords_text.png', denoised_image)
    # print("image saved")
    xy_cords = cords_txt.split(':')
    xy_cords = xy_cords[len(xy_cords) - 2], xy_cords[len(xy_cords) - 1]
    # print("Cords: ", xy_cords)  # Cords:  ('716', '1115')
    return xy_cords, share_cords, share_cords_w, share_cords_h


def tileScan(self, item, controls, center_x, center_y, scan_list, img_lib_path):
    print("Tile Scan here")
    return False, None


def monsterScan(self, item, controls, center_x, center_y, scan_list, img_lib_path):
    # print("Monster Scan found, ", item['name'])
    self.invokeDeviceConsole(f"Verifying {item['name']} match")
    attack_options = self.capture_screen()
    attack_btn = img.get_template_coordinates(attack_options, cv2.imread(
        img_lib_path + 'monsters/boss_attack_option.png'))
    # Checking attack option is present or not, if not, skipping
    if attack_btn[0] is False:
        # print("No monster found. wrong match. skipping")
        self.invokeDeviceConsole("Wrong match found. Hence skipping")
        time.sleep(1)
        self.device_emu.shell(f'input tap ' + str(center_x) + ' ' + str(center_y + 25))
        return False, None
    self.invokeDeviceConsole("Normal monster match verified")
    # Open the share window to read the cords
    share_window = self.capture_screen()
    share_btn = img.get_template_coordinates(share_window, cv2.imread(
        img_lib_path + 'monsters/boss_share_option.png'))
    if not share_btn[0]:
        # Deselect the selection
        self.device_emu.shell(f'input tap ' + str(center_x) + ' ' + str(
            center_y + 0))  # +20 to avoid wrong clicks on some cases(get base area)
        return False, None
    # When share btn is present
    self.device_emu.shell(f'input tap ' + str(share_btn[1]) + ' ' + str(share_btn[2]))
    time.sleep(1)
    share_window = self.capture_screen()
    # Read Cords from the share window
    share_window_info = getShareWindowDetails(share_window, img_lib_path)
    return True, share_window_info


def scoutablesScan(self, item, controls, center_x, center_y, scan_list, img_lib_path):
    print("Found Souctable ", item['name'])
    return False, None


def bossScan(self, item, controls, center_x, center_y, scan_list, img_lib_path):
    # print("Found ", item['preview_name'])
    self.invokeDeviceConsole(f"Verifying {item['preview_name']} match")
    attack_options = self.capture_screen()
    attack_btn = img.get_template_coordinates(attack_options, cv2.imread(
        img_lib_path + 'monsters/boss_attack_option.png'))
    # Checking attack option is present or not, if not, skipping
    if attack_btn[0] is False:
        # print("No monster found. wrong match. skipping")
        self.invokeDeviceConsole("Wrong match found. Hence skipping")
        time.sleep(1)
        self.device_emu.shell(f'input tap ' + str(center_x) + ' ' + str(center_y + 25))
        return False, None
    self.invokeDeviceConsole("Boss monster match verified")
    self.device_emu.shell(f'input tap ' + str(attack_btn[1]) + ' ' + str(attack_btn[2]))
    time.sleep(1)
    attack_details = self.capture_screen()
    # Close attack description window button finding
    close_btn = img.get_template_coordinates(attack_details, cv2.imread(
        img_lib_path + 'monsters/close_attack_window.png'))
    # Confirm the monster level is correct based on the logic 2 & 3
    flag = True if item['logic'] == 1 else False
    monster = item if item['logic'] == 1 else {}
    if item['logic'] == 2 or item['logic'] == 3:
        levels = [monster for monster in scan_list if
                  monster['preview_name'] == item['preview_name']]
        for level in levels:
            level_img = cv2.imread(
                img_lib_path + 'monsters/level_' + str(level['level']) + '.png', 0)
            img_gray = cv2.cvtColor(attack_details, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(img_gray, level_img, cv2.TM_CCOEFF_NORMED)
            (_, maxVal, _, _) = cv2.minMaxLoc(result)
            if maxVal >= 0.95:
                flag = True
                monster = level
                break
    # Close the attack window
    self.device_emu.shell(
        f'input tap ' + str(close_btn[1]) + ' ' + str(close_btn[2]))
    time.sleep(1)
    # Skip if level is not found in the list
    if flag is False:
        # print("Level is not in the scan list")
        self.invokeDeviceConsole("The level is excluded in the list. Hence skipping")
        return False, None
    # When a level match is found,
    # print("Match Found: Lv ", monster['level'], " ", monster['name'])
    self.invokeDeviceConsole(f"Lv {str(monster['level'])} {monster['name']} found.")
    # Reselect the monster
    self.device_emu.shell(f'input tap ' + str(center_x) + ' ' + str(
        center_y + 0))  # +20 to avoid wrong clicks on some cases(get base area)
    time.sleep(1)
    # Open the share window to read the cords
    share_window = self.capture_screen()
    share_btn = img.get_template_coordinates(share_window, cv2.imread(
        img_lib_path + 'monsters/boss_share_option.png'))
    if not share_btn[0]:
        # Deselect the selection
        self.device_emu.shell(f'input tap ' + str(center_x) + ' ' + str(
            center_y + 0))  # +20 to avoid wrong clicks on some cases(get base area)
        return False, None
    # When share btn is present
    self.device_emu.shell(f'input tap ' + str(share_btn[1]) + ' ' + str(share_btn[2]))
    time.sleep(1)
    share_window = self.capture_screen()
    # Read Cords from the share window
    share_window_info = getShareWindowDetails(share_window, img_lib_path)
    # print(share_window_info) # (('639', '553'), (True, 120, 247), 33, 192)
    # print(share_window_info[0])
    return True, share_window_info


def hideMarch(self, img_lib_path):
    # print("hide march")
    hide_march_img = cv2.imread(img_lib_path + '/other/hide_march.png')
    unhide_march_img = cv2.imread(img_lib_path + '/other/unhide_march.png')
    src_img = self.capture_screen()
    if img.check_template_match(src_img, unhide_march_img):
        return True
    hide_march = img.get_template_coordinates(src_img, hide_march_img)
    if hide_march[0]:
        self.invokeDeviceConsole("Minimizing the march status bar")
        self.device_emu.shell(f'input tap ' + str(hide_march[1]) + ' ' + str(hide_march[2]))
        sleep(1)
        return True
    return False
