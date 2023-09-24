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


def navigateToAllianceWarWindow(self, img_lib_path):
    if self.is_running is False:
        return False
    # Importing templates
    pvp_war = cv2.imread(img_lib_path + '/join_rally/pvp_war.png')
    alliance_btn_template = cv2.imread(img_lib_path + '/join_rally/alliance_button.png')
    alliance_war_btn_template = cv2.imread(img_lib_path + '/join_rally/alliance_war_button.png')
    monster_war_checked_template = cv2.imread(img_lib_path + '/join_rally/monster_war_checked.png')
    # Check the current window is Alliance war
    src_img = self.capture_screen()
    # src_img = self.capture_screen()
    alliance_war_window = img.check_template_match(src_img, pvp_war)
    if alliance_war_window:
        # Already on Alliance War Window, Now check the monster war option is checked
        h, w = src_img.shape[:2]
        # Crop the ss by half on both height and width to get only the monster war checkbox area
        monster_war_checkbox_region = src_img[0:h // 2, 0:w // 2]
        if img.check_template_match(monster_war_checkbox_region, monster_war_checked_template):
            # Monster war option is checked. Now return to the call
            return True
        else:
            monster_war_unchecked_template = cv2.imread(img_lib_path + '/join_rally/monster_war_unchecked.png')
            monster_war_check = img.get_template_coordinates(monster_war_checkbox_region,
                                                             monster_war_unchecked_template)
            self.device_emu.shell(f'input tap ' + str(monster_war_check[1]) + ' ' + str(monster_war_check[2]))
            self.log = "Monster War option has been enabled"
            self.invokeDeviceConsole(self.log)
            sleep(1)
            return True
    # When alliance war window not found, it has to check for the alliance button and navigate to alliance war window
    alliance_btn = img.get_template_coordinates(src_img, alliance_btn_template)
    if alliance_btn[0] is False:
        # Alliance button missing, so going back to the previous window
        # print("Main alliance button missing")
        self.log = "Cannot Locate the Alliance button"
        self.invokeDeviceConsole(self.log)
        self.device_emu.shell('input keyevent KEYCODE_BACK')
        sleep(1)
        return False
    else:
        # Alliance button found
        # print("Main alliance button found")
        self.log = "Alliance button has been successfully located"
        self.invokeDeviceConsole(self.log)
        self.device_emu.shell(f'input tap ' + str(alliance_btn[1]) + ' ' + str(alliance_btn[2]))
        sleep(1)
        src_img = self.capture_screen()
        alliance_war_icon = img.get_template_coordinates(src_img, alliance_war_btn_template)
        if alliance_war_icon:
            self.device_emu.shell(f'input tap ' + str(alliance_war_icon[1]) + ' ' + str(alliance_war_icon[2]))
            sleep(1)
            return False


def findCordsOfRalliesToJoin(img_lib_path, src_img):
    # Importing Templates
    boss_monster_tag = cv2.imread(img_lib_path + '/join_rally/boss_monster_tag.png')

    result = cv2.matchTemplate(src_img, boss_monster_tag, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    # Convert the result to a binary image using thresholding
    binary_result = np.zeros_like(result, dtype=np.uint8)
    binary_result[result > threshold] = 255
    # Find the locations of matches above the threshold
    locations = cv2.findNonZero(binary_result)
    # to avoid matching same match, check the previous location
    prev_loc = None
    cords = []
    if locations is not None:
        for loc in locations:
            x, y = loc[0]
            # Check if current match is close to previous match
            if prev_loc is not None and np.linalg.norm(np.array([x, y]) - prev_loc) < \
                    boss_monster_tag.shape[0] / 2:
                continue
            # Match Found
            # print(f"Match found at ({x}, {y})")
            cords.append({'x': x, 'y': y})
            # Update previous match location
            prev_loc = np.array([x, y])
    return cords


def checkRallyState(self, img_lib_path, src_img, cords, device_res, checked_cords_img):
    monster_join_template = cv2.imread(img_lib_path + '/join_rally/join_button.png')
    # crop the portion to check the join button present or not
    base_size = [{"540": [int(device_res) - cords['x'], 125]},
                 {"1080": [int(device_res) - cords['x'], 235]}]
    base_dimension = next(
        item[device_res] for item in base_size if device_res in item)
    # cv2.rectangle(src_img, (cords['x'], cords['y']),(cords['x'] + base_dimension[0], cords['y'] + base_dimension[1]), 255, 2)
    crop_img = (
        src_img[cords['y']:cords['y'] + base_dimension[1], cords['x']: cords['x'] + base_dimension[0]].copy())
    # cv2.imwrite(r"C:\Users\91974\OneDrive\Documents\Project\Evony\images\evony\tmp\demo.png", crop_img)
    if img.check_template_match(crop_img, monster_join_template):
        # Check location images and return false if found in the list already
        for loc in checked_cords_img:
            if img.check_template_match(crop_img, loc):
                # print("The current rally has been checked already")
                return False
        return True
    else:
        return False


def getCordsLocImg(image, img_lib_path, checked_cords_img):
    location_icon = cv2.imread(img_lib_path + "/join_rally/location_icon.png")
    height, width = location_icon.shape[:-1]
    # Crop and retain the second half of the image
    image = image[:, image.shape[:-1][1] // 2:]
    loc_cords = img.get_template_match_coordinates(image, location_icon)
    if loc_cords[0]:
        loc_img = image[loc_cords[2]:loc_cords[2] + height, loc_cords[1]:loc_cords[1] + width + 1000]
        # cv2.imwrite(r"C:\Users\91974\OneDrive\Documents\Project\Evony\images\evony\tmp\loc.png", loc_img)
        checked_cords_img.append(loc_img)


def fetchRallyDetailsAndJoin(self, img_lib_path, device_res, controls, checked_cords_img):
    pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
    rally_power_icon = cv2.imread(img_lib_path + '/join_rally/rally_power_icon.png')
    boss_rally_flag = cv2.imread(img_lib_path + '/join_rally/boss_rally_flag.png')
    back_button = cv2.imread(img_lib_path + '/join_rally/back_button.png')
    join_alliance_war = cv2.imread(img_lib_path + '/join_rally/join_alliance_war.png')
    march_timer = cv2.imread(img_lib_path + '/join_rally/march_timer.png')
    stamina_confirm = cv2.imread(img_lib_path + '/join_rally/stamina_confirm.png')
    rally_info = self.capture_screen()
    # Verify Boss Rally is Active Or Not
    if img.check_template_match(rally_info, boss_rally_flag) is not True:
        return None
    # FETCH TIMER
    base_size = [{"540": [5, 60]}, {"1080": [10, 115]}]
    base_dimension = next(
        item[device_res] for item in base_size if device_res in item)
    time_img = img.get_template_coordinates(rally_info, rally_power_icon)
    if time_img[0]:
        timer_w, timer_h = rally_power_icon.shape[:-1]
        # cv2.rectangle(rally_info, (time_img[1], time_img[2] + timer_h + base_dimension[0]),(time_img[1] + (int(device_res) - time_img[1]),time_img[2] + base_dimension[1]), 255, 2)
        cropped_img = (rally_info[time_img[2] + timer_h + base_dimension[0]:time_img[2] + base_dimension[1],
                       time_img[1]:time_img[1] + (int(device_res) - time_img[1])].copy())
        # cv2.imwrite(r"C:\Users\91974\OneDrive\Documents\Project\Evony\images\evony\tmp\demo.png", cropped_img)
        thresh = cv2.threshold(cropped_img, 200, 255, cv2.THRESH_BINARY_INV)[1]
        join_timer = pytesseract.image_to_string(thresh).replace(" ", "").replace("\n", "")
        # print("Timer: ", join_timer)
        try:
            # Convert the time string to a timedelta object
            delta_timer = datetime.strptime(join_timer, '%H:%M:%S') - datetime(
                1900, 1, 1)
        except Exception as e:
            print(e)
            # print("Invalid time scanned")
            self.log = "The detected remaining time is not valid"
            self.invokeDeviceConsole(self.log)
            return False
        # Get a timedelta object representing 5 minutes
        minutes = timedelta(minutes=5)
        # Check if the time delta is less than 5 minutes
        if delta_timer < minutes:
            # print("Yeyy! Timer is less than 5 min")
            self.log = "The rally timer is less than 5 minutes"
            self.invokeDeviceConsole(self.log)
            monster_name_size = fetchMonsterRallyNameAndSize(rally_info, img_lib_path, device_res, time_img, timer_h,
                                                             base_dimension, controls, self, checked_cords_img)
            if monster_name_size is False:
                back_btn = img.get_template_coordinates(rally_info, back_button)
                if back_btn[0]:
                    self.device_emu.shell(f'input tap ' + str(back_btn[1]) + ' ' + str(back_btn[2]))
                    sleep(1)
                return False
            else:
                # Continue to next window, which is selecting preset and joining
                join_alliance_war_btn = img.get_template_coordinates(rally_info, join_alliance_war)
                if join_alliance_war_btn[0]:
                    self.device_emu.shell(
                        f'input tap ' + str(join_alliance_war_btn[1]) + ' ' + str(join_alliance_war_btn[2]))
                    sleep(1)
                    rally_info = self.capture_screen()
                    # cv2.imwrite(r'images/evony/tmp/item.png', rally_info)
                    # Selecting Preset
                    preset_status = selectPreset(img_lib_path, self)
                    if not preset_status:
                        # Incase, if the preset window is not opened, go back
                        back_btn = img.get_template_coordinates(rally_info, back_button)
                        if back_btn[0]:
                            self.device_emu.shell(f'input tap ' + str(back_btn[1]) + ' ' + str(back_btn[2]))
                            sleep(1)
                        return False
                    # Checking March Timer
                    march_join_timer = checkMarchTimer(self, img_lib_path, device_res)
                    if march_join_timer is False:
                        # it couldn't find a time, possibly due to the red color time text,so skip it
                        # print("Couldn't read time, possibly due to red text on the timer, hence skip")
                        self.log = "Couldn't read the time, likely due to red text on the timer; therefore, skipping the rally"
                        self.invokeDeviceConsole(self.log)
                        back_btn = img.get_template_coordinates(rally_info, back_button)
                        for i in range(2):
                            if back_btn[0]:
                                self.device_emu.shell(f'input tap ' + str(back_btn[1]) + ' ' + str(back_btn[2]))
                                sleep(1)
                        # Get Cords location img of the selected Boss(skip the bosses)
                        getCordsLocImg(rally_info.copy(), img_lib_path, checked_cords_img)
                        return False
                    total_join_timer = datetime.strptime(join_timer, "%H:%M:%S")
                    # print(total_join_timer)
                    print(march_join_timer)

                    if total_join_timer <= march_join_timer:
                        # print("The march time to join is more.hence skipping!")
                        self.log = "The march time required to join the rally exceeds the available time, hence skipping the rally"
                        self.invokeDeviceConsole(self.log)
                        back_btn = img.get_template_coordinates(rally_info, back_button)
                        for i in range(2):
                            if back_btn[0]:
                                self.device_emu.shell(f'input tap ' + str(back_btn[1]) + ' ' + str(back_btn[2]))
                                sleep(1)
                    else:
                        # Subtract extra_time from total_time
                        new_time = total_join_timer - march_join_timer
                        # print("Joining rally,The remaining time is:", str(new_time))
                        # Join rally
                        march_timer_btn = img.get_template_coordinates(rally_info, march_timer)
                        self.device_emu.shell(f'input tap ' + str(march_timer_btn[1]) + ' ' + str(march_timer_btn[2]))
                        sleep(1)
                        # Check whether stamina refill prompt is visible or not
                        rally_info = self.capture_screen()
                        stamina = img.get_template_coordinates(rally_info, stamina_confirm)
                        if stamina[0]:
                            # print("Auto use stamina: ", self.args['auto_use_stamina'])
                            self.invokeDeviceConsole("Not enough stamina to join the rally")
                            if not self.args['auto_use_stamina']:
                                # print("Auto use stamina option is not selected. hence skipping")
                                self.invokeDeviceConsole("Auto use stamina option is not selected, therefore skipping the rally")
                                for i in range(3):
                                    self.device_emu.shell('input keyevent KEYCODE_BACK')
                                    sleep(1)
                                return False
                            start_time = time.time()
                            # print("Need stamina")
                            self.invokeDeviceConsole("Stamina will be automatically refilled to continue")
                            self.device_emu.shell(f'input tap ' + str(stamina[1]) + ' ' + str(stamina[2]))
                            sleep(1)
                            stamina_status = refillStamina(self, img_lib_path)
                            if not stamina_status:
                                # print("Probably no stamina found")
                                self.invokeDeviceConsole("No available stamina found")
                                for i in range(2):
                                    self.device_emu.shell('input keyevent KEYCODE_BACK')
                                    sleep(1)
                                return False
                            end_time = time.time()
                            time_diff = end_time - start_time
                            # Adding the extra time taken to use stamina to the march_join_timer
                            # print("Total Time: ", total_join_timer)
                            extra_join_timer = datetime.strptime(g_util.convertSecondToTimeFormat(round(time_diff)),
                                                                 "%H:%M:%S")
                            total_join_timer = datetime.strptime(str(total_join_timer - extra_join_timer), "%H:%M:%S")
                            # print("New Total time: ", total_join_timer)
                            if total_join_timer <= march_join_timer:
                                # print("The march time to join is more.hence skipping!")
                                self.log = "The march time required to join the rally exceeds the available time, hence skipping the rally"
                                self.invokeDeviceConsole(self.log)
                                back_btn = img.get_template_coordinates(rally_info, back_button)
                                for i in range(2):
                                    if back_btn[0]:
                                        self.device_emu.shell(f'input tap ' + str(back_btn[1]) + ' ' + str(back_btn[2]))
                                        sleep(1)
                                # Get Cords location img of the selected Boss(skip the bosses)
                                getCordsLocImg(rally_info.copy(), img_lib_path, checked_cords_img)
                                return False
                            else:
                                # print("perfect ok")
                                march_timer_btn = img.get_template_coordinates(rally_info, march_timer)
                                self.device_emu.shell(
                                    f'input tap ' + str(march_timer_btn[1]) + ' ' + str(march_timer_btn[2]))
                                # print("Joined the rally")
                                self.log = "Joining the rally"
                                self.invokeDeviceConsole(self.log)
                                sleep(1)
                        else:
                            # print("Joined the rally, Remaining time: " + str(new_time))
                            self.log = "Joining the rally"
                            self.invokeDeviceConsole(self.log)
        else:
            # print("Skip rallies cuz time is more than 5 min")
            self.log = "The rally timer is more than 5 minutes, hence skipping the rally"
            self.invokeDeviceConsole(self.log)
            back_btn = img.get_template_coordinates(rally_info, back_button)
            if back_btn[0]:
                self.device_emu.shell(f'input tap ' + str(back_btn[1]) + ' ' + str(back_btn[2]))
                sleep(1)
            # Get Cords location img of the selected Boss(skip the bosses)
            getCordsLocImg(rally_info.copy(), img_lib_path, checked_cords_img)
            return False
    else:
        return False


def fetchMonsterRallyNameAndSize(rally_info, img_lib_path, device_res, time_img, timer_h, base_dimension, controls,
                                 self, checked_cords_img):
    monster_power_icon = cv2.imread(img_lib_path + '/join_rally/monster_power_icon.png')
    pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
    # CHECK MONSTER NAME
    # cv2.rectangle(rally_info, (time_img_template[1],0), (time_img_template[1]+(int(device_res)-time_img_template[1]), time_img_template[2]+h+base_dimension[0]), 255, 2)
    cropped_img = (rally_info[base_dimension[1]:int((time_img[2] + timer_h + base_dimension[0]) / 1.2),
                   int(time_img[1] * 2.2):time_img[1] + (int(device_res) - time_img[1])].copy())
    # cv2.imwrite(r'images/evony/tmp/item1.png', cropped_img)
    # Yellow text to black and rest to white
    # Convert the image to HSV color space
    hsv = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2HSV)

    # Define the lower and upper thresholds for the yellow color
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])

    # Create a mask for the yellow color
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Replace the yellow color with black
    result = cv2.bitwise_and(cropped_img, cropped_img, mask=mask)
    result[mask > 0] = (0, 0, 0)

    # Replace the remaining pixels with white
    result[mask == 0] = (255, 255, 255)

    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)

    # cv2.imwrite(r"C:\Users\91974\OneDrive\Documents\Project\Evony\images\evony\tmp\demo.png", gray)
    monster_info_text = pytesseract.image_to_string(gray, config='--psm 6').replace(" ", "").replace("\n", "").lower()
    pattern = re.compile(r'[^a-zA-Z0-9\s]+')
    monster_info_text = re.sub(pattern, '', monster_info_text)
    # print("Text Reading from screen: ", monster_info_text)
    # Fetching all the monsters names from DB
    conn = dbUtils.create_connection("main.db")
    all_monsters_list = dbUtils.select_query_no_param(conn,
                                                      get_all_monster_names)
    # Checking the monster is in the list or not
    for monster in all_monsters_list:
        # Verifying the monster name is present in the converted text
        monster_flag = True
        for monster_words in monster[0].split():
            monster_words = re.sub(pattern, '', monster_words).lower()
            if monster_words not in monster_info_text:
                monster_flag = False
                break
        if monster_flag is False:
            continue

        # Check monster is present in the selected list
        monster_matches = [selected_monster for selected_monster in controls['monsters'] if
                           selected_monster['name'] == monster[0]]
        if not monster_matches:
            # print(monster[0], " is not in selected list.skipping")
            self.log = monster[0] + " is not in the selection list, hence skipping the rally"
            self.invokeDeviceConsole(self.log)
            # Get Cords location img of the selected Boss(skip the bosses)
            getCordsLocImg(rally_info.copy(), img_lib_path, checked_cords_img)
            return False
        # Check And Verify the Level based on logics declared
        if monster_matches[0]['logic'] == 3:
            result = cv2.matchTemplate(cropped_img, monster_power_icon, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            # Calculate the coordinates of the other three corners of the rectangle using the width and height of the template image
            w, h = monster_power_icon.shape[:-1]
            top_left = max_loc
            bottom_right = (cropped_img.shape[1] + w, top_left[1] + h)
            # Draw a rectangle around the matched region using the calculated corner coordinates
            # cv2.rectangle(cropped_img, top_left, bottom_right, (0, 255, 0), 2)
            roi = (cropped_img[top_left[1]:bottom_right[1], top_left[0] + h:bottom_right[0]].copy())
            boss_size = pytesseract.image_to_string(roi).replace("\n", "").replace(" ", "")
            # print("Size:: ", boss_size)
            for monster_info in monster_matches:
                # print("Monster info", monster_info)
                if monster_info['size'].lower() in boss_size.lower():
                    # print("Size found", monster_info['size'])
                    self.log = "Lv" + str(monster_info['level']) + " " + monster_info[
                        'name'] + " is found in the selection list"
                    self.invokeDeviceConsole(self.log)
                    return True
            # print(monster_info['name'] + " level is skipped in the selection")
            self.log = monster_info['name'] + " level is skipped in the selection list"
            self.invokeDeviceConsole(self.log)
            # Get Cords location img of the selected Boss(skip the bosses)
            getCordsLocImg(rally_info.copy(), img_lib_path, checked_cords_img)
            return False
        # it is certain that if the len is not 0, and it skips the logic 3 functionality, value found
        if len(monster_matches) != 0:
            self.log = monster[0] + " is found in the selection list"
            self.invokeDeviceConsole(self.log)
            return True
    # At this point, it is certain that monster name isnt in the all_monsters list
    # Get Cords location img of the selected Boss(skip the bosses)
    getCordsLocImg(rally_info.copy(), img_lib_path, checked_cords_img)
    return False


def selectPreset(img_lib_path, self):
    confirm_preset_window = cv2.imread(img_lib_path + '/join_rally/preset_window.png')
    src_img = self.capture_screen()
    # Confirm the Preset Selection Window
    if img.check_template_match(src_img, confirm_preset_window) is False:
        return False
    # GET THE PRESET IMAGES FOR THE PRESET COUNTER
    if 'current_preset' not in self.args:
        self.args['current_preset'] = 1
    if findPreset(self, src_img, img_lib_path):
        # CHECK ATTEMPT PRESET WITH GENERAL
        if self.args['attempt_preset_with_general']:
            if attemptPresetWithGeneral(self, img_lib_path):
                # print("attempt preset successful")
                self.log = "Attempt preset with general was successful"
                self.invokeDeviceConsole(self.log)
            else:
                self.log = "Attempt preset with general failed"
                self.invokeDeviceConsole(self.log)
        # Update Next Preset Value
        # print("Current Preset: ", self.args['current_preset'])
        self.args['current_preset'] += 1
        if self.args['current_preset'] == self.args['rotate_preset'] + 1:
            self.args['current_preset'] = 1
        # print("Next Preset: ", self.args['current_preset'])
        return True
    else:
        # When No preset match is found, it means preset is locked, so reset the preset turn to 1
        # print("Preset Locked, resetting to preset 1")
        self.log = "Preset " + str(self.args['current_preset']) + " is locked, resetting to Preset 1"
        self.invokeDeviceConsole(self.log)
        self.args['current_preset'] = 1
        if findPreset(self, src_img, img_lib_path):
            # Update Next Preset Value
            self.args['current_preset'] += 1
            if self.args['current_preset'] == self.args['rotate_preset'] + 1:
                self.args['current_preset'] = 1
            return True
    return False


def checkPresetWithGeneral(self, template):
    src_img = self.capture_screen()
    if not img.check_template_match(src_img, template):
        return True
    else:
        # print("Preset with general not found")
        return False


def attemptPresetWithGeneral(self, img_lib_path):
    preset_with_no_main_general_template = cv2.imread(img_lib_path + '/join_rally/preset_with_no_main_general.png')
    tmp_current_preset = self.args['current_preset']
    while True:
        # Check Preset for general
        if checkPresetWithGeneral(self, preset_with_no_main_general_template):
            return True
        # When no Preset with general found, Find preset in the loop
        # Update next preset value and check for general in the presets
        self.args['current_preset'] += 1
        if self.args['current_preset'] == self.args['rotate_preset'] + 1:
            self.args['current_preset'] = 1
        src_img = self.capture_screen()
        if not findPreset(self, src_img, img_lib_path):
            # When No preset match is found, it means preset is locked, so reset the preset turn to 1
            # print("Preset Locked, resetting to preset 1(attempt preset with general)")
            self.log = "Preset " + str(self.args['current_preset']) + " is locked, resetting to Preset 1"
            self.invokeDeviceConsole(self.log)
            self.args['current_preset'] = 1
            if findPreset(self, src_img, img_lib_path):
                if checkPresetWithGeneral(self, preset_with_no_main_general_template):
                    return True
                else:
                    return False
        if tmp_current_preset == self.args['current_preset']:
            # print("TMP: ", tmp_current_preset, " Current Preset: ", self.args['current_preset'])
            print("No general found in the preset loop")
            self.log = "No general is found in the preset loop"
            self.invokeDeviceConsole(self.log)
            # Verify again whether general is available
            if checkPresetWithGeneral(self, preset_with_no_main_general_template):
                return True
            else:
                return False


def findPreset(self, src_img, img_lib_path):
    dir_path = img_lib_path + '/presets'
    files = os.listdir(dir_path)
    preset_templates = [f for f in files if str(self.args['current_preset']) in f]
    for preset in preset_templates:
        # print(preset)
        tmp_preset = cv2.imread(img_lib_path + '/presets/' + preset)
        preset_match = img.get_template_coordinates(src_img, tmp_preset)
        if preset_match[0]:
            self.device_emu.shell(f'input tap ' + str(preset_match[1]) + ' ' + str(preset_match[2]))
            # print("Preset Found ", preset)
            sleep(1)
            return True
    return False


def checkMarchTimer(self, img_lib_path, device_res):
    rally_info = self.capture_screen()
    march_timer = cv2.imread(img_lib_path + '/join_rally/march_timer.png')
    # cv2.imwrite(r'images/evony/tmp/item1.png', rally_info)
    # Check for the time taking to join the rally after selecting preset
    alliance_war_window = cv2.matchTemplate(rally_info, march_timer, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(alliance_war_window)

    # Calculate the coordinates of the other three corners of the rectangle using the width and height of the template image
    timer_w, timer_h = march_timer.shape[:-1]
    base_size = [{"540": 10}, {"1080": 15}]
    base_dimension = next(item[device_res] for item in base_size if device_res in item)
    top_left = max_loc
    bottom_right = (rally_info.shape[1] + timer_w, top_left[1] + timer_h + base_dimension)
    roi = (rally_info[top_left[1]:bottom_right[1], top_left[0] + timer_h:bottom_right[0]].copy())
    gray_image = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    timer_img = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)[1]
    join_march_timer = pytesseract.image_to_string(timer_img, config='--psm 6').replace(" ", "").replace("\n", "")
    try:
        march_join_timer = datetime.strptime(join_march_timer, "%H:%M:%S")
    except Exception as e:
        print(e)
        return False
    return march_join_timer


def refillStamina(self, img_lib_path):
    if self.is_running is False:
        return False
    stamina_packs = [{'quantity': 100, 'path': img_lib_path + 'join_rally/stamina_100.png'},
                     {'quantity': 50, 'path': img_lib_path + 'join_rally/stamina_50.png'},
                     {'quantity': 25, 'path': img_lib_path + 'join_rally/stamina_25.png'},
                     {'quantity': 10, 'path': img_lib_path + 'join_rally/stamina_10.png'}]

    stamina_use = cv2.imread(img_lib_path + 'join_rally/stamina_use.png')
    confirm_use = cv2.imread(img_lib_path + 'join_rally/confirm_use.png')
    back_button = cv2.imread(img_lib_path + 'join_rally/back_button.png')
    self.device_emu.shell(f'input swipe 250 810 250 520 1500')
    sleep(1)
    src_img = self.capture_screen()

    # Loop the stamina list
    for stamina in stamina_packs:
        if self.is_running is False:
            return False
        # print(stamina['quantity'], " ", stamina['path'])
        stamina_img = cv2.imread(stamina['path'])
        # TODO Pack check is not accurate(eg, pack 25 is matching to pack 10)
        # print(stamina['quantity'])
        if img.check_template_match(src_img, stamina_img) is False:
            # print(stamina['quantity'], "Pack not found")
            self.log = "Stamina "+str(stamina['quantity'])+"VIT not found"
            self.invokeDeviceConsole(self.log)
            continue
        result = cv2.matchTemplate(src_img, stamina_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        top_left = max_loc
        bottom_right = (top_left[0] + src_img.shape[0], top_left[1] + stamina_img.shape[1])
        roi = (src_img[top_left[1]:bottom_right[1], 0:bottom_right[0]].copy())
        # Cropping roi to get the second half to eliminate text "use" in the description
        roi_h, roi_w = roi.shape[:2]
        roi = roi[0:roi_h, roi_w // 2:roi_w]
        apply_stamina = img.get_template_coordinates(roi, stamina_use)
        if not apply_stamina[0]:
            # print(f"Stamina {stamina['quantity']} is empty")
            self.log = "Stamina " + str(stamina['quantity']) + "is empty"
            self.invokeDeviceConsole(self.log)
            continue
        self.device_emu.shell(
            f'input tap ' + str((roi_w / 2) + apply_stamina[1]) + ' ' + str(apply_stamina[2] + top_left[1]))
        sleep(1)
        src_img = self.capture_screen()
        # Setting minimum stamina selection
        if stamina['quantity'] < 50:
            minimum_times = 50 / stamina['quantity']
            add_stamina_btn = cv2.imread(img_lib_path + '/join_rally/stamina_add.png')
            # Cropping src_img to get the second half to find the stamina add button(to avoid match with minus button)
            crop_h, crop_w = src_img.shape[:2]
            crop_src_img = src_img[0:crop_h, crop_w // 2:crop_w]
            add_stamina = img.get_template_coordinates(crop_src_img, add_stamina_btn)
            # cv2.imwrite(r'images/evony/tmp/item1.png', src_img)
            # print(f"ADD STAMINA ", add_stamina[0])
            for i in range(int(minimum_times) - 1):
                self.device_emu.shell(f'input tap ' + str((crop_w / 2) + add_stamina[1]) + ' ' + str(add_stamina[2]))
                sleep(1)
        confirm_stamina = img.get_template_coordinates(src_img, confirm_use)
        if confirm_stamina[0]:
            self.device_emu.shell(f'input tap ' + str(confirm_stamina[1]) + ' ' + str(confirm_stamina[2]))
            sleep(1)
            self.device_emu.shell('input keyevent KEYCODE_BACK')
            sleep(1)
            return True
    # If execution reaches this line, it means no stamina found/used
    self.log = "No Stamina Found"
    self.invokeDeviceConsole(self.log)
    return False
