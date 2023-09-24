#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import time
from time import sleep
from datetime import datetime, timedelta

import requests
from PyQt5.QtCore import pyqtSignal, QThread, QTimer, QTime
from ppadb.client import Client as AdbClient
import sys
import os
import numpy as np
import cv2
from modules import ImageRecognitionUtils as img
from .Cultivate import Cultivate
from .Query import *
from modules import DatabaseUtils as dbUtils
from modules import BuildingsLocator as build_loc
from modules import GeneralUtils as general_utils
from modules import JoinRally as rally
from modules import WorldMapScan as wm_scan
import pytesseract
import random
import pytz  # Import the pytz library to work with timezones
import subprocess

img_lib_path = None
device_res = None


class ConfigurationThread(QThread):
    start_stop_button_switch = pyqtSignal(int)
    switch_run = pyqtSignal(int)
    emulator_console = pyqtSignal(str, str)
    device_console = pyqtSignal(int, str, str)
    update_training_table = pyqtSignal(int, int)

    def __init__(self, parent=None, index=0,
                 config={"emulator_port": None, "emulator_name": None, "emulator_control": None}):
        super(ConfigurationThread, self).__init__(parent)
        self.index = index
        self.emulator_name = config["emulator_name"]
        self.emulator_port = config["emulator_port"]
        self.emulator_control = config["emulator_control"]
        self.device_emu = None
        self.log = None
        self.is_running = True
        self.args = {}
        self.expiry_date = datetime(2024, 1, 1, tzinfo=pytz.UTC)
        self.adb_path = general_utils.getPathADB() + "\\adb.exe"

    def quit(self):
        self.is_running = False
        self.start_stop_button_switch.emit(self.index)

    def run(self):
        print("Starting Thread...", self.index)
        if self.index == 0:
            # INIT ADB SERVER
            self.log = "Initiating ADB Server"
            self.invokeEmulatorConsole(self.log)
            # START  ADB SERVER
            # ///////////////////////////////////////////////////////////////
            os.system(f"{self.adb_path} kill-server")
            os.system(f"{self.adb_path} start-server")
        else:
            self.initDevice()

    def capture_screen(self, kick_timer=True, ads=False, game_settings=True):
        src_img = cv2.imdecode(np.frombuffer(self.device_emu.screencap(), np.uint8), cv2.IMREAD_COLOR)
        restart_img = cv2.imread(img_lib_path + "other/restart.png")
        world_map_btn = cv2.imread(img_lib_path + "other/world_map_return_btn.png")
        if kick_timer and img.check_template_match(src_img, restart_img):
            print("kick timer activated")
            self.invokeDeviceConsole(
                "Kick timer activated for " + self.emulator_control['game_settings']['kick_timer'] + " mins")
            time.sleep(self.emulator_control['game_settings']['kick_timer'] * 60)
            # time.sleep(10)
            # print("kick timer done")
            self.invokeDeviceConsole("Kick timer done. Restart initiated")
            # Restart the game
            restart = img.get_template_coordinates(src_img, restart_img)
            if restart[0]:
                self.device_emu.shell(f'input tap ' + str(restart[1]) + ' ' + str(restart[2]))
                sleep(5)
                src_img = cv2.imdecode(np.frombuffer(self.device_emu.screencap(), np.uint8), cv2.IMREAD_COLOR)
                while not img.check_template_match(src_img, world_map_btn):
                    # print("Still loading")
                    src_img = cv2.imdecode(np.frombuffer(self.device_emu.screencap(), np.uint8), cv2.IMREAD_COLOR)
            # emit twice to restart
            self.switch_run.emit(self.index)
            self.switch_run.emit(self.index)
        if ads:
            for i in range(5):
                ads_img = cv2.imread(img_lib_path + "other/x" + str(i + 1) + ".png")
                if img.check_template_match(src_img, ads_img):
                    # print("Ads found")
                    self.invokeDeviceConsole("Closing the ads")
                    ads_match = img.get_template_coordinates(src_img, ads_img)
                    self.device_emu.shell(f'input tap ' + str(ads_match[1]) + ' ' + str(ads_match[2]))
                    time.sleep(1)
                    break
        if game_settings:
            # Check add break option
            if self.emulator_control['game_settings']['add_break']['add_break']:
                # When break timer is enabled
                break_time = self.emulator_control['game_settings']['add_break']['value']
                current_time = QTime.currentTime()
                if break_time['from'] <= current_time <= break_time['to']:
                    # print("It's break time!")
                    # print(current_time.secsTo(break_time['to']))
                    self.invokeDeviceConsole(f"Going for a break until {break_time['to'].toString('hh:mm')}")
                    self.launchEvony(False)
                    sleep(current_time.secsTo(break_time['to']))
                    self.invokeDeviceConsole("Resuming the game after the break.")
                    self.launchEvony(True)
                    # TODO make sure it bypassed the update window on loading screen
        return src_img

    def invokeEmulatorConsole(self, log):
        self.log = log
        self.emulator_console.emit(self.log, self.emulator_name)
        sleep(0.1)

    def invokeDeviceConsole(self, log):
        self.log = log
        self.device_console.emit(self.index, self.log, self.emulator_name)
        sleep(0.1)

    def emulatorExec(self):
        try:
            if self.emulator_control['mode'] == "Join Rally":
                while self.is_running:
                    self.args = {}
                    self.runJoinRally(10)
            elif self.emulator_control['mode'] == "Rally Setter":
                print("inside rally setter")
            elif self.emulator_control['mode'] == "More Activities":
                controls = self.emulator_control['custom_tasks']
                if controls['task'] == 'cultivate':
                    self.cultivateGeneral(controls['settings'])
                elif controls['task'] == 'wof':
                    self.wheelOfFortune(controls['settings'])
                self.switch_run.emit(self.index)
            elif self.emulator_control['mode'] == "World Map Scan":
                self.runWorldMapScan()
            elif self.emulator_control['mode'] == "Patrol":
                self.runPatrol()
            elif self.emulator_control['mode'] == "Black Market":
                self.runBlackMarket()
            elif self.emulator_control['mode'] == "Troop Training":
                self.runTroopTraining()

        except Exception as e:
            print(e)

    def wheelOfFortune(self, settings):
        wof_window = cv2.imread(img_lib_path + "more_activities/wof_window.png")
        wof_congrats_screen = cv2.imread(img_lib_path + "more_activities/wof_congrats.png")
        wof_purchase_chips = cv2.imread(img_lib_path + "more_activities/wof_purchase_chips.png")
        use_chips = cv2.imread(img_lib_path + "more_activities/wof_use_chips.png")
        apply_chips = cv2.imread(img_lib_path + "more_activities/wof_use.png")
        max_chips = cv2.imread(img_lib_path + "more_activities/wof_max.png")
        add_chips = cv2.imread(img_lib_path + "more_activities/wof_add_chips.png")
        # print(settings)  # {'100': 2, '10': 1, '1': 2}

        # Verify cultivate window is open
        src_img = self.capture_screen()
        if not img.check_template_match(src_img, wof_window):
            # print("Wrong window")
            self.invokeDeviceConsole("Wrong Window opened. Exiting the from the bot")
            return False
        # Add chips
        self.invokeDeviceConsole("Adding Chips to the Wheel of Fortune")
        add_chips_btn = img.get_template_coordinates(src_img, add_chips)
        if add_chips_btn[0]:
            self.device_emu.shell(f'input tap ' + str(add_chips_btn[1]) + ' ' + str(add_chips_btn[2]))
            sleep(1)
            src_img = self.capture_screen()
            # Use all the chips
            while img.check_template_match(src_img, use_chips):
                # print("Chip found")
                add_chips = img.get_template_coordinates(src_img, use_chips)
                self.device_emu.shell(f'input tap ' + str(add_chips[1]) + ' ' + str(add_chips[2]))
                sleep(1)
                src_img = self.capture_screen()
                use_max_chips = img.get_template_coordinates(src_img, max_chips)
                self.device_emu.shell(
                    f'input tap ' + str(use_max_chips[1]) + ' ' + str(use_max_chips[2]))
                confirm_chips = img.get_template_coordinates(src_img, apply_chips)
                self.device_emu.shell(
                    f'input tap ' + str(confirm_chips[1]) + ' ' + str(confirm_chips[2]))
                sleep(5)
                src_img = self.capture_screen()
            self.device_emu.shell('input keyevent KEYCODE_BACK')
            time.sleep(1)

        for spin_ctrl in settings:
            if settings[spin_ctrl] != 0:
                tmp_img = cv2.imread(img_lib_path + "more_activities/wof_spin_" + spin_ctrl + ".png")
                i = 0
                while i < settings[spin_ctrl]:
                    src_img = self.capture_screen()
                    # Verify cultivate window is open
                    if not img.check_template_match(src_img, wof_window):
                        # print("Wrong window")
                        self.invokeDeviceConsole("Wrong Window opened. Exiting the from the bot")
                        return False

                    spin = img.get_template_coordinates(src_img, tmp_img)
                    if spin[0]:
                        self.device_emu.shell(f'input tap ' + str(spin[1]) + ' ' + str(spin[2]))
                        time.sleep(1)
                        # print("spin pressed ", spin_ctrl)
                        self.invokeDeviceConsole(
                            f"Spinning {'Once' if int(spin_ctrl) == 1 else ('10 Times' if int(spin_ctrl) == 10 else '100 Times')}")
                        # when add chips window pop up, skip the rest
                        src_img = self.capture_screen()
                        if img.check_template_match(src_img, wof_purchase_chips):
                            # print("Not enough chips to purchase")
                            self.invokeDeviceConsole(
                                f"Not enough chips for spin {'Once' if int(spin_ctrl) == 1 else ('10 Times' if int(spin_ctrl) == 10 else '100 Times')}")
                            self.device_emu.shell('input keyevent KEYCODE_BACK')
                            time.sleep(1)
                            break
                        if int(spin_ctrl) != 1:
                            while not (img.check_template_match(src_img, wof_congrats_screen)):
                                src_img = self.capture_screen()
                            # print("back pressed")
                            self.device_emu.shell('input keyevent KEYCODE_BACK')
                            time.sleep(1)
                        else:
                            time.sleep(4)
                    else:
                        self.invokeDeviceConsole(
                            f"Not enough chips for spin {'Once' if int(spin_ctrl) == 1 else ('10 Times' if int(spin_ctrl) == 10 else '100 Times')}")
                        break
                    i += 1

    def cultivateGeneral(self, settings):
        gold_cultivate = cv2.imread(img_lib_path + "more_activities/gold_cultivate.png")
        confirm_cultivate = cv2.imread(img_lib_path + "more_activities/confirm_cultivate.png")
        cancel_cultivate = cv2.imread(img_lib_path + "more_activities/cancel_cultivate.png")
        # Verify cultivate window is open
        src_img = self.capture_screen()
        if not img.check_template_match(src_img, gold_cultivate):
            # print("Wrong window")
            self.invokeDeviceConsole("Wrong window")
            return False
        while True:
            cultivate = img.get_template_coordinates(src_img, gold_cultivate)
            if cultivate[0]:
                self.device_emu.shell(f'input tap ' + str(cultivate[1]) + ' ' + str(cultivate[2]))
                time.sleep(1)
                src_img = self.capture_screen()
                if img.check_template_match(src_img, gold_cultivate):
                    # Screen didn't changed, hence skip the rest of the code
                    # TODO too many attempts(lag wifi icon), stop the program
                    continue
            # Verify cultivate button is pressed
            if not img.check_template_match(src_img, confirm_cultivate):
                continue
            src_img = self.capture_screen()
            cultivate = Cultivate(src_img, settings, img_lib_path)
            # print(cultivate.attributes)
            # Stop the program when any of the value reaches 290
            if any(value.get('org_value', 0) > 290 for value in self.attributes.values()):
                self.invokeDeviceConsole("One of the attribute value reaches 290. Hence Stopping.")
                return True

            # Validate conditions and press Confirm/Cancel
            if cultivate.validateAttributes():
                confirm = img.get_template_coordinates(src_img, confirm_cultivate)
                if confirm[0]:
                    self.device_emu.shell(f'input tap ' + str(confirm[1]) + ' ' + str(confirm[2]))
                    self.invokeDeviceConsole("Confirming the cultivation")
                    sleep(1)
            else:
                cancel = img.get_template_coordinates(src_img, cancel_cultivate)
                if cancel[0]:
                    self.device_emu.shell(f'input tap ' + str(cancel[1]) + ' ' + str(cancel[2]))
                    self.invokeDeviceConsole("Skipping the cultivation")
                    sleep(1)
            src_img = self.capture_screen()

    def runWorldMapScan(self):
        global img_lib_path
        global device_res
        controls = self.emulator_control['world_map_scan']
        # print(controls)
        scan_list = []
        # When Boss Scan is enabled
        if controls['enable_boss_scan']:
            for monster in controls['boss_scan']['monsters']:
                # print("Monster :::::::", monster)
                monster['type'] = 'boss_scan'
                monster['img'] = cv2.imread(img_lib_path + "monsters/" + monster['img_' + device_res + 'p'])
            scan_list.extend(controls['boss_scan']['monsters'])
        # When Normal monster Scan is enabled
        if controls['enable_monster_scan']:
            for monster in controls['monster_scan']['monsters']:
                # print("Monster :::::::", monster)
                monster['type'] = 'monster_scan'
                monster['img'] = cv2.imread(img_lib_path + "normal_monsters/" + monster['img_' + device_res + 'p'])
            scan_list.extend(controls['monster_scan']['monsters'])
        # When Scoutables Scan is enabled
        if controls['enable_scoutables_scan']:
            for scout in controls['scoutables_scan']['scoutables']:
                # print("Monster :::::::", monster)
                scout['type'] = 'scoutables_scan'
                scout['img'] = cv2.imread(img_lib_path + "scoutables/" + scout['img_' + device_res + 'p'])
            scan_list.extend(controls['scoutables_scan']['scoutables'])

        # TODO :: CHECK ENABLE FOR OTHER TYPES AND COPY IT IN THE SCAN_LIST & Capture other functionalities
        if controls['enable_tile_scan']:
            print("Copy tile scan list")
        # print(scan_list)
        if not wm_scan.locateWorldMap(self, img_lib_path):
            # Stop World Map Scan when it is failed to locate
            self.is_running = False
            self.invokeDeviceConsole("The scan has been stopped as the world map could not be located.")
        # Hide Marches bar if visible
        wm_scan.hideMarch(self, img_lib_path)
        # Attempt custom location when the condition is met
        wm_scan.attemptCustomCords(self, img_lib_path, controls['custom_cords'])
        current_direction = random.randint(1, 4)
        # Loop Begins here
        swipe_flag = False
        while self.is_running:
            wm_scan.locateWorldMap(self, img_lib_path)
            # Random to swipe the map
            random_number = random.randint(1, 7)
            # print("Random Number ", random_number)
            # Swipe Pattern
            swipe_coordinates = {1: '380 400 60 600', 2: '60 400 360 600', 3: '120 600 440 400', 4: '360 600 60 400'}
            # Valid direction to avoid getting the reverse swipe
            valid_directions = [i for i in range(1, 5) if i != current_direction and (i % 2) != (current_direction % 2)]
            # print("Valid Directions ", valid_directions)
            # Choose a random direction from the list of valid directions
            swipe_direction = random.choice(valid_directions)
            # print("Swipe Direction ", swipe_direction)
            # Update current direction
            current_direction = swipe_direction
            for times in range(random_number):
                # Swipe flag to skip the first swipe to capture the current screen
                if swipe_flag:
                    self.device_emu.shell(f'input swipe ' + swipe_coordinates[swipe_direction] + ' 1000')
                else:
                    swipe_flag = True
                time.sleep(1)
                src_img = self.capture_screen()
                # print("Screen shot done")
                # Scanning the SS with the selected items,if location moved on click, redo it the scan map once again
                scan_map = wm_scan.scanMapSS(self, scan_list, src_img, controls, img_lib_path, None)
                if not scan_map[0]:
                    src_img = self.capture_screen()
                    wm_scan.scanMapSS(self, scan_list, src_img, controls, img_lib_path, scan_map[1])

    def runBlackMarket(self):
        global device_res
        black_market_items = self.emulator_control['black_market']
        # print(black_market_items)
        # Adjust the base crop size based on the screen resolution
        base_size = [{"540": [110, 50]}, {"1080": [205, 105]}]
        base_dimension = next(item for item in base_size if device_res in item)
        # print(base_dimension[device_res])
        src_img = self.capture_screen()
        black_market_template = cv2.imread(img_lib_path + 'black_market/blackmarket.png')
        if img.check_template_match(src_img, black_market_template):
            # print("Inside Black Market")
            # Load templates
            for item in black_market_items['items']:
                item['image'] = cv2.imread(img_lib_path + 'black_market/' + item['file_name'])
            # print(black_market_items)
            rss_buy_templates = []
            rss_buy_list = [img_lib_path + 'black_market/food.png', img_lib_path + 'black_market/wood.png',
                            img_lib_path + 'black_market/stone.png', img_lib_path + 'black_market/iron.png']
            for img_path in rss_buy_list:
                rss_buy_templates.append(cv2.imread(img_path))
            gold_buy_template = cv2.imread(img_lib_path + 'black_market/gold.png')
            gem_buy_template = cv2.imread(img_lib_path + 'black_market/gem.png')
            base_template = cv2.imread(img_lib_path + 'black_market/base.png')
            confirm_buy = cv2.imread(img_lib_path + 'black_market/confirm.png')
            free_refresh = cv2.imread(img_lib_path + 'black_market/instant_refresh.png')
            gem_refresh = cv2.imread(img_lib_path + 'black_market/instant_refresh_gems.png')
            try:
                refresh_times = black_market_items['refresh_times']
                # print("Refresh times ", refresh_times)
                while refresh_times > 0:
                    time.sleep(1)
                    src_img = self.capture_screen()
                    res = cv2.matchTemplate(src_img, base_template, cv2.TM_CCOEFF_NORMED)
                    threshold = 0.8
                    loc = np.where(res >= threshold)
                    w, h = base_template.shape[:-1]
                    img_copy = src_img.copy()
                    prev_matches = []
                    # Looping through items
                    # tmp_item = 0
                    for pt in zip(*loc[::-1]):
                        too_close = False
                        # Skipping double matches
                        for prev_pt in prev_matches:
                            if abs(pt[0] - prev_pt[0]) < h and abs(pt[1] - prev_pt[1]) < w:
                                too_close = True
                                break
                        # Match found
                        if not too_close:
                            # tmp_item += 1
                            # print(pt)
                            prev_matches.append(pt)
                            # cv2.rectangle(src_img, (pt[0], pt[1] - base_dimension[device_res][0]), (pt[0] + h, pt[1] + w + base_dimension[device_res][1]), 255, 2)
                            crop_x = pt[0]
                            crop_y = pt[1] - base_dimension[device_res][0]
                            # print(crop_x, crop_y)
                            roi = (img_copy[
                                   pt[1] - base_dimension[device_res][0]:pt[1] + w + base_dimension[device_res][1],
                                   pt[0]:pt[0] + h].copy())
                            # cv2.imwrite(r'images/evony/tmp/item' + str(tmp_item) + '.png', roi)
                            item_found = False
                            # Buy items from the list
                            for item in black_market_items["items"]:
                                if img.check_template_match(roi, item['image']):
                                    # Check buy options in buy type
                                    match = None
                                    purchase_type = None
                                    if item['buy_type']['gold']:
                                        match = img.get_template_coordinates(roi, gold_buy_template)
                                        purchase_type = "Gold"
                                    if match is not None and match[0] is False and item['buy_type']['gems']:
                                        match = img.get_template_coordinates(roi, gem_buy_template)
                                        purchase_type = "Gem"
                                    if match is not None and match[0] is False and item['buy_type']['rss']:
                                        for rss_type in rss_buy_templates:
                                            match = img.get_template_coordinates(roi, rss_type)
                                            purchase_type = "Resources"
                                            if match[0]:
                                                break
                                    if match is not None and match[0]:
                                        self.log = "Item " + item[
                                            'name'] + " found. Available for purchase with: " + purchase_type
                                        self.invokeDeviceConsole(self.log)
                                        self.device_emu.shell(
                                            f'input tap ' + str(match[1] + crop_x) + ' ' + str(match[2] + crop_y))
                                        time.sleep(1)
                                        confirm_screen = self.capture_screen()
                                        match_confirm = img.get_template_coordinates(confirm_screen, confirm_buy)
                                        if match_confirm[0]:
                                            self.device_emu.shell(
                                                f'input tap ' + str(match_confirm[1]) + ' ' + str(match_confirm[2]))
                                            self.log = "Purchasing..."
                                            self.invokeDeviceConsole(self.log)
                                            time.sleep(1)
                                            # TODO Implement Rebuy
                                            if item['buy_type']['rebuy']:
                                                print("Rebuy enabled")
                                                self.log = "Rebuy is yet to implement..."
                                                self.invokeDeviceConsole(self.log)
                                            # print(item['name'], " found")
                                            item_found = True
                                            break

                            # Buy items by rss
                            if black_market_items['all_rss'] and item_found is False:
                                match_confirm = None
                                for rss_type in rss_buy_templates:
                                    match = img.get_template_coordinates(roi, rss_type)
                                    if match[0]:
                                        self.log = "Random item found. Available for purchase with: Resources"
                                        self.invokeDeviceConsole(self.log)
                                        self.device_emu.shell(
                                            f'input tap ' + str(match[1] + crop_x) + ' ' + str(match[2] + crop_y))
                                        time.sleep(1)
                                        confirm_screen = self.capture_screen()
                                        match_confirm = img.get_template_coordinates(confirm_screen, confirm_buy)
                                        if match_confirm[0]:
                                            self.log = "Purchasing..."
                                            self.invokeDeviceConsole(self.log)
                                            self.device_emu.shell(
                                                f'input tap ' + str(match_confirm[1]) + ' ' + str(match_confirm[2]))
                                            time.sleep(1)
                                        break
                                if match_confirm is not None and match_confirm[0]:
                                    continue
                            # Buy items by gold
                            if black_market_items['all_gold'] and item_found is False:
                                match_confirm = None
                                match = img.get_template_coordinates(roi, gold_buy_template)
                                if match[0]:
                                    self.log = "Random item found. Available for purchase with: Gold"
                                    self.invokeDeviceConsole(self.log)
                                    self.device_emu.shell(
                                        f'input tap ' + str(match[1] + crop_x) + ' ' + str(match[2] + crop_y))
                                    time.sleep(1)
                                    confirm_screen = self.capture_screen()
                                    match_confirm = img.get_template_coordinates(confirm_screen, confirm_buy)
                                    if match_confirm[0]:
                                        self.log = "Purchasing..."
                                        self.invokeDeviceConsole(self.log)
                                        self.device_emu.shell(
                                            f'input tap ' + str(match_confirm[1]) + ' ' + str(match_confirm[2]))
                                        time.sleep(1)
                                    continue
                    refresh_times -= 1
                    # Click on refresh
                    if refresh_times != 0:
                        refresh_match = img.get_template_coordinates(src_img, gem_refresh)
                        if refresh_match[0] is False:
                            refresh_match = img.get_template_coordinates(src_img, free_refresh)
                        if refresh_match[0]:
                            self.device_emu.shell(f'input tap ' + str(refresh_match[1]) + ' ' + str(refresh_match[2]))
                            time.sleep(1)
            except Exception as e:
                print(e)
            self.log = "Stopping Black Market Mode"
            self.invokeDeviceConsole(self.log)
            self.switch_run.emit(self.index)
        else:
            # print("Not inside the black market")
            self.log = "Not inside the Black Market window"
            self.invokeDeviceConsole(self.log)
            self.switch_run.emit(self.index)

    def runTroopTraining(self):
        global img_lib_path
        self.args = {}
        troops = self.emulator_control['troop_training']
        print(troops)
        culture = None
        deleted_rows = 0
        for index, troop in enumerate(troops):
            # Verify and open the training window
            verify_building = cv2.imread(img_lib_path + 'troops_training/verify' + troop['building'])
            src_img = self.capture_screen()
            if not img.check_template_match(src_img, verify_building):
                if not self.navigateInsideKeep():
                    # print("Cannot navigate inside the keep")
                    self.log = "Failed to navigate inside the keep"
                    self.invokeDeviceConsole(self.log)
                    break
                if not culture:
                    # find the culture
                    # print("Finding the culture")
                    self.log = "Attempting to identify the culture"
                    self.invokeDeviceConsole(self.log)
                    culture = build_loc.findKeepCulture(self, img_lib_path)
                    if not culture:
                        # Skip the current training as it couldn't find the current culture
                        self.log = "Skipping the training since the culture cannot be identified"
                        self.invokeDeviceConsole(self.log)
                        break
                    else:
                        self.log = "The culture is " + culture
                        self.invokeDeviceConsole(self.log)
                if not build_loc.searchBuilding(self, troop['building'], img_lib_path + "buildings/" + culture):
                    if self.is_running:
                        # Skip the current training as it couldnt find the building
                        # print("Skipping, update in console that building is not found")
                        self.log = "Skipping the training since the building cannot be located"
                        self.invokeDeviceConsole(self.log)
                        continue
                    else:
                        print("Stopped")
                        continue
                else:
                    # Open the training window by clicking the train popup btn
                    train_popup = cv2.imread(img_lib_path + 'troops_training/train_popup.png')
                    src_img = self.capture_screen()
                    template_match = img.get_template_coordinates(src_img, train_popup)
                    if template_match[0] and self.is_running:
                        self.device_emu.shell(f'input tap ' + str(template_match[1]) + ' ' + str(template_match[2]))
                        time.sleep(1)
            # Init template images
            train_btn = cv2.imread(img_lib_path + 'troops_training/train_btn.png')
            max_bar = cv2.imread(img_lib_path + 'troops_training/max_bar.png')
            left_arrow = cv2.imread(img_lib_path + 'troops_training/left_arrow.png')
            right_arrow = cv2.imread(img_lib_path + 'troops_training/right_arrow.png')
            troop_tier = cv2.imread(img_lib_path + 'troops_training/' + troop['tier'] + '.png')
            training_speed = cv2.imread(img_lib_path + 'troops_training/training_speed_btn.png')
            finish_all = cv2.imread(img_lib_path + 'troops_training/finish_all_btn.png')

            # Find the troop tier
            tiers = [{'tier': 1, 'filename': 't1.png'}, {'tier': 2, 'filename': 't2.png'},
                     {'tier': 3, 'filename': 't3.png'}, {'tier': 4, 'filename': 't4.png'},
                     {'tier': 5, 'filename': 't5.png'}, {'tier': 6, 'filename': 't6.png'},
                     {'tier': 7, 'filename': 't7.png'}, {'tier': 8, 'filename': 't8.png'},
                     {'tier': 9, 'filename': 't9.png'}, {'tier': 10, 'filename': 't10.png'},
                     {'tier': 11, 'filename': 't11.png'}, {'tier': 12, 'filename': 't12.png'},
                     {'tier': 13, 'filename': 't13.png'}, {'tier': 14, 'filename': 't14.png'},
                     {'tier': 15, 'filename': 't15.png'}, {'tier': 16, 'filename': 't16.png'}]
            src_img = self.capture_screen()
            input_tier = int(general_utils.extract_numbers_from_string(troop['tier']))
            current_tier = 0
            for i in range(1, 17):
                # print("tier finding: ", i)
                tmp_tier = cv2.imread(img_lib_path + 'troops_training/' + tiers[i - 1]['filename'])
                # cv2.imwrite(r'images/evony/tmp/' + tiers[i - 1]['filename'], tmp_tier)
                if img.check_template_match(src_img, tmp_tier) and self.is_running:
                    current_tier = tiers[i - 1]['tier']
                    # print("Yahoo!!! ", current_tier)
                    self.log = "Tier " + str(current_tier) + " troop found"
                    self.invokeDeviceConsole(self.log)
                    break
            if current_tier < input_tier:
                # print("forward")
                self.log = "Navigating forward to locate Tier " + str(input_tier) + " troop"
                self.invokeDeviceConsole(self.log)
                for i in range(input_tier - current_tier):
                    forward_arrow = img.get_template_coordinates(src_img, right_arrow)
                    self.device_emu.shell(f'input tap ' + str(forward_arrow[1]) + ' ' + str(forward_arrow[2]))
                    time.sleep(1)
            elif current_tier > input_tier:
                # print("backward")
                self.log = "Navigating backward to locate Tier " + str(input_tier) + " troop"
                self.invokeDeviceConsole(self.log)
                for i in range(current_tier - input_tier):
                    backward_arrow = img.get_template_coordinates(src_img, left_arrow)
                    self.device_emu.shell(f'input tap ' + str(backward_arrow[1]) + ' ' + str(backward_arrow[2]))
                    time.sleep(1)
            # Verify the tier and train
            src_img = self.capture_screen()
            if img.check_template_match(src_img, troop_tier) and self.is_running:
                # print("Time to train")
                self.log = "Training Tier is confirmed"
                self.invokeDeviceConsole(self.log)
                train_times_count = 0
                for times in range(int(troop['train_times'])):
                    src_img = self.capture_screen()
                    if img.check_template_match(src_img, train_btn) and img.check_template_match(src_img,
                                                                                                 max_bar):
                        train_troops_btn = img.get_template_coordinates(src_img, train_btn)
                        self.device_emu.shell(
                            f'input tap ' + str(train_troops_btn[1]) + ' ' + str(train_troops_btn[2]))
                        time.sleep(1)
                        src_img = self.capture_screen()
                        training_speed_btn = img.get_template_coordinates(src_img, training_speed)
                        self.device_emu.shell(
                            f'input tap ' + str(training_speed_btn[1]) + ' ' + str(training_speed_btn[2]))
                        time.sleep(1)
                        src_img = self.capture_screen()
                        finish_all_btn = img.get_template_coordinates(src_img, finish_all)
                        self.device_emu.shell(
                            f'input tap ' + str(finish_all_btn[1]) + ' ' + str(finish_all_btn[2]))
                        time.sleep(1)
                        train_times_count += 1
                    else:
                        # print("Not enough rss/ train btn not found(not unlocked)")
                        self.log = "The Train button is currently inaccessible or disabled(most likely due to insufficient resources/tier not unlocked)"
                        self.invokeDeviceConsole(self.log)
                        if train_times_count == 0:
                            # print("update console saying its skipped")
                            self.log = "Troop training is skipped"
                            self.invokeDeviceConsole(self.log)
                        elif train_times_count < int(troop['train_times']):
                            # print("update table train times column with new value")
                            self.log = "Troop training is partially skipped"
                            self.invokeDeviceConsole(self.log)
                            self.args = {'type': 'update', 'index': index - deleted_rows,
                                         'new_value': int(troop['train_times']) - train_times_count}
                            self.update_training_table.emit(self.index, self.args)
                        break

                # Update the table
                if int(troop['train_times']) == train_times_count:
                    # remove it
                    # print("removing the row from table")
                    self.args = {'type': 'remove', 'index': index - deleted_rows}
                    self.update_training_table.emit(self.index, self.args)
                    deleted_rows += 1
        self.switch_run.emit(self.index)

    def runJoinRally(self, iteration_times):
        global img_lib_path
        global device_res
        pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
        controls = self.emulator_control['join_rally']
        # print(controls['other_settings']) #{'rotate_preset': 6, 'auto_use_stamina': True}
        # print(controls['monsters'])#{'monsters': [{'level': 1, 'name': '(Boss)Zombie', 'size': '36.5K', 'logic': 1}, {'level': 4, 'name': 'Legendary Hydra', 'size': '328.4M', 'logic': 2}, {'level': 1, 'name': 'Warlord', 'size': '13m', 'logic': 3}]}
        self.args['rotate_preset'] = controls['other_settings']['rotate_preset']
        self.args['attempt_preset_with_general'] = controls['other_settings']['attempt_preset_with_general']
        self.args['auto_use_stamina'] = controls['other_settings']['auto_use_stamina']
        # MAIN WHILE LOOP
        swipe_direction = True  # True = Up, False = Down
        iteration = 0
        while self.is_running and iteration < iteration_times:
            checked_cords_img = []
            swipe_iteration = 0
            if swipe_direction:
                swipe_cords = '250 810 250 320'
            else:
                swipe_cords = '250 320 250 810'
            while swipe_iteration < 4:
                if self.is_running is False:
                    return False
                flag_counter = 0
                while rally.navigateToAllianceWarWindow(self, img_lib_path) is False:
                    flag_counter += 1
                    # Skip finding when cant find alliance war window for a specific times of try
                    if flag_counter > 10:
                        return False
                    # print("Locating the Alliance War Window")
                    self.log = "Locating the Alliance War Window"
                    self.invokeDeviceConsole(self.log)
                else:
                    self.log = "Alliance War window has been successfully located"
                    self.invokeDeviceConsole(self.log)
                # print("Swipe ", swipe_direction, swipe_iteration)
                sleep(1)
                # Scan the rallies
                src_img = self.capture_screen()
                get_cords = rally.findCordsOfRalliesToJoin(img_lib_path, src_img)
                if len(get_cords) == 0:
                    print("Currently no rallies")
                else:
                    # print("Cords ", get_cords)  # [{'x': 217, 'y': 369}, {'x': 217, 'y': 684}]
                    # Validate Rally State Whether It's still in Rally or its launched
                    for cords in get_cords:
                        if self.is_running is False:
                            return False
                        if rally.checkRallyState(self, img_lib_path, src_img, cords, device_res, checked_cords_img):
                            # Join found, Open the boss window to read other details and join rally
                            self.device_emu.shell(f'input tap ' + str(cords['x']) + ' ' + str(cords['y']))
                            sleep(1)
                            rally_status = rally.fetchRallyDetailsAndJoin(self, img_lib_path, device_res, controls,
                                                                          checked_cords_img)
                            if rally_status is None:
                                continue

                swipe_iteration += 1
                self.device_emu.shell(f'input swipe ' + swipe_cords + ' 1500')
                time.sleep(1)
            swipe_direction = not swipe_direction
            iteration = iteration + 1

    def runPatrol(self):
        global img_lib_path
        controls = self.emulator_control['patrol']
        patrol_log = {}
        skipped_log = {}
        coordinate_flag = True
        refresh_x = refresh_y = patrol_x = patrol_y = counter = 0
        patrol_window_img = cv2.imread(img_lib_path + "/patrol/patrol_window.png")
        while controls['patrol_gem'] > 0 and controls['refresh_gold'] > 0 and self.is_running:
            src_img = self.capture_screen()
            if not img.check_template_match(src_img, patrol_window_img):
                self.invokeDeviceConsole("Invalid window, cannot locate patrol, quitting...")
                self.switch_run.emit(self.index)
                return False
            # Getting x and y cords of the refresh button & patrol button
            if coordinate_flag:
                refresh_template = cv2.imread(img_lib_path + "/patrol/refresh.png")
                patrol_template = cv2.imread(img_lib_path + "/patrol/patrol.png")
                coordinate_flag, refresh_x, refresh_y = img.get_template_coordinates(src_img, refresh_template)
                coordinate_flag, patrol_x, patrol_y = img.get_template_coordinates(src_img, patrol_template)
                coordinate_flag = False
            patrol_item = img.get_patrol_text(src_img)
            # print("Patrol Item found :", patrol_item)
            self.invokeDeviceConsole("Patrol item found: " + patrol_item)
            # print("Patrol List: ", controls['patrol_list'])
            if patrol_item.replace(" X 1", "") in controls['patrol_list']:
                # click patrol,but now used refresh here
                # print("inside patrol func")
                self.device_emu.shell(f'input tap ' + str(patrol_x) + ' ' + str(patrol_y))  # Patrol
                self.invokeDeviceConsole("Item acquired from patrol: " + patrol_item.replace(" X 1", ""))
                sleep(1)
                self.device_emu.shell(f'input tap 478 212')  # random tap on screen
                controls.update({'patrol_gem': controls['patrol_gem'] - 1})
                counter = counter + 1
                if patrol_item in patrol_log:
                    value = patrol_log.get(patrol_item) + 1
                    patrol_log[patrol_item] = value
                else:
                    patrol_log[patrol_item] = 1
            else:
                # click refresh
                self.invokeDeviceConsole("Patrol item is not selected. Hence skipping")
                self.device_emu.shell(f'input tap ' + str(refresh_x) + ' ' + str(refresh_y))  # Refresh
                controls.update({'refresh_gold': controls['refresh_gold'] - 1})
                if patrol_item in skipped_log:
                    value = skipped_log.get(patrol_item) + 1
                    skipped_log[patrol_item] = value
                else:
                    skipped_log[patrol_item] = 1
            sleep(1)
            # Waiting to turn the refresh button enabled
            flag = True
            while flag and self.is_running:
                src_img = self.capture_screen()
                template_img = cv2.imread(img_lib_path + "/patrol/refresh_disabled.png")
                flag = img.check_template_match(src_img, template_img)
                # print(flag)
        # print("Patrol log:: ", patrol_log)
        # print("Skipped  log:: ", skipped_log)
        if controls['refresh_gold'] == 0 or controls['patrol_gem'] == 0 or self.is_running is False:
            self.invokeDeviceConsole("Patrol done " + str(counter) + " times, exiting")
        self.switch_run.emit(self.index)

    def initDevice(self):
        global img_lib_path
        global device_res

        # CONNECT DEVICE
        # print("Inside initDevice")
        self.log = "Attempting to start  " + self.emulator_name + " on port " + self.emulator_port
        self.invokeEmulatorConsole(self.log)
        try:
            os.system(f'{self.adb_path} connect 127.0.0.1:{self.emulator_port}')
            client = AdbClient(host="127.0.0.1", port=5037)
            self.device_emu = client.device(f"127.0.0.1:{self.emulator_port}")
            # print(self.device_emu.get_state())
        except Exception as e:
            print(e)
            self.device_emu = None
            self.is_running = False

        # CHECKING AGAIN THAT THE CONNECTION IS ESTABLISHED OR NOT
        trial_expired = general_utils.checkTrailExpired(self.expiry_date)
        # self.log = f"Trial Expired::{trial_expired}"
        # self.invokeEmulatorConsole(self.log)
        if self.device_emu is not None and trial_expired is False:
            img_res = self.device_emu.shell(f'wm size')
            img_res_type = img_res.split('x')[1].replace("\n", "") + "p"
            img_lib_path = "images/evony/" + img_res_type + "/"
            device_res = img_res.split('x')[1].replace("\n", "")
            print("Device resolution ", device_res)
            # print(img_lib_path)
            if device_res == "540":
                self.log = "Successfully started " + self.emulator_name + " on port " + self.emulator_port
                self.invokeEmulatorConsole(self.log)
                # SIGNAL TO CHANGE STOP BUTTON
                self.start_stop_button_switch.emit(self.index)
                tmp_log = "Current Mode :: " + self.emulator_control['mode'] + \
                          "  ,Current Profile :: " + self.emulator_control['profile']
                self.invokeDeviceConsole(tmp_log)
                self.emulatorExec()
            else:
                self.log = "Failed to start " + self.emulator_name + " on port " + self.emulator_port + ", supported screen resolution is 540p"
                self.invokeEmulatorConsole(self.log)
        elif trial_expired:
            self.log = "Trial has Expired"
            self.invokeEmulatorConsole(self.log)
            self.invokeDeviceConsole(self.log)
        else:
            self.log = "Failed to start " + self.emulator_name + " on port " + self.emulator_port + ", Most likely wrong port number"
            self.invokeEmulatorConsole(self.log)
            self.invokeDeviceConsole(self.log)

    def navigateInsideKeep(self):
        # print("Navigating inside the keep")
        self.log = "Attempting to navigate inside the keep if required"
        self.invokeDeviceConsole(self.log)
        wm_btn_img = cv2.imread(img_lib_path + 'other/world_map_return_btn.png')
        ac_btn_img = cv2.imread(img_lib_path + 'other/alliance_city_return_btn.png')
        src_img = self.capture_screen()
        counter = 0
        while not img.check_template_match(src_img, wm_btn_img):
            if counter == 15:
                return False
            # print("not inside the keep")
            ac_btn = img.get_template_coordinates(src_img, ac_btn_img)
            if ac_btn[0]:
                self.device_emu.shell(f'input tap ' + str(ac_btn[1]) + ' ' + str(ac_btn[2]))
                sleep(3)
            else:
                self.device_emu.shell('input keyevent KEYCODE_BACK')
            sleep(1)
            src_img = self.capture_screen()
            counter += 1
        return True

    def launchEvony(self, flag):
        package_name = "com.topgamesinc.evony"
        main_activity = "com.topgamesinc.androidplugin.UnityActivity"
        if flag:
            self.device_emu.shell(f"am start -n {package_name}/{main_activity}")
        else:
            self.device_emu.shell(f"am force-stop {package_name}")
