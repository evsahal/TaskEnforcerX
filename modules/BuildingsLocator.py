#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import time

import cv2
import numpy as np
from modules import ImageRecognitionUtils as img
import datetime


def searchBuilding(self, building, path):
    # print("Im inside openBuilding to find ", building)
    # Swipe Pattern
    swipe_coordinates = {'up': '380 400 60 600', 'left': '60 400 360 600', 'down': '60 600 380 400',
                         'right': '360 600 60 400'}
    general_buildings = getAllBuildings(path)
    direction_buildings = getDirectionBuildingsInfo(path)
    building_template = cv2.imread(path + building)
    # print("building path: ", path + building)
    self.device_emu.shell(f'input swipe 250 320 250 340 2500')  # SCREEN PRESS
    src_img = self.capture_screen()
    # cv2.imwrite(r"C:\Users\91974\OneDrive\Documents\Project\Evony\images\evony\tmp\demo.png", src_img)
    template_match = img.get_template_coordinates(src_img, building_template)

    i = 0
    while template_match[0] is not True and self.is_running:
        if i == 15:
            break
        for building in direction_buildings:
            # print(building['building_name'])
            if self.is_running:
                if img.check_template_match(src_img, building['building_img']):
                    # print(building["building_name"] + " Found While searching(Nav)")
                    for direction in building['next']['direction']:

                        for swipe_times in range(direction['swipe_times']):
                            if self.is_running:
                                self.device_emu.shell(
                                    f'input swipe ' + swipe_coordinates[direction['movement']] + ' 2000')
                                src_img = self.capture_screen()
                                template_match = img.get_template_coordinates(src_img, building_template)
                                if template_match[0] is True:
                                    # print("Yeyyyy Found it inside direction_building")
                                    break
                                else:
                                    direction_template = get_general_building_img(general_buildings,
                                                                                  building['next'][
                                                                                      'building_name'])
                                    if img.check_template_match(src_img, direction_template):
                                        # print("Next direction building found and skipping rest of the iterations")
                                        break
                        if template_match[0] is True:
                            break
        if template_match[0]:
            break

        for building in general_buildings:
            if "next_building_direction" in building and img.check_template_match(src_img, cv2.imread(building['path'])) and self.is_running:
                # print(building["building_name"] + " Found While searching in general category")
                for direction in building['next_building_direction']['direction']:
                    if self.is_running:
                        for swipe_times in range(direction['swipe_times']):
                            if self.is_running:
                                self.device_emu.shell(
                                    f'input swipe ' + swipe_coordinates[direction['movement']] + ' 2000')
                                src_img = self.capture_screen()
                                template_match = img.get_template_coordinates(src_img, building_template)
                                if template_match[0] is True:
                                    # print("Yeyyyy Found it when inside general_building")
                                    break
                                else:
                                    general_template = get_general_building_img(general_buildings,
                                                                                building[
                                                                                    'next_building_direction'][
                                                                                    'building_name'])
                                    if img.check_template_match(src_img, general_template):
                                        # print("Next general building found and skipping rest of the iterations")
                                        # print(building['next_building_direction']['building_name'])
                                        continue
                        if template_match[0] is True:
                            break
        if template_match[0]:
            break
        # Random swipe
        if self.is_running:
            self.device_emu.shell(f'input swipe ' + swipe_coordinates['up'] + ' 2000')
            src_img = self.capture_screen()
            template_match = img.get_template_coordinates(src_img, building_template)
            if template_match[0]:
                # print("Yeyyyy Found it on random swipe")
                break
        i += 1

    if template_match[0] is True and self.is_running:
        self.device_emu.shell(f'input tap ' + str(template_match[1]) + ' ' + str(template_match[2]))
        time.sleep(1)
        return True
    else:
        return False


def findKeepCulture(self, img_lib_path):
    self.device_emu.shell(f'input swipe 250 320 250 340 2500')  # SCREEN PRESS
    src_img = self.capture_screen()
    # Try matching all the buildings template with the src_img
    # cultures = ['europe', 'china', 'japan', 'korea', 'america', 'russia', 'arabia']
    cultures = ['europe', 'russia']
    # Pass "" to append the path of the images later
    all_buildings = getAllBuildings("")
    for building in all_buildings:
        for culture in cultures:
            template_building = cv2.imread(img_lib_path + "buildings/" + culture + building['path'])
            if img.check_template_match(src_img, template_building):
                # print("Culture Match Found:: ", culture)
                return culture
    # print("Couldn't find a culture")
    return None


def get_general_building_img(buildings_info, building_name):
    building_dict = next(filter(lambda x: x['building_name'] == building_name, buildings_info), None)
    if building_dict is None:
        return None
    return cv2.imread(building_dict['path'])


