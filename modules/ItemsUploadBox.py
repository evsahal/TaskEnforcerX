#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import shutil
import time
from pathlib import Path
import os.path
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QCursor
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QListWidget, QListWidgetItem, QWidget, QHBoxLayout, QPushButton, \
    QFrame, QFileDialog, QLineEdit, QComboBox, QCheckBox

from modules import extract_numbers_from_string, select_query_no_param, \
    create_connection, execute_query, add_monster_image_query, add_normal_monster_query, add_scoutables_query, \
    get_all_normal_monster_names, get_all_scoutables_names, get_all_boss_monster_preview_names, add_boss_monster_query, \
    add_boss_monster_query_upload, add_monster_level_query
from modules.ui.upload_window import Ui_Upload_Window
from modules.ui.normal_monster_item import Ui_normal_monster_item
from modules.ui.boss_monster_item import Ui_boss_monster_item
from modules.ui.scoutables_item import Ui_scoutables_item
from modules import GeneralUtils as gu


class UploadNormalMonsterItem(QWidget, Ui_normal_monster_item):
    def __init__(self, properties, parent=None):
        super(UploadNormalMonsterItem, self).__init__(parent)
        self.setupUi(self)
        try:
            self.content_frame.setObjectName("content_frame_" + str(properties['id']))
            self.delete_item.setObjectName("delete_item_" + str(properties['id']))
            self.select_directory.setObjectName("select_directory_" + str(properties['id']))
            self.img_path.setObjectName("img_path_" + str(properties['id']))
            self.img_path.setReadOnly(True)
            self.monster_name.setObjectName("monster_name_" + str(properties['id']))
            self.preview_image.setObjectName("preview_image_" + str(properties['id']))
            self.img_540p.setObjectName("img_540p_" + str(properties['id']))
            self.img_1080p.setObjectName("img_1080p_" + str(properties['id']))
        except Exception as e:
            print(e)


class UploadScoutablesItem(QWidget, Ui_scoutables_item):
    def __init__(self, properties, parent=None):
        super(UploadScoutablesItem, self).__init__(parent)
        self.setupUi(self)
        try:
            self.content_frame.setObjectName("content_frame_" + str(properties['id']))
            self.delete_item.setObjectName("delete_item_" + str(properties['id']))
            self.select_directory.setObjectName("select_directory_" + str(properties['id']))
            self.img_path.setObjectName("img_path_" + str(properties['id']))
            self.img_path.setReadOnly(True)
            self.scoutables_name.setObjectName("scoutables_name_" + str(properties['id']))
            self.preview_image.setObjectName("preview_image_" + str(properties['id']))
            self.img_540p.setObjectName("img_540p_" + str(properties['id']))
            self.img_1080p.setObjectName("img_1080p_" + str(properties['id']))
            self.type.setObjectName("type_" + str(properties['id']))
        except Exception as e:
            print(e)


