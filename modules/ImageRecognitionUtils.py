#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import cv2
import numpy as np
from PIL import Image
from pytesseract import pytesseract, Output
from skimage.metrics import structural_similarity as ssim


def get_template_coordinates(image, template_image):
    w, h = template_image.shape[:-1]
    result = cv2.matchTemplate(image, template_image, cv2.TM_CCOEFF_NORMED)
    threshold = .8
    loc = np.where(result >= threshold)
    try:
        x = loc[1][0]
        y = loc[0][0]
    except:
        return False, 0, 0
    center_x = int(x + 0.5 * h)
    center_y = int(y + 0.5 * w)
    return True, center_x, center_y


def get_template_coordinates_gray(image, template_image):
    w, h = template_image.shape[:-1]
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_template_image = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray_image, gray_template_image, cv2.TM_CCOEFF_NORMED)
    threshold = .8
    loc = np.where(result >= threshold)
    try:
        x = loc[1][0]
        y = loc[0][0]
    except:
        return False, 0, 0
    center_x = int(x + 0.5 * h)
    center_y = int(y + 0.5 * w)
    return True, center_x, center_y


def get_template_match_coordinates(image, template_image):
    result = cv2.matchTemplate(image, template_image, cv2.TM_CCOEFF_NORMED)
    threshold = .8
    loc = np.where(result >= threshold)
    try:
        x = loc[1][0]
        y = loc[0][0]
    except:
        return False, 0, 0
    return True, x, y


def check_template_match(image, template_image):
    w, h = template_image.shape[:-1]
    result = cv2.matchTemplate(image, template_image, cv2.TM_CCOEFF_NORMED)
    threshold = .9
    loc = np.where(result >= threshold)
    try:
        x = loc[1][0]
        y = loc[0][0]
    except:
        return False
    return True


def check_image_match(image_1, image_2):
    # Convert the images to grayscale
    img1_gray = cv2.cvtColor(image_1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(image_2, cv2.COLOR_BGR2GRAY)

    # Calculate the SSIM value
    ssim_score = ssim(img1_gray, img2_gray)

    # Define a threshold for similarity
    similarity_threshold = 0.95

    # Compare the SSIM score with the threshold
    if ssim_score >= similarity_threshold:
        return True
    else:
        return False


def get_text_from_image_grayscale(image):
    pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
    config_tesseract = r'--tessdata-dir "Tesseract-OCR\Tessdata"'
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, config=config_tesseract)
    return text


def get_patrol_text(image):
    pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
    config_tesseract = r'--tessdata-dir "Tesseract-OCR\Tessdata"'
    lower = np.array([50, 100, 100])
    upper = np.array([70, 255, 255])
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    invert = 255 - mask
    result = pytesseract.image_to_string(invert, lang="eng", config=config_tesseract, output_type=Output.DICT)
    for txt in result['text'].split('\n'):
        if "X 1" in txt:
            return txt
    return None


def get_hsv_of_rgb(rgb_code):
    # rgb = np.uint8([[[0, 255, 0]]])
    rgb = np.uint8([[rgb_code]])

    # Convert RGB color to HSV
    hsv = cv2.cvtColor(rgb, cv2.COLOR_BGR2HSV)
    return hsv


def rgb_of_pixel(img_path, x, y):
    im = Image.open(img_path).convert('RGB')
    r, g, b = im.getpixel((x, y))
    rgb = (r, g, b)
    return rgb
