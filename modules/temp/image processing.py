import cv2
import numpy as np


def preprocess_image(image_path):
    # Load image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Normalize images to 0 - 1 range

    image_gray = cv2.normalize(img, None, 0.0, 1.0, cv2.NORM_MINMAX, cv2.CV_32F)

    return image_gray



# Preprocess source and template images
source_img_path = r'C:\Users\91974\OneDrive\Documents\Project\Evony\images\evony\tmp\b11.png'
template_img_path = r'C:\Users\91974\OneDrive\Documents\GitHub\TEX\images\evony\540p\monsters\lv11_boss_540p.png'
source_img = preprocess_image(source_img_path)
template_img = preprocess_image(template_img_path)

# Find matches using the normalized correlation coefficient

match = cv2.matchTemplate(source_img, template_img, cv2.TM_CCOEFF_NORMED)

# Get the location of the best match

min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)

# If a match was found, draw a rectangle around it

if max_val > 0.9:
    print("Drawing rectangle")
    cv2.rectangle(source_img, max_loc, (max_loc[0] + template_img.shape[1], max_loc[1] + template_img.shape[0]), (0, 255, 0), 2)


# Display result
cv2.imshow('Detected', source_img)
#cv2.imshow('Detected', template_img)
cv2.waitKey(0)
cv2.destroyAllWindows()

