#################################################################################
# Copyright (c) 2023, MwoNuZzz
# All rights reserved.
#
# This source code is licensed under the GNU General Public License as found in the
# LICENSE file in the root directory of this source tree.
#################################################################################
import json
import sqlite3
from sqlite3 import Error

from modules.Query import get_all_boss_monster_info_query, get_all_normal_monster_info_query, \
    get_all_scoutables_info_query, get_all_profiles_info_query


# GENERAL

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
        return False
    return conn


def execute_query(conn, query, values):
    # with conn: for auto commit
    try:
        c = conn.cursor()
        c.execute(query, values)
    except Error as e:
        print(e)
        return False
    return c


def execute_query_no_param(conn, query):
    # with conn: for auto commit
    try:
        c = conn.cursor()
        c.execute(query)
    except Error as e:
        print(e)
        return False
    return c


def select_query_no_param(conn, query):
    try:
        c = conn.cursor()
        c.execute(query)
        return c
    except Error as e:
        print(e)
        return False


def select_query(conn, query, condition):
    try:
        c = conn.cursor()
        c.execute(query, condition)
        return c
    except Error as e:
        print(e)
        return False


def getAllScoutablesData():
    conn = create_connection("main.db")
    conn.execute("PRAGMA foreign_keys = ON")
    scoutables_table = select_query_no_param(conn, get_all_scoutables_info_query)
    scoutables_table = scoutables_table.fetchall()
    # print(scoutables_table)
    normal_monster_list = []
    for scout in scoutables_table:
        tmp_dict = {'id': scout[0], 'name': scout[1], 'type': scout[2], 'system': scout[3], 'preview_image': scout[4],
                    'img_540p': scout[5], 'img_id': scout[6]}
        normal_monster_list.append(tmp_dict)
    return normal_monster_list


def getAllProfiles():
    conn = create_connection("main.db")
    conn.execute("PRAGMA foreign_keys = ON")
    profile_table = select_query_no_param(conn, get_all_profiles_info_query)
    profile_table = profile_table.fetchall()
    profile_list = []
    for profile in profile_table:
        tmp_dict = {'id': profile[0], 'name': profile[1], 'controls': profile[2],
                    'default': True if profile[3] == 0 else False}
        profile_list.append(tmp_dict)
    return profile_list


def getAllNormalMonsterData():
    conn = create_connection("main.db")
    conn.execute("PRAGMA foreign_keys = ON")
    normal_monster_table = select_query_no_param(conn, get_all_normal_monster_info_query)
    normal_monster_table = normal_monster_table.fetchall()
    normal_monster_list = []
    for monster in normal_monster_table:
        tmp_dict = {'id': monster[0], 'name': monster[1], 'system': monster[2], 'preview_image': monster[3],
                    'img_540p': monster[4], 'img_threshold': monster[5],
                    'click_pos': json.loads(monster[6]), 'img_id': monster[7]}
        normal_monster_list.append(tmp_dict)
    return normal_monster_list


def getAllBossMonsterData():
    conn = create_connection("main.db")
    conn.execute("PRAGMA foreign_keys = ON")
    boss_monster_table = select_query_no_param(conn, get_all_boss_monster_info_query)
    boss_monster_table = boss_monster_table.fetchall()
    tmp_boss_monster_list = []
    for monster in boss_monster_table:
        tmp_dict = {'id': monster[0], 'preview_name': monster[1], 'monster_title': monster[2],
                    'monster_category': monster[3], 'system': monster[4], 'enable_map_scan': monster[5],
                    'monster_logic_id': monster[6], 'level_id': monster[7], 'level': monster[8], 'name': monster[9],
                    'size': monster[10],
                    'preview_image': monster[11], 'img_540p': monster[12], 'img_threshold': monster[13],
                    'click_pos': json.loads(monster[14]), 'img_id': monster[15]}
        tmp_boss_monster_list.append(tmp_dict)
    seen_keys = set()
    boss_monster_list = []
    for monster_list1 in tmp_boss_monster_list:
        levels = []
        if monster_list1["id"] not in seen_keys:
            for monster_list2 in tmp_boss_monster_list:
                if monster_list1["id"] == monster_list2["id"]:
                    levels.append(
                        {'level_id': monster_list2["level_id"], 'level': monster_list2["level"],
                         'name': monster_list2["name"], 'size': monster_list2["size"]})
            seen_keys.add(monster_list1["id"])
            tmp_dict = {'id': monster_list1["id"], 'preview_name': monster_list1["preview_name"],
                        'monster_title': monster_list1["monster_title"],
                        'monster_category': monster_list1["monster_category"], 'system': monster_list1["system"],
                        'enable_map_scan': monster_list1['enable_map_scan'],
                        'monster_logic_id': monster_list1["monster_logic_id"],
                        'levels': levels, 'preview_image': monster_list1["preview_image"],
                        'img_540p': monster_list1["img_540p"], 'img_threshold': monster_list1["img_threshold"],
                        'click_pos': monster_list1["click_pos"], 'img_id': monster_list1["img_id"]}

            boss_monster_list.append(tmp_dict)
    #print(boss_monster_list)
    return boss_monster_list
