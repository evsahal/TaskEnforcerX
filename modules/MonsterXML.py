#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import xml.etree.ElementTree as ET
from lxml import etree
import shutil
from pathlib import Path
from modules import create_connection, execute_query
from modules.Query import add_monster_image_query, add_boss_monster_query, add_monster_level_query


class MonsterXML:
    def __init__(self, file_path):
        self.file_path = file_path
        self.boss_monsters_list = []

    def readMonsterXML(self):
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        tree = ET.parse(self.file_path, parser=parser)
        root = tree.getroot()

        logic = root.get('logic')

        for boss_monsters in tree.findall('boss_monster'):
            # print("--Boss Monster--")
            boss_monster = {}
            for boss in boss_monsters:
                # print(boss.tag + " : " + boss.text)
                monster_image = {}
                monster_level_info = []
                if boss.tag == "preview_name":
                    boss_monster["preview_name"] = boss.text
                if boss.tag == "monster_title":
                    boss_monster["monster_title"] = boss.text
                if boss.tag == "monster_category":
                    boss_monster["monster_category"] = boss.text
                boss_monster["monster_logic_id"] = logic
                if boss.tag == "monster_image":
                    for img in boss:
                        # print(img.tag + " : " + img.text)
                        if img.tag == "preview_image":
                            monster_image['preview_image'] = img.text
                        if img.tag == "p_540":
                            monster_image['img_540p'] = img.text
                        if img.tag == "p_1080":
                            monster_image['img_1080p'] = img.text
                    boss_monster["monster_image"] = monster_image
                    # print(monster_image)
                if boss.tag == "monster_level":
                    for levels in boss:
                        monster_level = {}
                        for level in levels:
                            # print(level.tag + " : " + level.text)
                            if level.tag == "lv":
                                monster_level["level"] = level.text
                            if level.tag == "name":
                                monster_level["name"] = level.text
                            if level.tag == "size":
                                monster_level["size"] = level.text
                        # print(monster_level_info)
                        monster_level_info.append(monster_level)
                    boss_monster["monster_level_info"] = monster_level_info
                    # print(monster_level_info)
            self.boss_monsters_list.append(boss_monster)
        # return self.boss_monsters_list

    def processAndSaveToDatabase(self):

        for boss in self.boss_monsters_list:
            # print(boss)
            monster_image = {}
            monster = {}
            monster_image["p_img"] = boss["monster_image"]["preview_image"]
            monster_image["540p"] = boss["monster_image"]["img_540p"]
            monster_image["1080p"] = boss["monster_image"]["img_1080p"]
            # Important line below to uncomment
            # self.moveMonsterImagesToPath(monster_image)

            # print(monster_image)
            conn = create_connection("main.db")
            conn.execute("PRAGMA foreign_keys = ON")
            monster_image_id = execute_query(conn, add_monster_image_query, monster_image).lastrowid

            monster["p_name"] = boss["preview_name"]
            monster["title"] = boss["monster_title"]
            monster["category"] = boss["monster_category"]
            monster["img_id"] = monster_image_id
            monster["logic_id"] = boss["monster_logic_id"]
            # print(monster)
            monster_id = execute_query(conn, add_boss_monster_query, monster).lastrowid

            for levels in boss["monster_level_info"]:
                level = {'boss_monster_id': monster_id, 'name': levels["name"], 'level': levels["level"],
                         'size': levels["size"]}
                # print(level)
                execute_query(conn, add_monster_level_query, level)
            # Important line below to uncomment
            conn.commit()

    def moveMonsterImagesToPath(self, img):
        file = Path(self.file_path)
        src_dir = str(file.parent)
        shutil.copy2(src_dir + "/images/preview/" + img['p_img'], "images/evony/preview/" + img['p_img'])
        shutil.copy2(src_dir + "/images/540p/" + img['540p'], "images/evony/540p/" + img['540p'])
        shutil.copy2(src_dir + "/images/1080p/" + img['1080p'], "images/evony/1080p/" + img['1080p'])