class UploadBossMonsterItem(QWidget, Ui_boss_monster_item):
    def __init__(self, properties, parent=None):
        super(UploadBossMonsterItem, self).__init__(parent)
        self.setupUi(self)
        try:
            self.content_frame.setObjectName("content_frame_" + str(properties['id']))
            self.delete_item.setObjectName("delete_item_" + str(properties['id']))
            self.select_directory.setObjectName("select_directory_" + str(properties['id']))
            self.img_path.setObjectName("img_path_" + str(properties['id']))
            self.img_path.setReadOnly(True)
            self.select_logic.setObjectName("select_logic_" + str(properties['id']))
            self.select_logic.setPlaceholderText(str(properties['id']))
            self.select_category.setObjectName("select_category_" + str(properties['id']))
            # self.monster_name.setText("Boss Monster" + str(properties['id']))
            self.monster_name.setObjectName("monster_name_" + str(properties['id']))
            self.preview_name.setObjectName("preview_name_" + str(properties['id']))
            self.enable_map_scan.setObjectName("enable_map_scan_" + str(properties['id']))
            self.preview_image.setObjectName("preview_image_" + str(properties['id']))
            self.img_540p.setObjectName("img_540p_" + str(properties['id']))
            self.img_1080p.setObjectName("img_1080p_" + str(properties['id']))
            self.level_frame.setObjectName("level_frame_" + str(properties['id']))
            self.level_name.setObjectName("level_name_" + str(properties['id']))
            self.level.setObjectName("level_" + str(properties['id']))
            self.level_power.setObjectName("level_power_" + str(properties['id']))
            self.add_level.setObjectName("add_level_" + str(properties['id']))
            self.level_widget.setObjectName("level_widget_" + str(properties['id']))
            self.add_level.clicked.connect(self.addNewLevel)
            self.select_logic.currentIndexChanged.connect(self.logicSelectionChange)
            self.max_level = 0
            self.current_level = 0
        except Exception as e:
            print(e)

    def logicSelectionChange(self, index):
        object_id = self.sender().placeholderText()
        self.initLevelWidget(object_id, index + 1)

    def initLevelWidget(self, object_id, logic):
        self.findChild(QFrame, "level_frame_" + object_id).setEnabled(True)
        self.findChild(QLineEdit, "level_name_" + object_id).clear()
        self.findChild(QLineEdit, "level_" + object_id).clear()
        self.findChild(QLineEdit, "level_power_" + object_id).clear()
        self.findChild(QPushButton, "add_level_" + str(object_id)).setEnabled(True)
        self.current_level = 0
        if logic == 1:
            self.max_level = 1
        elif logic == 2 or logic == 3:
            self.max_level = 10
        try:
            # Setting the Items list
            if hasattr(self, 'add_levels_layout'):
                # TODO need fix for instant deletion
                self.add_levels_layout.removeWidget(self.add_levels_fc)
                self.add_levels_layout.deleteLater()

            self.add_levels_fc = FlowContainerLevels()
            self.add_levels_fc.setObjectName("levels_fc_" + str(object_id))
            self.add_levels_layout = QVBoxLayout()
            level_widget = self.findChild(QWidget, "level_widget_" + str(object_id))
            level_widget.setLayout(self.add_levels_layout)
            self.add_levels_layout.addWidget(self.add_levels_fc)
        except Exception as e:
            print(e)

    def addNewLevel(self):
        object_id = gu.extract_numbers_from_string(self.sender().objectName())
        name = self.findChild(QLineEdit, "level_name_" + object_id).text().strip()
        level = self.findChild(QLineEdit, "level_" + object_id).text().strip()
        power = self.findChild(QLineEdit, "level_power_" + object_id).text().strip()
        # Validate inputs
        if not name or not level or not power:
            print("Fields are empty.")
            # self.upload_console.appendPlainText("Fields are empty.")
            return False
        self.current_level += 1
        if self.max_level == self.current_level:
            self.findChild(QPushButton, "add_level_" + str(object_id)).setEnabled(False)
        try:
            properties = {'name': name, 'level': level, 'power': power}
            self.add_levels_fc.addLevelItems(properties)
        except Exception as e:
            print(e)


class FlowContainerLevels(QListWidget):
    def __init__(self):
        super().__init__()
        # make it look like a normal scroll area
        self.viewport().setBackgroundRole(QPalette.Window)
        # display items from left to right, instead of top to bottom
        self.setFlow(self.LeftToRight)
        # wrap items that don't fit the width of the viewport
        # similar to self.setViewMode(self.IconMode)
        self.setWrapping(True)
        # prevent user repositioning
        self.setMovement(self.Static)
        # always re-layout items when the view is resized
        self.setResizeMode(self.Adjust)

        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setSpacing(3)

    def addLevelItems(self, properties):
        item = QListWidgetItem()
        item.setFlags(item.flags())
        self.addItem(item)
        btn = QPushButton("Level - " + properties['level'])
        btn.setFixedSize(80, 30)
        btn.setProperty('levels',
                        {'name': properties['name'], 'level': properties['level'], 'power': properties['power']})
        item.setSizeHint(QtCore.QSize(btn.width(), btn.height()))
        item.setSizeHint(btn.sizeHint())
        self.setItemWidget(item, btn)