def getAllBuildings(path):
    buildings_info = [{'building_name': 'Art Hall', 'path': path + "_arthall.png",
                       'next_building_direction': {'building_name': 'Academy',
                                                   'direction': [{'movement': 'up', 'swipe_times': 1}]}},
                      {'building_name': 'Archer Tower', 'path': path + "_archertower.png",
                       'next_building_direction': {'building_name': 'Walls',
                                                   'direction': [{'movement': 'up', 'swipe_times': 1}]}},
                      {'building_name': 'Battlefield', 'path': path + "_battlefield.png",
                       'next_building_direction': {'building_name': 'Academy',
                                                   'direction': [{'movement': 'up', 'swipe_times': 2}]}},
                      {'building_name': 'Bunker', 'path': path + "_bunker.png",
                       'next_building_direction': {'building_name': 'Academy',
                                                   'direction': [{'movement': 'left', 'swipe_times': 2}]}},
                      {'building_name': 'Keep', 'path': path + "_keep.png",
                       'next_building_direction': {'building_name': 'Holy Palace',
                                                   'direction': [{'movement': 'right', 'swipe_times': 1}]}},
                      {'building_name': 'Portal', 'path': path + "_portal.png",
                       'next_building_direction': {'building_name': 'Academy',
                                                   'direction': [{'movement': 'left', 'swipe_times': 2}]}},
                      {'building_name': 'Rally Spot', 'path': path + "_rallyspot.png",
                       'next_building_direction': {'building_name': 'Academy',
                                                   'direction': [{'movement': 'left', 'swipe_times': 2}]}},
                      {'building_name': 'Research Factory', 'path': path + "_researchfactory.png",
                       'next_building_direction': {'building_name': 'Academy',
                                                   'direction': [{'movement': 'up', 'swipe_times': 1}]}},
                      {'building_name': 'Tavern', 'path': path + "_tavern.png",
                       'next_building_direction': {'building_name': 'Holy Palace',
                                                   'direction': [{'movement': 'up', 'swipe_times': 1}]}},
                      {'building_name': 'Warehouse', 'path': path + "_warehouse.png",
                       'next_building_direction': {'building_name': 'Academy',
                                                   'direction': [{'movement': 'up', 'swipe_times': 1}]}},
                      {'building_name': 'Watchtower', 'path': path + "_watchtower.png",
                       'next_building_direction': {'building_name': 'Pasture',
                                                   'direction': [{'movement': 'up', 'swipe_times': 1}]}},
                      {'building_name': 'Pasture', 'path': path + "_pasture.png"},
                      {'building_name': 'Academy', 'path': path + "_academy.png"},
                      {'building_name': 'Holy Palace', 'path': path + "_holypalace.png"},
                      {'building_name': 'Walls', 'path': path + "_walls.png"}]
    return buildings_info


def getDirectionBuildingsInfo(path):
    buildings_info = getAllBuildings(path)
    direction_buildings_info = [{'building_name': 'Walls',
                                 'building_img': cv2.imread([d for d in buildings_info if d.get("building_name") == "Walls"][0][
                                     "path"]),
                                 'building_order': 1, 'occurrence_possibility': True,
                                 'nearby_buildings': ['Pasture', 'Art Hall', 'Battlefield'],
                                 'next': {'building_name': 'Pasture',
                                          'direction': [{'movement': 'left', 'swipe_times': 1}]},
                                 'previous': {'building_name': 'Archer Tower',
                                              'direction': [{'movement': 'down', 'swipe_times': 1}]}},
                                {'building_name': 'Pasture',
                                 'building_img': cv2.imread([d for d in buildings_info if d.get("building_name") == "Pasture"][0][
                                     "path"]),
                                 'building_order': 2, 'occurrence_possibility': True,
                                 'nearby_buildings': ['Art Hall', 'Battlefield', 'Watchtower',
                                                      'Subordinate City',
                                                      'Research Factory'],
                                 'next': {'building_name': 'Barracks',
                                          'direction': [{'movement': 'up', 'swipe_times': 2}]},
                                 'previous': {'building_name': 'Walls',
                                              'direction': [{'movement': 'right', 'swipe_times': 1}]}},
                                {'building_name': 'Academy',
                                 'building_img': cv2.imread([d for d in buildings_info if d.get("building_name") == "Academy"][0][
                                     "path"]),
                                 'building_order': 3, 'occurrence_possibility': True,
                                 'nearby_buildings': ['Research Factory', 'Warehouse', 'Shrine', 'Keep', 'Tavern'],
                                 'next': {'building_name': 'Holy Palace',
                                          'direction': [{'movement': 'right', 'swipe_times': 1}]},
                                 'previous': {'building_name': 'Pasture',
                                              'direction': [{'movement': 'down', 'swipe_times': 2}]}},
                                {'building_name': 'Holy Palace', 'building_img':
                                    cv2.imread([d for d in buildings_info if d.get("building_name") == "Holy Palace"][0]["path"]),
                                 'building_order': 4, 'occurrence_possibility': True,
                                 'nearby_buildings': ['Keep', 'Tavern', 'Rally Spot', 'Bunker', 'Portal'],
                                 'next': {'building_name': 'Walls',
                                          'direction': [{'movement': 'down', 'swipe_times': 2},
                                                        {'movement': 'left', 'swipe_times': 1},
                                                        {'movement': 'up', 'swipe_times': 1},
                                                        {'movement': 'left', 'swipe_times': 1},
                                                        {'movement': 'down', 'swipe_times': 1},
                                                        {'movement': 'right', 'swipe_times': 1}]},
                                 'previous': {'building_name': 'Academy',
                                              'direction': [{'movement': 'left', 'swipe_times': 1}]}}]
    return direction_buildings_info
