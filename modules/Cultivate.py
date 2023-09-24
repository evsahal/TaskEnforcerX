#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import re
from time import sleep
import numpy as np
import cv2
from modules import ImageRecognitionUtils as img, GeneralUtils as g_util
import pytesseract


class Cultivate:
    def __init__(self, src_img, settings, img_lib_path):
        self.attributes = {}
        self.src_img = src_img
        self.img_lib_path = img_lib_path
        self.validateSS(settings)

    def validateSS(self, settings):
        # Setting up attribute var
        for flag in settings:
            if settings[flag]:
                self.attributes[flag] = {'attribute': flag, 'org_value': None, 'status': None, 'new_value': None,
                                         'drop': None, 'image': self.cropAttributeImage(flag)}
        # print(attributes)
        # Now process each attribute ss
        for attr in self.attributes:
            # print(attr)
            self.attributes[attr]['org_value'] = self.fetchCultivateValue(self.attributes[attr]['image'])
            # print(attributes[attr]['org_value'])
            self.attributes[attr]['status'] = self.checkNewCultivateStatus(self.attributes[attr]['image'])
            # print(attributes[attr]['status'])
            if self.attributes[attr]['status'] is not None:
                self.attributes[attr]['new_value'] = self.fetchNewCultivateValue(self.attributes[attr]['image'],
                                                                                 self.attributes[attr]['status'])
                # print(attributes[attr]['new_value'])
            # remove the image to free the space
            if 'image' in self.attributes[attr]:
                del self.attributes[attr]['image']
        # set drop value
        highest_org_value = max(item['org_value'] for item in self.attributes.values())
        for key, value in self.attributes.items():
            self.attributes[key]['drop'] = highest_org_value - value['org_value']

    def cropAttributeImage(self, attr):
        template_img = cv2.imread(self.img_lib_path + "more_activities/" + attr + "_cultivate.png")
        w, h = template_img.shape[:-1]
        cords = img.get_template_match_coordinates(self.src_img, template_img)
        if cords[0]:
            roi = self.src_img[cords[2]:cords[2] + w, cords[1] + h:cords[1] * 10].copy()
            return roi

    def fetchNewCultivateValue(self, attr_img, status):
        if status:
            template_img = cv2.imread(self.img_lib_path + "more_activities/up_cultivate.png")
            # Define the lower and upper thresholds for the green color
            lower_color = np.array([35, 100, 100])
            upper_color = np.array([85, 255, 255])
        else:
            template_img = cv2.imread(self.img_lib_path + "more_activities/down_cultivate.png")
            # Define the lower and upper thresholds for the red color
            lower_color = np.array([0, 100, 100])
            upper_color = np.array([10, 255, 255])
        w, h = template_img.shape[:-1]
        cords = img.get_template_match_coordinates(attr_img, template_img)
        if cords[0]:
            roi = attr_img[cords[2]:cords[2] + w, cords[1] + h:cords[1] * 10].copy()
            # Convert the image to HSV color space
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            # Create a mask for the green/red color
            mask = cv2.inRange(hsv, lower_color, upper_color)
            # Replace the green/red color with black
            result = cv2.bitwise_and(roi, roi, mask=mask)
            result[mask > 0] = (0, 0, 0)
            # Create a mask for the non-green/non-red areas
            inverse_mask = cv2.bitwise_not(mask)
            # Replace the non-green/non-red areas with white
            result[inverse_mask > 0] = (255, 255, 255)
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 3)
            pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
            text = pytesseract.image_to_string(gray, config='--psm 6')
            text = re.sub(r'\D', '', text)
            number = int(text) if text.isdigit() else 1
            return -number if not status else number

    def fetchCultivateValue(self, attr_img):
        arrow_cultivate = cv2.imread(self.img_lib_path + "more_activities/arrow_cultivate.png")
        w, h = arrow_cultivate.shape[:-1]
        cords = img.get_template_match_coordinates(attr_img, arrow_cultivate)
        if cords[0]:
            roi = attr_img[cords[2]:cords[2] + w, 0:cords[1]].copy()
            # Convert the image to HSV color space
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            # Define the lower and upper thresholds for the green color
            lower_green = np.array([35, 100, 100])
            upper_green = np.array([85, 255, 255])
            # Create a mask for the green color
            mask = cv2.inRange(hsv, lower_green, upper_green)
            # Replace the green color with black
            result = cv2.bitwise_and(roi, roi, mask=mask)
            result[mask > 0] = (0, 0, 0)
            # Create a mask for the non-green areas
            inverse_mask = cv2.bitwise_not(mask)
            # Replace the non-green areas with white
            result[inverse_mask > 0] = (255, 255, 255)
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 3)
            pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
            text = pytesseract.image_to_string(gray, config='--psm 6')
            text = re.sub(r'\D', '', text)
            return int(text) if text.isdigit() else 0

    def checkNewCultivateStatus(self, attr_img):
        cultivate = ['up_cultivate', 'down_cultivate']
        for x in cultivate:
            template_img = cv2.imread(self.img_lib_path + "more_activities/" + x + ".png")
            if img.check_template_match(attr_img, template_img):
                return True if x == 'up_cultivate' else False
        return None

    def validateAttributes(self):
        # checkAllStatusTrue
        if all(value['status'] for value in self.attributes.values()):
            return True

        # checkNewValueTotal
        total = 0
        for attr in self.attributes:
            if self.attributes[attr]['new_value'] is not None:
                total += self.attributes[attr]['new_value']
        # print("Total is ", total)
        if total > 0:
            return True
        highest_drops = self.getAttrNameOfHighestDropValue()
        if len(self.attributes) == 1:
            # Its obvious that the value is 0 or negative
            return False
        elif len(self.attributes) in [2, 3, 4]:
            for drop in highest_drops:
                if self.attributes[drop]['new_value'] is not None:
                    if self.attributes[drop]['new_value'] > 0:
                        return True
        return False

    def getAttrNameOfHighestDropValue(self):
        highest_drop_value = -1  # Initialize with a value lower than any possible drop value
        highest_drop_attributes = []
        for key, value in self.attributes.items():
            drop = value['drop']
            if drop > highest_drop_value:
                highest_drop_value = drop
                highest_drop_attributes = [value['attribute']]
            elif drop == highest_drop_value:
                highest_drop_attributes.append(value['attribute'])
        # print(highest_drop_attributes)
        return highest_drop_attributes
