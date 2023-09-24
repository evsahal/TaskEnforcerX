#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import os
from datetime import datetime, timedelta
import re
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
import requests
import pytz  # Import the pytz library to work with timezones


def extract_numbers_from_string(string):
    number = ''
    for i in string:
        if i.isnumeric():
            number += str(int(i))
    return number


def remove_number_from_string(string):
    return re.sub(r'\d+', '', string)


def getIcon(value):
    icon4 = QIcon()
    icon4.addFile(value, QSize(), QIcon.Normal, QIcon.Off)
    return icon4


def get_date_and_time():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def generateObjectName(name):
    name = name.lower().replace(" ", "")
    name = name + "_"
    return name


def format_with_prefix(num):
    if num >= 1000000000:
        result = num / 1000000000
        return "{:.0f}b".format(result) if result.is_integer() else "{:.1f}b".format(result).rstrip('.0')
    elif num >= 1000000:
        result = num / 1000000
        return "{:.0f}m".format(result) if result.is_integer() else "{:.1f}m".format(result).rstrip('.0')
    elif num >= 1000:
        result = num / 1000
        return "{:.0f}k".format(result) if result.is_integer() else "{:.1f}k".format(result).rstrip('.0')
    else:
        return str(num)


def parse_with_prefix(num):
    if isinstance(num, str):
        if num[-1] == 'm':
            return float(num[:-1]) * 1000000
        elif num[-1] == 'k':
            return float(num[:-1]) * 1000
        else:
            return float(num)
    else:
        return float(num)


def convertSecondToTimeFormat(seconds):
    time_str = str(timedelta(seconds=seconds))

    # Pad the string with leading zeros if necessary
    if len(time_str) < 8:
        time_str = "0" * (8 - len(time_str)) + time_str

    return time_str


def get_current_date_from_internet():
    try:
        # Use a trusted NTP server to get the current date and time
        current_datetime = requests.get("https://worldtimeapi.org/api/ip").json()["datetime"]
        # Create a timezone-aware datetime object using UTC timezone
        return datetime.fromisoformat(current_datetime).replace(tzinfo=pytz.UTC)
    except Exception as e:
        print(f"Error fetching current date: {e}")
        return None


def checkTrailExpired(expiry_date):
    current_date = get_current_date_from_internet()
    if current_date is None:
        # print("Unable to fetch the date from internet")
        return True
    remaining_days = (expiry_date - current_date).days
    if remaining_days >= 0:
        return False
    else:
        # print("Trail expired")
        return True


def getPathADB():
    # print(os.path.join(os.getcwd(), "platform-tools"))
    return os.path.join(os.getcwd(), "platform-tools")