class FlowContainerUpload(QListWidget):
    def __init__(self):
        super().__init__()
        # make it look like a normal scroll area
        self.viewport().setBackgroundRole(QPalette.Window)
        # display items from left to right, instead of top to bottom
        self.setFlow(self.LeftToRight)
        # wrap items that don't fit the width of the viewport
        # similar to self.setViewMode(self.IconMode)
        self.setWrapping(True)
        # prevent user repositioning
        self.setMovement(self.Static)
        # always re-layout items when the view is resized
        self.setResizeMode(self.Adjust)

        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setSpacing(3)

    def addUploadItems(self, properties):
        item = QListWidgetItem()
        item.setFlags(item.flags())
        self.addItem(item)
        if properties['type'] == "monster_upload":
            frame = UploadNormalMonsterItem(properties)
            frame.setObjectName("item_" + str(properties['id']))
            # print(frame.objectName())
            # item.setSizeHint(frame.sizeHint())
            item.setSizeHint(QtCore.QSize(frame.width(), frame.height()))
            self.setItemWidget(item, frame)
        elif properties['type'] == "boss_upload":
            frame = UploadBossMonsterItem(properties)
            frame.setObjectName("item_" + str(properties['id']))
            # print(frame.objectName())
            item.setSizeHint(frame.sizeHint())
            # item.setSizeHint(QtCore.QSize(frame.width(), frame.height()))
            self.setItemWidget(item, frame)
        elif properties['type'] == "scoutables_upload":
            frame = UploadScoutablesItem(properties)
            frame.setObjectName("item_" + str(properties['id']))
            # print(frame.objectName())
            # item.setSizeHint(frame.sizeHint())
            item.setSizeHint(QtCore.QSize(frame.width(), frame.height()))
            self.setItemWidget(item, frame)

    def removeUploadItem(self, index):
        item = self.takeItem(index)
        if item is not None:
            item.widget().deleteLater()


class ItemsUploadBox(QMainWindow, Ui_Upload_Window):
    upload_success = pyqtSignal(dict)

    def __init__(self, parent, sub_window_type):
        super(ItemsUploadBox, self).__init__(parent)
        print(sub_window_type)
        self.setupUi(self)
        self.upload_type = sub_window_type
        self.center()
        self.cancel_btn.clicked.connect(self.close)  # Connect button clicked signal to close() slot
        self.upload_btn.clicked.connect(self.upload_items)
        self.add_item_btn.clicked.connect(self.add_items)
        self.counter = 1
        self.img_path = None
        self.preview_name_list = None
        # Setting the Items list
        self.upload_items_fc = FlowContainerUpload()
        self.items_layout = QVBoxLayout(self)
        self.items_layout.addWidget(self.upload_items_fc)
        self.preview_frame.setLayout(self.items_layout)

    def getExistingPreviewNames(self):
        conn = create_connection("main.db")
        if self.upload_type == "monster_upload":
            return select_query_no_param(conn, get_all_normal_monster_names).fetchall()
        elif self.upload_type == "scoutables_upload":
            return select_query_no_param(conn, get_all_scoutables_names).fetchall()
        elif self.upload_type == "boss_upload":
            return select_query_no_param(conn, get_all_boss_monster_preview_names).fetchall()

    def upload_items(self):
        print("uploading...")
        self.preview_name_list = self.getExistingPreviewNames()
        self.preview_name_list = [names[0] for names in self.preview_name_list]
        if self.upload_type == "monster_upload":
            self.upload_console.appendPlainText("Initiating Normal Monster Upload...")
            print(self.upload_items_fc.count())  # Total items count
            items = []
            for i in range(self.upload_items_fc.count()):
                data = {}
                item = self.upload_items_fc.item(i)
                widget = self.upload_items_fc.itemWidget(item)
                index = extract_numbers_from_string(widget.objectName())
                data['directory_path'] = widget.findChild(QLineEdit, "img_path_" + str(index)).text()
                data['monster_name'] = widget.findChild(QLineEdit, "monster_name_" + str(index)).text()
                data['preview_image'] = widget.findChild(QLineEdit, "preview_image_" + str(index)).text()
                data['img_540p'] = widget.findChild(QLineEdit, "img_540p_" + str(index)).text()
                data['img_1080p'] = widget.findChild(QLineEdit, "img_1080p_" + str(index)).text()
                items.append(data)
                # print(data)
            flag = True
            for index, item in enumerate(items):
                # Validate all fields are not empty
                tmp_flag = False if item['directory_path'] == '' or item['monster_name'] == '' or item[
                    'preview_image'] == '' or item['img_540p'] == '' or item['img_1080p'] == '' else True
                if not tmp_flag:
                    flag = tmp_flag
                    self.upload_console.appendPlainText(f"\u2022 Some fields are empty in item {index + 1}")
                # Validate name is already not in use
                if item['monster_name'] in self.preview_name_list:
                    self.upload_console.appendPlainText(f"\u2022 Name already exist in item {index + 1}")
                    flag = False
                else:
                    self.preview_name_list.append(item['monster_name'])
                # Validate the image formats (png)
                tmp_list = 'preview_image', 'img_540p', 'img_1080p'
                for key in tmp_list:
                    if item[key] == '':
                        self.upload_console.appendPlainText(f"\u2022 {key} file is invalid in item {index + 1}")
                    elif not item[key].endswith('.png'):
                        self.upload_console.appendPlainText(f"\u2022 {item[key]} is not a png file")
                        flag = False
            if not flag:
                self.upload_console.appendPlainText("Validation Failed")
                return False
            # Uploading
            conn = create_connection("main.db")
            conn.execute("PRAGMA foreign_keys = ON")
            flag = True
            for index, item in enumerate(items):
                tmp_log = f"\u2022 Uploading {str(index + 1)} of {self.upload_items_fc.count()}..."
                self.upload_console.appendPlainText(tmp_log)
                self.upload_console.appendPlainText("-" * (len(tmp_log) + 3))
                # add images to db and get the row id
                monster_image = {"p_img": item['preview_image'], "540p": item['img_540p'], "1080p": item['img_1080p']}
                monster_image_id = execute_query(conn, add_monster_image_query, monster_image).lastrowid
                monster = {"m_name": item['monster_name'], "img_id": monster_image_id, "system": 1}
                # print(monster)
                result = execute_query(conn, add_normal_monster_query, monster)
                # Move images to path is everything is fine
                if result is not False:
                    self.moveImagesToPath(item, "normal_monsters")
                else:
                    flag = False
            if flag:
                conn.commit()
                self.upload_console.appendPlainText("Uploading completed")
                # Disable function buttons
                self.upload_btn.setEnabled(False)
                self.add_item_btn.setEnabled(False)
                self.upload_zip_btn.setEnabled(False)
                self.upload_success.emit({'type': self.upload_type, 'monster': items})
        elif self.upload_type == "scoutables_upload":
            self.upload_console.appendPlainText("Scoutables Upload")
            self.upload_console.appendPlainText("-" * (len("Scoutables Upload") + 5))
            print(self.upload_items_fc.count())  # Total items count
            items = []
            for i in range(self.upload_items_fc.count()):
                data = {}
                item = self.upload_items_fc.item(i)
                widget = self.upload_items_fc.itemWidget(item)
                index = extract_numbers_from_string(widget.objectName())
                data['directory_path'] = widget.findChild(QLineEdit, "img_path_" + str(index)).text()
                data['scoutables_name'] = widget.findChild(QLineEdit, "scoutables_name_" + str(index)).text()
                data['type'] = widget.findChild(QComboBox, "type_" + str(index)).currentText()
                data['preview_image'] = widget.findChild(QLineEdit, "preview_image_" + str(index)).text()
                data['img_540p'] = widget.findChild(QLineEdit, "img_540p_" + str(index)).text()
                data['img_1080p'] = widget.findChild(QLineEdit, "img_1080p_" + str(index)).text()
                items.append(data)
                # print(data)
            flag = True
            for index, item in enumerate(items):
                # Validate all fields are not empty
                tmp_flag = False if item['directory_path'] == '' or item['scoutables_name'] == '' or item[
                    'type'] == '' or \
                                    item['preview_image'] == '' or item['img_540p'] == '' or item[
                                        'img_1080p'] == '' else True
                if not tmp_flag:
                    flag = tmp_flag
                    self.upload_console.appendPlainText(f"\u2022 Some fields are empty in item {index + 1}")
                # Validate name is already not in use
                if item['scoutables_name'] in self.preview_name_list:
                    self.upload_console.appendPlainText(f"\u2022 Name already exist in item {index + 1}")
                    flag = False
                else:
                    self.preview_name_list.append(item['scoutables_name'])
                # Validate the image formats (png)
                tmp_list = 'preview_image', 'img_540p', 'img_1080p'
                for key in tmp_list:
                    if item[key] == '':
                        self.upload_console.appendPlainText(f"\u2022 {key} file is invalid in item {index + 1}")
                    elif not item[key].endswith('.png'):
                        self.upload_console.appendPlainText(f"\u2022 {item[key]} is not a png file")
                        flag = False
            if not flag:
                self.upload_console.appendPlainText("Validation Failed")
                return False
            # Uploading
            conn = create_connection("main.db")
            conn.execute("PRAGMA foreign_keys = ON")
            flag = True
            for index, item in enumerate(items):
                # add images to db and get the row id
                tmp_log = f"\u2022 Uploading {str(index + 1)} of {self.upload_items_fc.count()}..."
                self.upload_console.appendPlainText(tmp_log)
                self.upload_console.appendPlainText("-" * (len(tmp_log) + 3))
                scout_image = {"p_img": item['preview_image'], "540p": item['img_540p'], "1080p": item['img_1080p']}
                scout_image_id = execute_query(conn, add_monster_image_query, scout_image).lastrowid
                scout = {"s_name": item['scoutables_name'], "type": item['type'], "img_id": scout_image_id, "system": 1}
                # print(monster)
                result = execute_query(conn, add_scoutables_query, scout)
                # Move images to path is everything is fine
                if result is not False:
                    self.moveImagesToPath(item, "scoutables")
                else:
                    flag = False
            if flag:
                conn.commit()
                self.upload_console.appendPlainText("Uploading completed")
                # Disable function buttons
                self.upload_btn.setEnabled(False)
                self.add_item_btn.setEnabled(False)
                self.upload_zip_btn.setEnabled(False)
                self.upload_success.emit({'type': self.upload_type, 'scoutables': items})
        elif self.upload_type == "boss_upload":
            self.upload_console.appendPlainText("Initiating Boss Monster Upload...")
            print(self.upload_items_fc.count())  # Total items count
            items = []
            for i in range(self.upload_items_fc.count()):
                data = {}
                item = self.upload_items_fc.item(i)
                widget = self.upload_items_fc.itemWidget(item)
                index = extract_numbers_from_string(widget.objectName())
                data['directory_path'] = widget.findChild(QLineEdit, "img_path_" + str(index)).text()
                data['logic'] = widget.findChild(QComboBox, "select_logic_" + str(index)).currentText()
                data['category'] = widget.findChild(QComboBox, "select_category_" + str(index)).currentText()
                data['monster_name'] = widget.findChild(QLineEdit, "monster_name_" + str(index)).text()
                data['preview_name'] = widget.findChild(QLineEdit, "preview_name_" + str(index)).text()
                data['enable_map_scan'] = widget.findChild(QCheckBox, "enable_map_scan_" + str(index)).isChecked()
                data['preview_image'] = widget.findChild(QLineEdit, "preview_image_" + str(index)).text()
                data['img_540p'] = widget.findChild(QLineEdit, "img_540p_" + str(index)).text()
                data['img_1080p'] = widget.findChild(QLineEdit, "img_1080p_" + str(index)).text()
                # Access all the levels
                levels = []
                level_widget = widget.findChild(QWidget, "level_widget_" + str(index))
                child_widgets = level_widget.findChildren(QWidget)
                for wi in child_widgets:
                    if "levels_fc_" in wi.objectName():
                        for buttons in wi.findChildren(QPushButton):
                            levels.append(buttons.property('levels'))
                data['levels'] = levels
                items.append(data)

            flag = True
            for index, item in enumerate(items):
                # Validate all fields are not empty
                tmp_flag = False if item['directory_path'] == '' or item['logic'] == '' or item['category'] == '' or \
                                    item['monster_name'] == '' or item['preview_name'] == '' or item[
                                        'preview_image'] == '' or item['img_540p'] == '' or item[
                                        'img_1080p'] == '' else True
                if not tmp_flag:
                    flag = tmp_flag
                    self.upload_console.appendPlainText(f"\u2022 Some fields are empty in item {index + 1}")
                # Validate Levels
                check_level = set()
                check_power = set()
                for level in item['levels']:
                    if int(extract_numbers_from_string(item['logic'])) == 1 or int(
                            extract_numbers_from_string(item['logic'])) == 3:
                        if level['name'].lower() != item['monster_name'].lower():
                            self.upload_console.appendPlainText(
                                f"\u2022 Incorrect level name in item {index + 1}")
                            flag = False
                    if level.get('level') in check_level:
                        self.upload_console.appendPlainText(
                            f"\u2022 Duplicate level no. found in item {index + 1}")
                        flag = False
                    else:
                        check_level.add(level.get('level'))
                    if level.get('power') in check_power:
                        self.upload_console.appendPlainText(
                            f"\u2022 Duplicate power found in item {index + 1}")
                        flag = False
                    else:
                        check_power.add(level.get('power'))

                # Validate name is already not in use
                if item['preview_name'] in self.preview_name_list:
                    self.upload_console.appendPlainText(f"\u2022 Preview name already exist in item {index + 1}")
                    flag = False
                else:
                    self.preview_name_list.append(item['preview_name'])
                # Validate the image formats (png)
                tmp_list = 'preview_image', 'img_540p', 'img_1080p'
                for key in tmp_list:
                    if item[key] == '':
                        self.upload_console.appendPlainText(f"\u2022 {key} file is invalid in item {index + 1}")
                    elif not item[key].endswith('.png'):
                        self.upload_console.appendPlainText(f"\u2022 {item[key]} is not a png file")
                        flag = False
            if not flag:
                self.upload_console.appendPlainText("Validation Failed")
                return False

            # Saving to DB
            conn = create_connection("main.db")
            conn.execute("PRAGMA foreign_keys = ON")
            flag = True
            for index, item in enumerate(items):
                # add images to db and get the row id
                tmp_log = f"\u2022 Uploading {str(index + 1)} of {self.upload_items_fc.count()}..."
                self.upload_console.appendPlainText(tmp_log)
                self.upload_console.appendPlainText("-" * (len(tmp_log) + 3))
                boss_image = {"p_img": item['preview_image'], "540p": item['img_540p'], "1080p": item['img_1080p']}
                boss_image_id = execute_query(conn, add_monster_image_query, boss_image).lastrowid
                boss = {"p_name": item['preview_name'], "title": item['monster_name'], "category": item['category'],
                        "img_id": boss_image_id,
                        "logic_id": int(extract_numbers_from_string(item['logic'])), "system": 1,
                        "enable_map_scan": item["enable_map_scan"]}
                boss_id = execute_query(conn, add_boss_monster_query_upload, boss).lastrowid
                for level in item['levels']:
                    lev = {"boss_monster_id": boss_id, "level": level['level'], "name": level['name'],
                           "size": level['power']}
                    if not execute_query(conn, add_monster_level_query, lev):
                        flag = False
                # Move images to path is everything is fine
                if boss_id and flag:
                    self.moveImagesToPath(item, "monsters")
                elif not boss_id:
                    flag = False
            if flag:
                conn.commit()
                self.upload_console.appendPlainText("Uploading completed.Please restart the application to load the "
                                                    "new settings")
                # Disable function buttons
                self.upload_btn.setEnabled(False)
                self.add_item_btn.setEnabled(False)
                self.upload_zip_btn.setEnabled(False)
                self.upload_success.emit(
                    {'type': self.upload_type, 'boss': items, 'logic': int(extract_numbers_from_string(item['logic']))})

    def moveImagesToPath(self, data, dir_name):
        # file = Path(self.file_path)
        # src_dir = str(file.parent)
        directory = data['directory_path']
        if os.path.isfile(directory + "/preview/" + data['preview_image']):
            self.upload_console.appendPlainText(f"Moving {data['preview_image']} image to the application path...")
            shutil.copy2(directory + "/preview/" + data['preview_image'],
                         "images/evony/preview/" + data['preview_image'])
        else:
            self.upload_console.appendPlainText(f"{data['preview_image']} not found,hence skipping...")

        if os.path.isfile(directory + "/540p/" + data['img_540p']):
            self.upload_console.appendPlainText(f"Moving {data['img_540p']} image to the application path...")
            shutil.copy2(directory + "/540p/" + data['img_540p'],
                         "images/evony/540p/" + dir_name + "/" + data['img_540p'])
        else:
            self.upload_console.appendPlainText(f"{data['img_540p']} image not found,hence skipping...")

        if os.path.isfile(directory + "/1080p/" + data['img_1080p']):
            self.upload_console.appendPlainText(f"Moving {data['img_1080p']} image to the application path...")
            shutil.copy2(directory + "/1080p/" + data['img_1080p'],
                         "images/evony/1080p/" + dir_name + "/" + data['img_1080p'])
        else:
            self.upload_console.appendPlainText(f"{data['img_1080p']} image not found,hence skipping...")

    def center(self):
        parent_rect = self.parent().geometry()
        sub_rect = self.geometry()
        x = parent_rect.x() + (parent_rect.width() - sub_rect.width()) / 2
        y = parent_rect.y() + (parent_rect.height() - sub_rect.height()) / 2
        self.move(int(x), int(y))  # Move sub window to center position

    def add_items(self):
        try:
            properties = {'id': self.counter, 'type': self.upload_type, 'img_path': self.img_path}
            self.upload_items_fc.addUploadItems(properties)
            delete_item = self.preview_frame.findChild(QPushButton, "delete_item_" + str(self.counter))
            delete_item.clicked.connect(self.remove_item)
            select_directory = self.preview_frame.findChild(QPushButton, "select_directory_" + str(self.counter))
            select_directory.clicked.connect(self.choose_dir)
            img_path = self.preview_frame.findChild(QLineEdit, "img_path_" + str(self.counter))
            img_path.setText(self.img_path)
        except Exception as e:
            print(e)
        self.counter += 1

    def choose_dir(self):
        # create a file dialog object
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)

        # get the selected directory
        self.img_path = dialog.getExistingDirectory(self, "Select Directory")

        # Updating all directory path
        for i in range(self.upload_items_fc.count()):
            item = self.upload_items_fc.item(i)
            widget = self.upload_items_fc.itemWidget(item)
            index = extract_numbers_from_string(widget.objectName())
            # print(widget.objectName())
            widget.findChild(QLineEdit, "img_path_" + str(index)).setText(self.img_path)

    def remove_item(self):
        object_name = self.sender().objectName()
        # print(object_name)
        try:
            for i in range(self.upload_items_fc.count()):
                item = self.upload_items_fc.item(i)
                widget = self.upload_items_fc.itemWidget(item)
                # print(widget.objectName(), i)
                if widget is not None and widget.objectName() == "item_" + extract_numbers_from_string(
                        object_name):
                    self.upload_items_fc.removeUploadItem(i)
                    break
        except Exception as e:
            print(e)
