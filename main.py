#################################################################################
# Copyright (c) 2023, MwoNuZzz
# All rights reserved.
#
# This source code is licensed under the GNU General Public License as found in the
# LICENSE file in the root directory of this source tree.
#################################################################################

import sys
import os
import platform
from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtWidgets import QHeaderView
import faulthandler
# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from modules import *
import functools

from modules.ui.splash_screen_dialog import Ui_SplashScreen
from widgets import *
from ppadb.client import Client as AdbClient

os.environ["QT_FONT_DPI"] = "96"  # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None
all_boss_monsters = None
all_normal_monsters = None
all_scoutables = None
troops_training = []


# from . resources_rc import *

class DialogBoxNotification(QDialog, Ui_Dialog):
    def __init__(self, text, parent=None):
        super(DialogBoxNotification, self).__init__(parent)
        self.setupUi(self)
        self.dialog_content_label.setText(text)
        # self.show()


def openDialog(txt):
    d_box = DialogBoxNotification(txt)
    d_box.exec_()


# SPLASH SCREEN
class SplashScreen(QMainWindow):
    splash_progress = pyqtSignal(str, int)
    global troops_training
    global widgets

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)

        ## REMOVE TITLE BAR
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        ## DROP SHADOW EFFECT
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.ui.dropShadowFrame.setGraphicsEffect(self.shadow)
        ## SHOW ==> SPLASH WINDOW
        ########################################################################
        self.show()

        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.loadMainWindow)
        self.loading_timer.start(100)

    def loadMainWindow(self):
        self.main_window = MainWindow()
        self.splash_progress.connect(self.progress)
        self.splash_progress.emit("Setting up TaskEnforcerX", 0)

        # CONFIGURATION PAGE
        # ///////////////////////////////////////////////////////////////
        for index in range(self.main_window.total_emulator):
            emu_name = self.main_window.findChild(QLineEdit, f"emu_name_{str(index + 1)}")
            emu_port = self.main_window.findChild(QLineEdit, f"emu_port_{str(index + 1)}")
            emu_name.textChanged.connect(self.main_window.emulatorNameChange)
            emu_port.textChanged.connect(self.main_window.emulatorPortChange)

        self.splash_progress.emit("Initializing and configuring settings for each emulator instance...", 5)
        # EMULATOR START & RUN and Troop Training Queue Button
        for index in range(self.main_window.total_emulator):
            emu_start = self.main_window.findChild(QPushButton, "emu_start_" + str(index + 1))
            emu_run = self.main_window.findChild(QPushButton, "emu_run_" + str(index + 1))
            emu_start.clicked.connect(self.main_window.startAndStopEmulator)
            emu_run.clicked.connect(self.main_window.invokeStartAndStop)

        self.splash_progress.emit("Configuring additional settings for each emulator instance...", 10)
        # Troop Training Queue Button
        widgets.add_queue_1.clicked.connect(lambda: self.main_window.addQueueTraining(1))
        widgets.add_queue_2.clicked.connect(lambda: self.main_window.addQueueTraining(2))
        widgets.add_queue_3.clicked.connect(lambda: self.main_window.addQueueTraining(3))
        widgets.add_queue_4.clicked.connect(lambda: self.main_window.addQueueTraining(4))
        widgets.add_queue_5.clicked.connect(lambda: self.main_window.addQueueTraining(5))
        widgets.add_queue_6.clicked.connect(lambda: self.main_window.addQueueTraining(6))
        widgets.add_queue_7.clicked.connect(lambda: self.main_window.addQueueTraining(7))
        widgets.add_queue_8.clicked.connect(lambda: self.main_window.addQueueTraining(8))
        widgets.add_queue_9.clicked.connect(lambda: self.main_window.addQueueTraining(9))
        widgets.add_queue_10.clicked.connect(lambda: self.main_window.addQueueTraining(10))

        # Settings Upload Button
        widgets.upload_normal_monsters.clicked.connect(lambda: self.main_window.openUploadMenu("monster_upload"))
        widgets.upload_boss_monsters.clicked.connect(lambda: self.main_window.openUploadMenu("boss_upload"))
        widgets.upload_scoutables.clicked.connect(lambda: self.main_window.openUploadMenu("scoutables_upload"))

        # upload XML
        # xml = MonsterXML("test/XML UP/Achelois.xml")
        # xml.readMonsterXML()
        # xml.processAndSaveToDatabase()
        self.splash_progress.emit("Setting up boss interface controls...", 15)
        # should exec loadBossMonsterSettingsWidget() first to load values in the global variable all_boss_monsters
        self.main_window.loadBossMonsterSettingsWidget()
        self.main_window.loadNormalMonsterSettingsWidget()
        self.main_window.loadScoutablesSettingsWidget()
        self.main_window.loadMonsterControlsJoinRally()
        self.splash_progress.emit("Setting up world map controls...", 20)
        self.main_window.loadWorldMapScanUIControls()
        self.main_window.loadBossMonsterControlsScanMap()
        self.main_window.loadNormalMonsterControlsScanMap()
        self.main_window.loadScoutablesControlsScanMap()
        self.main_window.loadBlackMarketControls()
        self.main_window.setUpMoreActivitiesFrames()
        # Init Troops training total values for all the active emulators
        for index in range(self.main_window.total_emulator):
            troops_training.append({'food': 0, 'wood': 0, 'stone': 0, 'ore': 0, 'gold': 0})

        # Profile Settings
        self.main_window.loadProfileNames()
        # self.main_window.profile_thread = []
        for index in range(self.main_window.total_emulator):
            self.splash_progress.emit("Preparing emulator profiles...", (21 + index))

            emu_profile = self.main_window.findChild(QComboBox, "emu_profile_" + str(index + 1))
            emu_profile.currentIndexChanged.connect(lambda: Profile.changeProfile(self.main_window))

            emu_mode = self.main_window.findChild(QComboBox, f"emu_mode_{str(index + 1)}")
            emu_mode.currentIndexChanged.connect(lambda: Profile.changeMode(self.main_window))

            emulator_profile = self.main_window.findChild(QComboBox, "comboBoxProfile_" + str(index + 1))
            emulator_profile.currentIndexChanged.connect(lambda: Profile.changeProfile(self.main_window))

            emulator_mode = self.main_window.findChild(QComboBox, f"comboBoxMode_{str(index + 1)}")
            # emulator_mode.currentIndexChanged.connect(lambda: Profile.updateModeToDB(self.main_window))
            emulator_mode.currentIndexChanged.connect(lambda: Profile.changeMode(self.main_window))

            self.main_window.findChild(QWidget, "profile_edit_widget_" + str(index + 1)).hide()
            self.main_window.findChild(QPushButton, "create_profile_btn_" + str(index + 1)).clicked.connect(
                lambda: Profile.createNewProfile(self.main_window))
            load_profiles_combo = self.main_window.findChild(QComboBox, "load_profile_combo_" + str(index + 1))
            load_profiles_combo.currentIndexChanged.connect(lambda: Profile.changeLoadProfile(self.main_window))
            # load_profiles_combo.currentIndexChanged.connect(lambda: Profile.changeProfile(self.main_window))
            save_profile = self.main_window.findChild(QPushButton, "save_profile_btn_" + str(index + 1))
            save_profile.clicked.connect(lambda: Profile.saveProfile(self.main_window))
            delete_profile = self.main_window.findChild(QPushButton, "delete_profile_btn_" + str(index + 1))
            delete_profile.clicked.connect(lambda: Profile.deleteProfile(self.main_window))
            copy_profile_btn = self.main_window.findChild(QPushButton, "copy_profile_btn_" + str(index + 1))
            copy_profile_btn.clicked.connect(lambda: Profile.copyProfile(self.main_window))
            # self.main_window.profile_thread.append(False)
        self.splash_progress.emit("Loading user profiles...", 50)
        self.main_window.loadEmulatorProfiles(self.splash_progress)
        self.splash_progress.emit("Finalizing setup...", 99)
        self.splash_progress.emit("Finalizing setup...", 100)

    def progress(self, text, counter):
        # SET VALUE TO PROGRESS BAR
        self.ui.progressBar.setValue(counter)
        self.ui.label_loading.setText(text)
        # CLOSE SPLASH SCREEN
        if counter >= 100:
            # STOP TIMER
            self.loading_timer.stop()
            # SHOW MAIN WINDOW
            self.main_window.show()
            # CLOSE SPLASH SCREEN
            self.close()


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui
        global troops_training
        self.all_profiles = None
        self.total_emulator = 10

        # THREAD INIT AND STARTING ADB SERVER
        self.thread = {}
        self.thread[0] = ConfigurationThread(parent=None)
        self.thread[0].start()
        self.thread[0].emulator_console.connect(self.logEmulatorConsole)

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "TaskEnforcerX"
        description = "TaskEnforcerX"
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        useCustomTheme = False
        themeFile = "themes\py_dracula_light.qss"

        # SET THEME AND HACKS
        if useCustomTheme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, themeFile, True)

            # SET HACKS
            AppFunctions.setThemeHack(self)

        # EXTRA RIGHT BOX
        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)

        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)
        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////

        # LEFT MENUS
        widgets.btn_about.clicked.connect(self.menuButtonClick)
        widgets.btn_config.clicked.connect(self.menuButtonClick)
        widgets.btn_collective.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_1.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_2.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_3.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_4.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_5.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_6.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_7.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_8.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_9.clicked.connect(self.menuButtonClick)
        widgets.btn_emu_10.clicked.connect(self.menuButtonClick)
        widgets.btn_settings.clicked.connect(self.menuButtonClick)
        widgets.ico_btn_support.clicked.connect(self.menuButtonClick)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        widgets.stackedWidget.setCurrentWidget(widgets.config)
        widgets.btn_config.setStyleSheet(UIFunctions.selectMenu(widgets.btn_config.styleSheet()))

    # Load Profiles
    def loadProfileNames(self):
        self.all_profiles = getAllProfiles()
        for index in range(self.total_emulator):
            load_profiles_combo = self.findChild(QComboBox, f"load_profile_combo_{str(index + 1)}")
            combo_box_profile = self.findChild(QComboBox, f"comboBoxProfile_{str(index + 1)}")
            emu_profile = self.findChild(QComboBox, f"emu_profile_{str(index + 1)}")
            load_profiles_combo.clear()
            combo_box_profile.clear()
            emu_profile.clear()
            for profile in self.all_profiles:
                load_profiles_combo.addItem(profile['name'])
                combo_box_profile.addItem(profile['name'])
                emu_profile.addItem(profile['name'])

    # Update Uploaded Settings items
    def uploadSuccess(self, properties):
        # Reload Settings and controls
        # print(properties)
        try:
            if properties['type'] == "boss_upload":
                monsters = properties['boss']
                for monster in monsters:
                    prev_img = "images/evony/preview/" + monster['preview_image']
                    if properties['logic'] == 1:
                        self.monster_list_logic1_fc.addMonsters(
                            {"name": monster['preview_name'], "img_path": prev_img, "system": True})
                        delete_item = self.monster_list_logic1_fc.findChild(QPushButton,
                                                                            generateObjectName(
                                                                                monster["preview_name"]) + "delete")
                        delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.monster_list_logic1_fc))
                    elif properties['logic'] == 2:
                        self.monster_list_logic2_fc.addMonsters(
                            {"name": monster['preview_name'], "img_path": prev_img, "system": True})
                        delete_item = self.monster_list_logic2_fc.findChild(QPushButton,
                                                                            generateObjectName(
                                                                                monster["preview_name"]) + "delete")
                        delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.monster_list_logic2_fc))
                    elif properties['logic'] == 3:
                        self.monster_list_logic3_fc.addMonsters(
                            {"name": monster['preview_name'], "img_path": prev_img, "system": True})
                        delete_item = self.monster_list_logic3_fc.findChild(QPushButton,
                                                                            generateObjectName(
                                                                                monster["preview_name"]) + "delete")
                        delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.monster_list_logic3_fc))

            elif properties['type'] == "monster_upload":
                monsters = properties['monster']
                for monster in monsters:
                    prev_img = "images/evony/preview/" + monster['preview_image']
                    self.monster_list_fc.addMonsters(
                        {"name": monster['monster_name'], "img_path": prev_img, "system": True})
                    delete_item = self.monster_list_fc.findChild(QPushButton,
                                                                 generateObjectName(monster["monster_name"]) + "delete")
                    delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.monster_list_fc))
            elif properties['type'] == "scoutables_upload":
                scoutables = properties['scoutables']
                for scoutable in scoutables:
                    prev_img = "images/evony/preview/" + scoutable['preview_image']
                    self.scoutables_list_fc.addMonsters({"name": scoutable['scoutables_name'], "img_path": prev_img,
                                                         "system": True})
                    delete_item = self.scoutables_list_fc.findChild(QPushButton,
                                                                    generateObjectName(
                                                                        scoutable["scoutables_name"]) + "delete")
                    delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.scoutables_list_fc))
        except Exception as e:
            print(e)

    def openUploadMenu(self, sub_window_type):
        self.sub_window = ItemsUploadBox(self, sub_window_type)
        self.sub_window.show()
        self.sub_window.upload_success.connect(self.uploadSuccess)

    # LOAD WORLD MAP SCAN NAV BUTTON CONTROLS
    def loadWorldMapScanUIControls(self):
        for index in range(1, self.total_emulator + 1):
            # World Map Scan Page Buttons
            map_scan_btn_widgets = self.findChild(QWidget, "map_scan_btn_widgets_" + str(index))
            nav_buttons = map_scan_btn_widgets.findChildren(QPushButton)
            for btn_index, button in enumerate(nav_buttons):
                if btn_index == 0:
                    button.setStyleSheet("background-color: rgb(161, 110, 235);border-radius: 10px;")
                button.clicked.connect(self.MapScanButtonClick)
            # World Map Scan Page Navigation Buttons
            next_page = self.findChild(QPushButton, "map_scan_next_" + str(index))
            previous_page = self.findChild(QPushButton, "map_scan_previous_" + str(index))
            next_page.clicked.connect(lambda: self.MapScanNavButtonClick(True))
            previous_page.clicked.connect(lambda: self.MapScanNavButtonClick(False))

    def MapScanNavButtonClick(self, flag):
        sender = self.sender()
        index = extract_numbers_from_string(sender.objectName())
        stacked_widget = self.findChild(QStackedWidget, "map_scan_stack_" + str(index))
        current_index = stacked_widget.currentIndex()
        # Flag checks whether the button pressed is next or previous
        if flag:
            new_index = current_index + 1 if current_index != 3 else 0
        else:
            new_index = current_index - 1 if current_index != 0 else 3
        stacked_widget.setCurrentIndex(new_index)
        new_page_id = stacked_widget.currentWidget().objectName()
        map_scan_btn_widgets = self.findChild(QWidget, "map_scan_btn_widgets_" + str(index))
        nav_buttons = map_scan_btn_widgets.findChildren(QPushButton)
        for button in nav_buttons:
            if button.objectName() == "btn_" + new_page_id:
                button.setStyleSheet("background-color: rgb(161, 110, 235);border-radius: 10px;")
            else:
                button.setStyleSheet("background-color: rgb(240, 105, 183);border-radius: 10px;")

    def MapScanButtonClick(self):
        sender = self.sender()
        btn_obj_id = sender.objectName()
        index = extract_numbers_from_string(btn_obj_id)
        # print("Button Clicked:", btn_obj_id)  # Button Clicked: btn_scan_rss_1
        stacked_widget = self.findChild(QStackedWidget, "map_scan_stack_" + str(index))
        new_index = stacked_widget.indexOf(self.findChild(QWidget, btn_obj_id[len("btn_"):]))
        stacked_widget.setCurrentIndex(new_index)
        # Update Selection Color
        map_scan_btn_widgets = self.findChild(QWidget, "map_scan_btn_widgets_" + str(index))
        nav_buttons = map_scan_btn_widgets.findChildren(QPushButton)
        for button in nav_buttons:
            if button.objectName() == btn_obj_id:
                button.setStyleSheet("background-color: rgb(161, 110, 235);border-radius: 10px;")
            else:
                button.setStyleSheet("background-color: rgb(240, 105, 183);border-radius: 10px;")

    def addQueueTraining(self, index):
        global troops_training
        print(index)
        table = self.findChild(QTableWidget, "troop_queue_table_" + str(index))
        troop_type = self.findChild(QComboBox, "troop_type_" + str(index))
        troop_tier = self.findChild(QComboBox, "troop_tier_" + str(index))
        train_times = self.findChild(QLineEdit, "batches_" + str(index))
        total_troop_per_batch = self.findChild(QLineEdit, "total_batches_" + str(index))
        row_position = table.rowCount() - 1
        if troop_type.currentText() == "" or troop_tier.currentText() == "" or train_times.text() == "":
            openDialog("Some Fields are not selected")
        else:
            try:
                conn = create_connection("main.db")
                tier_info = select_query(conn, get_troop_tier_info, {'troop_type': troop_type.currentText(),
                                                                     'troop_tier': troop_tier.currentText()}).fetchone()
                print(tier_info)  # ('Siege', 'T5', 0, 160, 420, 160, 0)
                # Inserting Rows
                table.insertRow(row_position)
                table.setItem(row_position, 0, QTableWidgetItem(troop_type.currentText()))
                table.setItem(row_position, 1, QTableWidgetItem(troop_tier.currentText()))
                table.setItem(row_position, 2, QTableWidgetItem(train_times.text()))
                if total_troop_per_batch.text() == "":
                    for i in range(3, 9):
                        table.setItem(row_position, i, QTableWidgetItem("NIL"))
                else:
                    food = tier_info[2] * int(total_troop_per_batch.text()) * int(train_times.text())
                    wood = tier_info[3] * int(total_troop_per_batch.text()) * int(train_times.text())
                    stone = tier_info[4] * int(total_troop_per_batch.text()) * int(train_times.text())
                    ore = tier_info[5] * int(total_troop_per_batch.text()) * int(train_times.text())
                    gold = tier_info[6] * int(total_troop_per_batch.text()) * int(train_times.text())
                    table.setItem(row_position, 3,
                                  QTableWidgetItem(str(int(train_times.text()) * int(total_troop_per_batch.text()))))
                    table.setItem(row_position, 4, QTableWidgetItem(format_with_prefix(food)))
                    table.setItem(row_position, 5, QTableWidgetItem(format_with_prefix(wood)))
                    table.setItem(row_position, 6, QTableWidgetItem(format_with_prefix(stone)))
                    table.setItem(row_position, 7, QTableWidgetItem(format_with_prefix(ore)))
                    table.setItem(row_position, 8, QTableWidgetItem(format_with_prefix(gold)))

                    # Updating Footer Values
                    troops_training[index - 1]['food'] += food
                    troops_training[index - 1]['wood'] += wood
                    troops_training[index - 1]['stone'] += stone
                    troops_training[index - 1]['ore'] += ore
                    troops_training[index - 1]['gold'] += gold
                    bold_font = QFont()
                    bold_font.setBold(True)
                    # FOOD
                    table.setItem(row_position + 1, 4,
                                  QTableWidgetItem(format_with_prefix(troops_training[index - 1]['food'])))
                    table.item(row_position + 1, 4).setFont(bold_font)
                    # WOOD
                    table.setItem(row_position + 1, 5,
                                  QTableWidgetItem(format_with_prefix(troops_training[index - 1]['wood'])))
                    table.item(row_position + 1, 5).setFont(bold_font)
                    # STONE
                    table.setItem(row_position + 1, 6,
                                  QTableWidgetItem(format_with_prefix(troops_training[index - 1]['stone'])))
                    table.item(row_position + 1, 6).setFont(bold_font)
                    # ORE
                    table.setItem(row_position + 1, 7,
                                  QTableWidgetItem(format_with_prefix(troops_training[index - 1]['ore'])))
                    table.item(row_position + 1, 7).setFont(bold_font)
                    # GOLD
                    table.setItem(row_position + 1, 8,
                                  QTableWidgetItem(format_with_prefix(troops_training[index - 1]['gold'])))
                    table.item(row_position + 1, 8).setFont(bold_font)

                # Adding Action Column
                delete_button = QPushButton()
                delete_button.setObjectName(u"delete_button_" + str(row_position) + str(index))
                icon = QIcon()
                icon.addFile(u":/extra icons/images/extra icons/delete-red.png", QSize(), QIcon.Normal, QIcon.Off)
                delete_button.setIcon(icon)
                table.setCellWidget(row_position, 9, delete_button)
                delete_button.clicked.connect(lambda checked, row=row_position: self.removeQueueTraining(index))
                # Reset Fields
                troop_type.setCurrentIndex(-1)
                troop_tier.setCurrentIndex(-1)
                train_times.clear()

            except Exception as e:
                print(e)

    def updateTroopsTrainingQueue(self):
        table_index = self.sender().index
        args = self.sender().args
        row_index = args['index']
        table = self.findChild(QTableWidget, "troop_queue_table_" + str(table_index))
        if args['type'] == "remove":
            try:
                delete_button = table.cellWidget(row_index, 9)
                print(table.item(row_index, 0).text() + " ---- " + table.item(row_index, 1).text())
                delete_button.click()
            except Exception as e:
                print(e)
        elif args['type'] == "update":
            try:
                print("Updating train times column")
                if table.item(row_index, 4).text() != "NIL":
                    troop_type = table.item(row_index, 0).text()
                    troop_tier = table.item(row_index, 1).text()
                    current_train_times = int(table.item(row_index, 2).text())
                    total_troops = int(table.item(row_index, 3).text())
                    total_row = table.rowCount() - 1
                    troops_per_batch = total_troops / current_train_times
                    conn = create_connection("main.db")
                    tier_info = select_query(conn, get_troop_tier_info, {'troop_type': troop_type,
                                                                         'troop_tier': troop_tier}).fetchone()
                    print(tier_info)  # ('Siege', 'T5', 0, 160, 420, 160, 0)
                    # Updating current row
                    food = int(tier_info[2] * troops_per_batch * args['new_value'])
                    wood = int(tier_info[3] * troops_per_batch * args['new_value'])
                    stone = int(tier_info[4] * troops_per_batch * args['new_value'])
                    ore = int(tier_info[5] * troops_per_batch * args['new_value'])
                    gold = int(tier_info[6] * troops_per_batch * args['new_value'])
                    table.setItem(row_index, 3, QTableWidgetItem(str(int(args['new_value'] * troops_per_batch))))
                    table.setItem(row_index, 4, QTableWidgetItem(format_with_prefix(food)))
                    table.setItem(row_index, 5, QTableWidgetItem(format_with_prefix(wood)))
                    table.setItem(row_index, 6, QTableWidgetItem(format_with_prefix(stone)))
                    table.setItem(row_index, 7, QTableWidgetItem(format_with_prefix(ore)))
                    table.setItem(row_index, 8, QTableWidgetItem(format_with_prefix(gold)))

                    # Update Total row
                    food = tier_info[2] * troops_per_batch * (current_train_times - args['new_value'])
                    wood = tier_info[3] * troops_per_batch * (current_train_times - args['new_value'])
                    stone = tier_info[4] * troops_per_batch * (current_train_times - args['new_value'])
                    ore = tier_info[5] * troops_per_batch * (current_train_times - args['new_value'])
                    gold = tier_info[6] * troops_per_batch * (current_train_times - args['new_value'])
                    troops_training[table_index - 1]['food'] -= food
                    troops_training[table_index - 1]['wood'] -= wood
                    troops_training[table_index - 1]['stone'] -= stone
                    troops_training[table_index - 1]['ore'] -= ore
                    troops_training[table_index - 1]['gold'] -= gold

                    bold_font = QFont()
                    bold_font.setBold(True)
                    table.setItem(total_row, 4,
                                  QTableWidgetItem(format_with_prefix(int(troops_training[table_index - 1]['food']))))
                    table.item(total_row, 4).setFont(bold_font)
                    table.setItem(total_row, 5,
                                  QTableWidgetItem(format_with_prefix(int(troops_training[table_index - 1]['wood']))))
                    table.item(total_row, 5).setFont(bold_font)
                    table.setItem(total_row, 6,
                                  QTableWidgetItem(format_with_prefix(int(troops_training[table_index - 1]['stone']))))
                    table.item(total_row, 6).setFont(bold_font)
                    table.setItem(total_row, 7,
                                  QTableWidgetItem(format_with_prefix(int(troops_training[table_index - 1]['ore']))))
                    table.item(total_row, 7).setFont(bold_font)
                    table.setItem(total_row, 8,
                                  QTableWidgetItem(format_with_prefix(int(troops_training[table_index - 1]['gold']))))
                    table.item(total_row, 8).setFont(bold_font)
                # Update Total times
                table.setItem(row_index, 2, QTableWidgetItem(str(args['new_value'])))
            except Exception as e:
                print(e)

    def removeQueueTraining(self, index):
        global troops_training
        try:
            table = self.findChild(QTableWidget, "troop_queue_table_" + str(index))
            button = self.sender()
            row = table.indexAt(button.pos()).row()
            troop_type = table.item(row, 0).text()
            troop_tier = table.item(row, 1).text()
            total_troops = table.item(row, 3).text()
            total_row = table.rowCount() - 1

            # Fetch rss values with tier and troop type to minus it from the total
            conn = create_connection("main.db")
            tier_info = select_query(conn, get_troop_tier_info, {'troop_type': troop_type,
                                                                 'troop_tier': troop_tier}).fetchone()
            food = tier_info[2] * int(total_troops)
            wood = tier_info[3] * int(total_troops)
            stone = tier_info[4] * int(total_troops)
            ore = tier_info[5] * int(total_troops)
            gold = tier_info[6] * int(total_troops)

            # Update Total Values
            troops_training[index - 1]['food'] -= food
            troops_training[index - 1]['wood'] -= wood
            troops_training[index - 1]['stone'] -= stone
            troops_training[index - 1]['ore'] -= ore
            troops_training[index - 1]['gold'] -= gold

            bold_font = QFont()
            bold_font.setBold(True)
            table.setItem(total_row, 4, QTableWidgetItem(format_with_prefix(troops_training[index - 1]['food'])))
            table.item(total_row, 4).setFont(bold_font)
            table.setItem(total_row, 5, QTableWidgetItem(format_with_prefix(troops_training[index - 1]['wood'])))
            table.item(total_row, 5).setFont(bold_font)
            table.setItem(total_row, 6, QTableWidgetItem(format_with_prefix(troops_training[index - 1]['stone'])))
            table.item(total_row, 6).setFont(bold_font)
            table.setItem(total_row, 7, QTableWidgetItem(format_with_prefix(troops_training[index - 1]['ore'])))
            table.item(total_row, 7).setFont(bold_font)
            table.setItem(total_row, 8, QTableWidgetItem(format_with_prefix(troops_training[index - 1]['gold'])))
            table.item(total_row, 8).setFont(bold_font)

        except Exception as e:
            print(e)
        table.removeRow(row)

    # LOAD EMULATOR PROFILE
    def loadEmulatorProfiles(self, splash_progress):
        conn = create_connection("main.db")
        self.all_emulator_profiles = select_query_no_param(conn, get_all_emulator_profiles).fetchall()
        # print(self.all_emulator_profiles) #(1, 'Rexy', 5685, 'Join Rally', '')
        loading_progress = 50
        for index, profile in enumerate(self.all_emulator_profiles):
            loading_progress += index
            splash_progress.emit("Loading user profiles...", loading_progress)
            # load configuration fields
            self.findChild(QLineEdit, f"emu_name_{str(profile[0])}").setText(profile[1])
            self.findChild(QLineEdit, f"emu_port_{str(profile[0])}").setText(str(profile[2]))
            self.findChild(QComboBox, f"comboBoxMode_{str(profile[0])}").setCurrentText(str(profile[3]))
            check_profile_exist = [values['name'] for values in self.all_profiles if values['name'] == profile[4]]
            if len(check_profile_exist) != 0:
                self.findChild(QComboBox, f"emu_profile_{str(profile[0])}").setCurrentText(str(profile[4]))

    # Load Monster Logics in settings
    # ///////////////////////////////////////////////////////////////
    def loadBlackMarketControls(self):
        global widgets
        for emulator_index in range(self.total_emulator):
            buy_items_frame = self.findChild(QFrame, "buy_items_frame_" + str(emulator_index + 1))
            items = buy_items_frame.findChildren(QCheckBox)
            for item in items:
                if item.objectName().startswith("item_"):
                    # print(item.text())
                    object_name = item.objectName().replace("item_", "rebuy_")
                    layout = QHBoxLayout()
                    layout.setContentsMargins(0, 0, 0, 0)
                    toggle = PyToggle(tooltip="Rebuy")
                    toggle.setObjectName(object_name)
                    layout.addWidget(toggle)
                    toggle_box = self.findChild(QWidget, item.objectName().replace("item_", "toggle_"))
                    toggle_box.setLayout(layout)

    def loadBossMonsterSettingsWidget(self):
        global widgets
        global all_boss_monsters
        self.monster_list_logic1_fc = FlowContainer()
        self.monster_list_logic2_fc = FlowContainer()
        self.monster_list_logic3_fc = FlowContainer()
        logic1_layout = QVBoxLayout(self)
        logic2_layout = QVBoxLayout(self)
        logic3_layout = QVBoxLayout(self)
        logic1_layout.addWidget(self.monster_list_logic1_fc)
        logic2_layout.addWidget(self.monster_list_logic2_fc)
        logic3_layout.addWidget(self.monster_list_logic3_fc)
        all_boss_monsters = getAllBossMonsterData()
        for monster in all_boss_monsters:
            prev_img = "images/evony/preview/" + monster['preview_image']
            if monster['monster_logic_id'] == 1:
                self.monster_list_logic1_fc.addMonsters({"name": monster['preview_name'], "img_path": prev_img,
                                                         "system": True if monster["system"] == 1 else False})
                delete_item = self.monster_list_logic1_fc.findChild(QPushButton,
                                                                    generateObjectName(
                                                                        monster['preview_name']) + "delete")
                delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.monster_list_logic1_fc))
            elif monster['monster_logic_id'] == 2:
                self.monster_list_logic2_fc.addMonsters({"name": monster['preview_name'], "img_path": prev_img,
                                                         "system": True if monster["system"] == 1 else False})
                delete_item = self.monster_list_logic2_fc.findChild(QPushButton,
                                                                    generateObjectName(
                                                                        monster['preview_name']) + "delete")
                delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.monster_list_logic2_fc))
            elif monster['monster_logic_id'] == 3:
                self.monster_list_logic3_fc.addMonsters({"name": monster['preview_name'], "img_path": prev_img,
                                                         "system": True if monster["system"] == 1 else False})
                delete_item = self.monster_list_logic3_fc.findChild(QPushButton,
                                                                    generateObjectName(
                                                                        monster['preview_name']) + "delete")
                delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.monster_list_logic3_fc))
        widgets.logic1_frame.setLayout(logic1_layout)
        widgets.logic2_frame.setLayout(logic2_layout)
        widgets.logic3_frame.setLayout(logic3_layout)

    def loadScoutablesSettingsWidget(self):
        global all_scoutables
        global widgets
        self.scoutables_list_fc = FlowContainer()
        scoutables_layout = QVBoxLayout(self)
        scoutables_layout.addWidget(self.scoutables_list_fc)
        all_scoutables = getAllScoutablesData()
        # print(all_scoutables)
        for scoutable in all_scoutables:
            # print(scoutable["name"])
            prev_img = "images/evony/preview/" + scoutable['preview_image']
            self.scoutables_list_fc.addMonsters({"name": scoutable['name'], "img_path": prev_img,
                                                 "system": True if scoutable["system"] == 1 else False})
            delete_item = self.scoutables_list_fc.findChild(QPushButton,
                                                            generateObjectName(scoutable["name"]) + "delete")
            delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.scoutables_list_fc))
        widgets.scoutables_frame.setLayout(scoutables_layout)

    def remove_item_from_settings(self, flow_container):
        print(self.sender().objectName())
        delete_btn_object = self.sender().objectName()
        print(flow_container.parent().objectName())
        if flow_container.parent().objectName() == "scoutables_frame":
            global all_scoutables
            all_scoutables = getAllScoutablesData()
            scoutables = [scoutable for scoutable in all_scoutables if
                          generateObjectName(scoutable['name']) + "delete" == self.sender().objectName()][0]
            # print(scoutables)
            conn = create_connection("main.db")
            execute_query(conn, delete_monster_images_with_id, {'img_id': scoutables['img_id']})
            execute_query(conn, delete_scoutables_with_id, {'id': scoutables['id']})
            conn.commit()
            try:
                for i in range(flow_container.count()):
                    item = flow_container.item(i)
                    widget = flow_container.itemWidget(item)
                    # print(widget.objectName())
                    delete_btn = widget.findChild(QPushButton, delete_btn_object)
                    if delete_btn is not None:
                        if flow_container.takeItem(i) is not None:
                            # item.widget().deleteLater()
                            break
            except Exception as e:
                print(e)
        elif flow_container.parent().objectName() == "normal_monster_frame":
            global all_normal_monsters
            all_normal_monsters = getAllNormalMonsterData()
            monsters = [monster for monster in all_normal_monsters if
                        generateObjectName(monster['name']) + "delete" == self.sender().objectName()][0]
            conn = create_connection("main.db")
            execute_query(conn, delete_monster_images_with_id, {'img_id': monsters['img_id']})
            execute_query(conn, delete_normal_monster_with_id, {'id': monsters['id']})
            conn.commit()
            try:
                for i in range(flow_container.count()):
                    item = flow_container.item(i)
                    widget = flow_container.itemWidget(item)
                    # print(widget.objectName())
                    delete_btn = widget.findChild(QPushButton, delete_btn_object)
                    if delete_btn is not None:
                        if flow_container.takeItem(i) is not None:
                            # item.widget().deleteLater()
                            break
            except Exception as e:
                print(e)
        elif flow_container.parent().objectName() == "logic1_frame" or flow_container.parent().objectName() == "logic2_frame" or flow_container.parent().objectName() == "logic3_frame":
            global all_boss_monsters
            all_boss_monsters = getAllBossMonsterData()
            monsters = [monster for monster in all_boss_monsters if
                        generateObjectName(monster['preview_name']) + "delete" == self.sender().objectName()][0]
            conn = create_connection("main.db")
            execute_query(conn, delete_monster_images_with_id, {'img_id': monsters['img_id']})
            execute_query(conn, delete_boss_monster_with_id, {'id': monsters['id']})
            execute_query(conn, delete_boss_monster_levels_with_boss_monster_id, {'id': monsters['id']})
            conn.commit()
            try:
                for i in range(flow_container.count()):
                    item = flow_container.item(i)
                    widget = flow_container.itemWidget(item)
                    # print(widget.objectName())
                    delete_btn = widget.findChild(QPushButton, delete_btn_object)
                    if delete_btn is not None:
                        if flow_container.takeItem(i) is not None:
                            # item.widget().deleteLater()
                            break
            except Exception as e:
                print(e)

    def loadNormalMonsterSettingsWidget(self):
        global all_normal_monsters
        global widgets
        self.monster_list_fc = FlowContainer()
        monster_layout = QVBoxLayout(self)
        monster_layout.addWidget(self.monster_list_fc)
        all_normal_monsters = getAllNormalMonsterData()
        # print(all_normal_monsters)
        for monster in all_normal_monsters:
            prev_img = "images/evony/preview/" + monster['preview_image']
            self.monster_list_fc.addMonsters(
                {"name": monster['name'], "img_path": prev_img, "system": True if monster["system"] == 1 else False})
            delete_item = self.monster_list_fc.findChild(QPushButton,
                                                         generateObjectName(monster["name"]) + "delete")
            delete_item.clicked.connect(lambda: self.remove_item_from_settings(self.monster_list_fc))
        widgets.normal_monster_frame.setLayout(monster_layout)

    def loadScoutablesControlsScanMap(self):
        global widgets
        global all_scoutables
        for emulator_index in range(self.total_emulator):
            scoutables_layout = FlowLayout()
            for scoutable in all_scoutables:
                # print(scoutable)
                cbox = QCheckBox(scoutable["name"])
                cbox.setObjectName(generateObjectName(scoutable["name"]) + str(emulator_index + 1))
                scoutables_layout.addWidget(cbox)
            self.findChild(QFrame, "scoutables_scan_frame_" + str(emulator_index + 1)).setLayout(
                scoutables_layout)

    def loadNormalMonsterControlsScanMap(self):
        global widgets
        global all_normal_monsters

        for emulator_index in range(self.total_emulator):
            normal_monster_layout = FlowLayout()
            for monster in all_normal_monsters:
                # print(monster)
                cbox = QCheckBox(monster["name"])
                cbox.setObjectName(generateObjectName(monster["name"]) + str(emulator_index + 1))
                normal_monster_layout.addWidget(cbox)
            self.findChild(QFrame, "normal_monster_scan_frame_" + str(emulator_index + 1)).setLayout(
                normal_monster_layout)

    def loadBossMonsterControlsScanMap(self):
        global widgets
        global all_boss_monsters

        boss_monsters = self.filterMonsterListByCategory("Boss Monster")
        event_monsters = self.filterMonsterListByCategory("Event Monster")
        # print(event_monsters)
        for emulator_index in range(self.total_emulator):
            boss_monster_layout = FlowLayout()
            other_monster_layout = FlowLayout()
            # print("Emulator : ", emulator_index)
            for monster in boss_monsters:
                # print(monster)
                if monster['enable_map_scan'] == 1:
                    cbox = QCheckBox(monster["preview_name"])
                    cbox.setObjectName(generateObjectName(monster["preview_name"]) + "sm_" + str(emulator_index + 1))
                    boss_monster_layout.addWidget(cbox)
            for monster in event_monsters:
                if monster["monster_logic_id"] == 2 and monster['enable_map_scan'] == 1:
                    checkbox_obj_name = "checkbox_" + generateObjectName(monster["preview_name"]) + "sm_" + str(
                        emulator_index + 1)
                    combobox_obj_name = "combobox_" + generateObjectName(monster["preview_name"]) + "sm_" + str(
                        emulator_index + 1)
                    vert_layout = QVBoxLayout()
                    check_box = QCheckBox(monster["preview_name"])
                    check_box.setObjectName(checkbox_obj_name)
                    check_box.stateChanged.connect(self.monster_checkbox_change_logic3)

                    vert_layout.addWidget(check_box)
                    vert_layout.setContentsMargins(0, 0, 10, 5)
                    combo_box = CheckComboBox(placeholderText="None")
                    combo_box.setObjectName(combobox_obj_name)
                    combo_box.setDisabled(True)
                    model = combo_box.model()
                    combo_box.addItem("Select Level")
                    model.item(0).setEnabled(False)
                    combo_box.insertSeparator(1)
                    tmp_index = 2
                    for level in monster['levels']:
                        # print(level)
                        combo_box.addItem(str(level['name']))
                        model.item(tmp_index).setCheckable(True)
                        tmp_index = tmp_index + 1

                    vert_layout.addWidget(combo_box)
                    other_monster_layout.addItem(vert_layout)

                elif monster["monster_logic_id"] == 3 and monster['enable_map_scan'] == 1:
                    checkbox_obj_name = "checkbox_" + generateObjectName(monster["preview_name"]) + "sm_" + str(
                        emulator_index + 1)
                    combobox_obj_name = "combobox_" + generateObjectName(monster["preview_name"]) + "sm_" + str(
                        emulator_index + 1)
                    vert_layout = QVBoxLayout()
                    check_box = QCheckBox(monster["preview_name"])
                    check_box.setObjectName(checkbox_obj_name)
                    check_box.stateChanged.connect(self.monster_checkbox_change_logic3)

                    vert_layout.addWidget(check_box)
                    vert_layout.setContentsMargins(0, 0, 10, 5)
                    combo_box = CheckComboBox(placeholderText="None")
                    combo_box.setObjectName(combobox_obj_name)
                    combo_box.setDisabled(True)
                    model = combo_box.model()
                    combo_box.addItem("Select Level")
                    model.item(0).setEnabled(False)
                    combo_box.insertSeparator(1)
                    tmp_index = 2
                    for level in monster['levels']:
                        # print(level)
                        combo_box.addItem("Level " + str(level['level']))
                        model.item(tmp_index).setCheckable(True)
                        tmp_index = tmp_index + 1

                    vert_layout.addWidget(combo_box)
                    other_monster_layout.addItem(vert_layout)

            self.findChild(QFrame, "boss_monster_scan_frame_" + str(emulator_index + 1)).setLayout(boss_monster_layout)
            self.findChild(QFrame, "other_monster_scan_frame_" + str(emulator_index + 1)).setLayout(
                other_monster_layout)

    def loadMonsterControlsJoinRally(self):
        global widgets
        global all_boss_monsters
        # print(all_boss_monsters)
        boss_monsters = self.filterMonsterListByCategory("Boss Monster")
        event_monsters = self.filterMonsterListByCategory("Event Monster")
        for emulator_index in range(self.total_emulator):
            boss_monster_layout = FlowLayout()
            event_monster_layout = FlowLayout()
            event_monster_combo_layout = FlowLayout()
            # print("Emulator : ", emulator_index)
            for monster in boss_monsters:
                # print(monster)
                cbox = QCheckBox(monster["preview_name"])
                cbox.setObjectName(generateObjectName(monster["preview_name"]) + "jr_" + str(emulator_index + 1))
                boss_monster_layout.addWidget(cbox)

            for monster in event_monsters:
                if monster["monster_logic_id"] == 2:
                    checkbox_obj_name = "checkbox_" + generateObjectName(monster["preview_name"]) + "jr_" + str(
                        emulator_index + 1)
                    combobox_obj_name = "combobox_" + generateObjectName(monster["preview_name"]) + "jr_" + str(
                        emulator_index + 1)
                    vert_layout = QVBoxLayout()
                    check_box = QCheckBox(monster["preview_name"])
                    check_box.setObjectName(checkbox_obj_name)
                    check_box.stateChanged.connect(self.monster_checkbox_change_logic3)

                    vert_layout.addWidget(check_box)
                    vert_layout.setContentsMargins(0, 0, 10, 5)
                    combo_box = CheckComboBox(placeholderText="None")
                    combo_box.setObjectName(combobox_obj_name)
                    combo_box.setDisabled(True)
                    model = combo_box.model()
                    combo_box.addItem("Skip Level")
                    model.item(0).setEnabled(False)
                    combo_box.insertSeparator(1)
                    tmp_index = 2
                    for level in monster['levels']:
                        # print(level)
                        combo_box.addItem(str(level['name']))
                        model.item(tmp_index).setCheckable(True)
                        tmp_index = tmp_index + 1

                    vert_layout.addWidget(combo_box)
                    event_monster_layout.addItem(vert_layout)
                # print(monster)
                elif monster["monster_logic_id"] == 3:
                    checkbox_obj_name = "checkbox_" + generateObjectName(monster["preview_name"]) + "jr_" + str(
                        emulator_index + 1)
                    combobox_obj_name = "combobox_" + generateObjectName(monster["preview_name"]) + "jr_" + str(
                        emulator_index + 1)
                    vert_layout = QVBoxLayout()
                    check_box = QCheckBox(monster["preview_name"])
                    check_box.setObjectName(checkbox_obj_name)
                    check_box.stateChanged.connect(self.monster_checkbox_change_logic3)

                    vert_layout.addWidget(check_box)
                    vert_layout.setContentsMargins(0, 0, 10, 5)
                    combo_box = CheckComboBox(placeholderText="None")
                    combo_box.setObjectName(combobox_obj_name)
                    combo_box.setDisabled(True)
                    model = combo_box.model()
                    combo_box.addItem("Skip Level")
                    model.item(0).setEnabled(False)
                    combo_box.insertSeparator(1)
                    tmp_index = 2
                    for level in monster['levels']:
                        # print(level)
                        combo_box.addItem("Level " + str(level['level']))
                        model.item(tmp_index).setCheckable(True)
                        tmp_index = tmp_index + 1

                    vert_layout.addWidget(combo_box)
                    event_monster_combo_layout.addItem(vert_layout)

            self.findChild(QFrame, "boss_monster_body_frame_" + str(emulator_index + 1)).setLayout(boss_monster_layout)
            self.findChild(QFrame, "event_monster_body_frame_" + str(emulator_index + 1)).setLayout(
                event_monster_layout)
            self.findChild(QFrame, "event_monster_combo_body_frame_" + str(emulator_index + 1)).setLayout(
                event_monster_combo_layout)

    def setUpMoreActivitiesFrames(self):
        frames = ['task_settings_one_frame_', 'task_settings_two_frame_']
        for emulator_index in range(self.total_emulator):
            for frame in frames:
                object_name = frame + str(emulator_index + 1)
                css = "#" + object_name + "{ border: 1px solid  rgb(29, 33, 38); }"
                self.findChild(QFrame, object_name).setStyleSheet(css)

    def monster_checkbox_change_logic3(self):
        # print(self.sender().objectName())
        checkbox = self.findChild(QCheckBox, self.sender().objectName())
        combobox = self.findChild(QComboBox, self.sender().objectName().replace("checkbox_", "combobox_"))

        if checkbox.isChecked():
            combobox.setDisabled(False)
        else:
            for i in combobox.checkedIndices():
                combobox.setItemCheckState(i, False)
            combobox.setDisabled(True)

    def filterMonsterListByCategory(self, category):
        global all_boss_monsters
        monsters = []
        for monster in all_boss_monsters:
            if monster['monster_category'] == category:
                monsters.append(monster)
        return monsters

    # EMULATOR NAME & PORT CHANGE
    # ///////////////////////////////////////////////////////////////
    def emulatorPortChange(self):
        edit = self.sender()
        edit_name = edit.objectName()
        index = int(extract_numbers_from_string(edit_name))
        conn = create_connection("main.db")
        update = execute_query(conn, update_emulator_port, {'emulator_port': edit.text(), 'id': index})
        conn.commit()

    def emulatorNameChange(self):
        edit = self.sender()
        edit_name = edit.objectName()
        index = int(extract_numbers_from_string(edit_name))
        conn = create_connection("main.db")
        update = execute_query(conn, update_emulator_name, {'emulator_name': edit.text(), 'id': index})
        conn.commit()
        if edit_name == f"emu_name_{str(index)}":
            if edit.text() == "":
                self.findChild(QPushButton, "btn_emu_" + str(index)).setText("Emulator " + str(index))
                self.findChild(QGroupBox, "groupBox_console_" + str(index)).setTitle(
                    "Emulator " + str(index) + " Console")
            else:
                self.findChild(QPushButton, "btn_emu_" + str(index)).setText(edit.text())
                self.findChild(QGroupBox, "groupBox_console_" + str(index)).setTitle(edit.text() + " Console")

    # SWITCH EMULATOR START STOP BUTTON  WITH LED
    # ///////////////////////////////////////////////////////////////
    def switchRunButton(self):
        global widgets
        thread_index = self.sender().index
        run_btn = self.findChild(QPushButton, "emu_start_" + str(thread_index))
        print("Run Button text:: ", run_btn.text())
        if run_btn.text() == "Start":
            # Change template Stop
            print("Changing to stop button:::")
            run_btn.setText("Stop")
            led = self.findChild(QLabel, "emu_led_" + str(thread_index))
            led.setPixmap(QPixmap(u":/extra icons/images/extra icons/green-led-on.png"))
        elif run_btn.text() == "Stop":
            # Change template to run
            run_btn.setText("Start")
            led = self.findChild(QLabel, "emu_led_" + str(thread_index))
            led.setPixmap(QPixmap(u":/extra icons/images/extra icons/red-led-on.png"))
            self.thread[thread_index].is_running = False
            self.thread[thread_index].device_emu = None

    # RESTART MODE
    def invokeSwitchRun(self):
        index = self.sender().index
        self.findChild(QPushButton, "emu_start_" + str(index)).click()

    # Press Emulator Start & Stop with config run btn
    def invokeStartAndStop(self):
        btn = self.sender()
        index = int(extract_numbers_from_string(btn.objectName()))
        self.findChild(QPushButton, "emu_start_" + str(index)).click()

    # STARTING & STOPPING EMULATOR RUN(THREADING)
    # ///////////////////////////////////////////////////////////////
    def startAndStopEmulator(self):
        btn = self.sender()
        btn_name = btn.text()
        index = int(extract_numbers_from_string(btn.objectName()))
        # STOP BUTTON
        if btn_name == "Stop":
            self.thread[index].invokeEmulatorConsole(
                "Stopping " + self.thread[index].emulator_name + " on port " + self.thread[index].emulator_port)
            self.thread[index].quit()
            icon = QIcon()
            icon.addFile(u":/icons/images/icons/cil-media-play.png", QSize(), QIcon.Normal, QIcon.Off)
            self.findChild(QPushButton, "emu_run_" + str(index)).setIcon(icon)
        # START BUTTON
        elif btn_name == "Start":
            icon = QIcon()
            icon.addFile(u":/icons/images/icons/cil-media-stop.png", QSize(), QIcon.Normal, QIcon.Off)
            self.findChild(QPushButton, "emu_run_" + str(index)).setIcon(icon)

            emulator_port = self.findChild(QLineEdit, f"emu_port_{str(index)}").text()
            emulator_name = self.findChild(QLineEdit, f"emu_name_{str(index)}").text()
            config = {"emulator_port": emulator_port, "emulator_name": emulator_name,
                      "emulator_control": self.getEmulatorControls(index)}

            self.thread[index] = ConfigurationThread(parent=None, index=index, config=config)
            self.thread[index].start()
            self.thread[index].emulator_console.connect(self.logEmulatorConsole)
            self.thread[index].device_console.connect(self.deviceConsole)
            self.thread[index].start_stop_button_switch.connect(self.switchRunButton)
            self.thread[index].switch_run.connect(self.invokeSwitchRun)
            self.thread[index].update_training_table.connect(self.updateTroopsTrainingQueue)

    # MAPPING CONTROLS AND PASSING TO THREADS
    # ///////////////////////////////////////////////////////////////
    def getEmulatorControls(self, index):
        # index = self.sender().index
        # print("Inside emulator controls:",index)
        emu_dict = {}
        emu_dict['mode'] = str(self.findChild(QComboBox, "comboBoxMode_" + str(index)).currentText())
        emu_dict['profile'] = str(self.findChild(QComboBox, "comboBoxProfile_" + str(index)).currentText())
        emu_dict['game_settings'] = self.getGameSettings(index)
        if emu_dict['mode'] == "Join Rally":
            emu_dict['join_rally'] = self.getJoinRallyControls(index)
        elif emu_dict['mode'] == "Troop Training":
            emu_dict['troop_training'] = self.getTroopTrainingControls(index)
        elif emu_dict['mode'] == "Black Market":
            emu_dict['black_market'] = self.getBlackMarketControls(index)
        elif emu_dict['mode'] == "World Map Scan":
            emu_dict['world_map_scan'] = self.getWorldMapScanControls(index)
        elif emu_dict['mode'] == "Patrol":
            emu_dict['patrol'] = self.getPatrolControls(index)
        elif emu_dict['mode'] == "More Activities":
            emu_dict['custom_tasks'] = self.getCustomTasksControls(index)
        # self.thread[index].emulator_control = emu_dict
        # print("Dict in main: ", self.thread[index].emulator_control)
        return emu_dict

    def getGameSettings(self, index):
        add_break = {'add_break': self.findChild(QCheckBox, "add_break_" + str(index)).isChecked(),
                     'value': {'from': QTime.fromString(
                         self.findChild(QTimeEdit, "break_from_" + str(index)).time().toString("hh:mm"), "hh:mm"),
                         'to': QTime.fromString(
                             self.findChild(QTimeEdit, "break_to_" + str(index)).time().toString("hh:mm"),
                             "hh:mm")}}
        game_settings = {'kick_timer': self.findChild(QSpinBox, "kick_timer_" + str(index)).value(),
                         'add_break': add_break}
        return game_settings

    def getCustomTasksControls(self, index):
        controls = {}
        for task in self.findChild(QGroupBox, "activity_select_" + str(index)).findChildren(QRadioButton):
            if task.isChecked():
                controls['task'] = task.objectName().split('_')[2]
                break
        # print("Selected Custom Task is : ", controls['task'])
        tmp = {}
        if controls['task'] == "cultivate":
            checkboxes = self.findChild(QGroupBox, "activity_settings_" + str(index)).findChildren(QCheckBox)
            for cb in checkboxes:
                if cb.objectName().startswith(controls['task']):
                    tmp[cb.text().lower()] = cb.isChecked()
        elif controls['task'] == "wof":
            spinboxes = self.findChild(QGroupBox, "activity_settings_" + str(index)).findChildren(QSpinBox)
            for sb in spinboxes:
                if sb.objectName().startswith(controls['task']):
                    tmp[sb.property("name")] = sb.value()
        controls['settings'] = tmp
        # print(controls) #{'task': 'cultivate', 'settings': {'Leadership': True, 'Attack': True, 'Defense': True, 'Politics': True}}
        print(controls)  # {'task': 'wof', 'settings': {'100': 4, '10': 1, '1': 0}}
        return controls

    def getWorldMapScanControls(self, index):
        enable_boss_scan = self.findChild(QCheckBox, "enable_boss_scan_" + str(index))
        enable_monster_scan = self.findChild(QCheckBox, "enable_monster_scan_" + str(index))
        enable_tile_scan = self.findChild(QCheckBox, "enable_tile_scan_" + str(index))
        enable_scoutables_scan = self.findChild(QCheckBox, "enable_scoutables_scan_" + str(index))
        share_collective = self.findChild(QRadioButton, "world_map_scan_share_collective_" + str(index))
        share_whisper = self.findChild(QRadioButton, "world_map_scan_share_whisper_" + str(index))
        share_ac = self.findChild(QRadioButton, "world_map_scan_share_ac_" + str(index))
        start_at_cords_option = self.findChild(QCheckBox, "world_map_scan_start_cords_" + str(index))
        cords_x = self.findChild(QLineEdit, "world_map_scan_cords_x_" + str(index)).text()
        cords_y = self.findChild(QLineEdit, "world_map_scan_cords_y_" + str(index)).text()

        world_map_scan_properties = {}
        world_map_scan_properties['share_collective'] = True if share_collective.isChecked() else False
        world_map_scan_properties['share_whisper'] = True if share_whisper.isChecked() else False
        world_map_scan_properties['share_ac'] = True if share_ac.isChecked() else False
        world_map_scan_properties['custom_cords'] = None if not start_at_cords_option.isChecked() else {
            'x': cords_x.strip(),
            'y': cords_y.strip()}
        if enable_boss_scan.isChecked():
            world_map_scan_properties['enable_boss_scan'] = True
            world_map_scan_properties['boss_scan'] = self.getBossScanControls(index)
        else:
            world_map_scan_properties['enable_boss_scan'] = False
            world_map_scan_properties['boss_scan'] = None
        if enable_monster_scan.isChecked():
            world_map_scan_properties['enable_monster_scan'] = True
            world_map_scan_properties['monster_scan'] = self.getMonsterScanControls(index)
        else:
            world_map_scan_properties['enable_monster_scan'] = False
            world_map_scan_properties['monster_scan'] = None
        if enable_tile_scan.isChecked():
            world_map_scan_properties['enable_tile_scan'] = True
        else:
            world_map_scan_properties['enable_tile_scan'] = False
            world_map_scan_properties['tile_scan'] = None
        if enable_scoutables_scan.isChecked():
            world_map_scan_properties['enable_scoutables_scan'] = True
            world_map_scan_properties['scoutables_scan'] = self.getScoutablesScanControls(index)
        else:
            world_map_scan_properties['enable_scoutables_scan'] = False
            world_map_scan_properties['scoutables_scan'] = None

        return world_map_scan_properties

    def getScoutablesScanControls(self, index):
        controls = {}
        scoutables_scan_frame = self.findChild(QFrame, "scoutables_scan_frame_" + str(index))
        # Fetching selected scoutables
        checkbox_list = scoutables_scan_frame.findChildren(QCheckBox)
        scout_list = []
        for checkbox in checkbox_list:
            if checkbox.isChecked():
                scoutables = {}
                for scout in all_scoutables:
                    if scout['name'] == checkbox.text():
                        scoutables['img_540p'] = scout['img_540p']
                        scoutables['img_1080p'] = scout['img_1080p']
                        scoutables['name'] = scout['name']
                        scoutables['type'] = scout['type']
                        break
                scout_list.append(scoutables)
                controls['scoutables'] = scout_list
        return controls

    def getMonsterScanControls(self, index):
        controls = {}
        normal_monster_scan_frame = self.findChild(QFrame, "normal_monster_scan_frame_" + str(index))
        # Fetching selected monsters
        checkbox_list = normal_monster_scan_frame.findChildren(QCheckBox)
        monster_list = []
        for checkbox in checkbox_list:
            if checkbox.isChecked():
                monsters = {}
                for monster in all_normal_monsters:
                    if monster['name'] == checkbox.text():
                        monsters['img_540p'] = monster['img_540p']
                        monsters['img_1080p'] = monster['img_1080p']
                        monsters['img_threshold'] = monster['img_threshold']
                        monsters['click_pos'] = monster['click_pos']
                        monsters['name'] = monster['name']
                        break
                monster_list.append(monsters)
                controls['monsters'] = monster_list
        return controls

    def getBossScanControls(self, index):
        controls = {}
        boss_monster_scan_frame = self.findChild(QFrame, "boss_monster_scan_frame_" + str(index))
        other_monster_scan_frame = self.findChild(QFrame, "other_monster_scan_frame_" + str(index))
        # Fetching selected monsters
        checkbox_list = boss_monster_scan_frame.findChildren(QCheckBox)
        monster_list = []
        for checkbox in checkbox_list:
            if checkbox.isChecked():
                monsters = {}
                for monster in all_boss_monsters:
                    if monster['preview_name'] == checkbox.text():
                        monsters['logic'] = 1
                        monsters['img_540p'] = monster['img_540p']
                        monsters['img_1080p'] = monster['img_1080p']
                        monsters['img_threshold'] = monster['img_threshold']
                        monsters['click_pos'] = monster['click_pos']
                        monsters['level'] = monster['levels'][0]['level']
                        monsters['name'] = monster['levels'][0]['name']
                        monsters['preview_name'] = monster['preview_name']
                        monsters['size'] = monster['levels'][0]['size']
                        break
                monster_list.append(monsters)
        checkbox_list = other_monster_scan_frame.findChildren(QCheckBox)
        for checkbox in checkbox_list:
            if checkbox.isChecked():
                for monster in all_boss_monsters:
                    if monster['preview_name'] == checkbox.text():
                        combo_box = self.findChild(CheckComboBox,
                                                   checkbox.objectName().replace("checkbox_", "combobox_"))
                        for combobox_lv in combo_box.checkedIndices():
                            monsters = {}
                            monsters['logic'] = monster['monster_logic_id']
                            monsters['img_540p'] = monster['img_540p']
                            monsters['img_1080p'] = monster['img_1080p']
                            monsters['img_threshold'] = monster['img_threshold']
                            monsters['click_pos'] = monster['click_pos']
                            monsters['preview_name'] = monster['preview_name']
                            for level in monster['levels']:
                                if level['level'] == combobox_lv - 1:
                                    monsters['level'] = level['level']
                                    monsters['name'] = level['name']
                                    monsters['size'] = level['size']
                                    monster_list.append(monsters)
                                    break
        controls['monsters'] = monster_list
        return controls

    def getBlackMarketControls(self, index):

        # Get buy items selected
        buy_items_frame = self.findChild(QFrame, "buy_items_frame_" + str(index))
        items = buy_items_frame.findChildren(QCheckBox)
        refresh_times = self.findChild(QSpinBox, "market_refresh_" + str(index)).value()
        all_items = {
            "5M Food": {"name": "5M Food", "file_name": "5m_food.png"},
            "5M Wood": {"name": "5M Wood", "file_name": "5m_wood.png"},
            "5M Stone": {"name": "5M Stone", "file_name": "5m_stone.png"},
            "5M Ore": {"name": "5M Ore", "file_name": "5m_iron.png"},
            "2M Food": {"name": "2M Food", "file_name": "2m_food.png"},
            "2M Wood": {"name": "2M Wood", "file_name": "2m_wood.png"},
            "2M Stone": {"name": "2M Stone", "file_name": "2m_stone.png"},
            "2M Ore": {"name": "2M Ore", "file_name": "2m_iron.png"},
            "1M Food": {"name": "1M Food", "file_name": "1m_food.png"},
            "1M Wood": {"name": "1M Wood", "file_name": "1m_wood.png"},
            "1M Stone": {"name": "1M Stone", "file_name": "1m_stone.png"},
            "1M Ore": {"name": "1M Ore", "file_name": "1m_iron.png"},
            "Food Speedup": {"name": "Food Speedup", "file_name": "food_speed_up.png"},
            "Wood Speedup": {"name": "Wood Speedup", "file_name": "wood_speed_up.png"},
            "Stone Speedup": {"name": "Stone Speedup", "file_name": "stone_speed_up.png"},
            "Iron Speedup": {"name": "Iron Speedup", "file_name": "iron_speed_up.png"},
            "General Exp": {"name": "General Exp", "file_name": "general_exp.png"},
            "Monarch Exp": {"name": "Monarch Exp", "file_name": "monarch_exp_big.png"},
            "Wheel Chips": {"name": "Wheel Chips", "file_name": "wheel_chips.png"},
            "VIP Time": {"name": "VIP Time", "file_name": "vip_time.png"},
            "Tributes": {"name": "Tributes", "file_name": "tributes.png"},
            "Treasure Box": {"name": "Treasure Box", "file_name": "treasure_box.png"},
            "Stamina": {"name": "Stamina", "file_name": "stamina.png"}}
        buy_items = []
        try:
            for checkbox in items:
                if checkbox.objectName().startswith("item_"):
                    if checkbox.isChecked():
                        item_values = all_items[checkbox.text()]
                        item = {"name": item_values["name"], "file_name": item_values["file_name"], "buy_type": {}}
                        item["buy_type"]["rss"] = self.findChild(QPushButton,
                                                                 checkbox.objectName().replace("item_",
                                                                                               "rss_")).isChecked()
                        item["buy_type"]["gold"] = self.findChild(QPushButton,
                                                                  checkbox.objectName().replace("item_",
                                                                                                "gold_")).isChecked()
                        item["buy_type"]["gems"] = self.findChild(QPushButton,
                                                                  checkbox.objectName().replace("item_",
                                                                                                "gem_")).isChecked()
                        item["buy_type"]["rebuy"] = self.findChild(PyToggle,
                                                                   checkbox.objectName().replace("item_",
                                                                                                 "rebuy_")).isChecked()
                        buy_items.append(item)
        except Exception as e:
            print(e)
        # print(buy_items)
        all_items_properties = {"refresh_times": int(refresh_times), "all_rss": False, "all_gold": False,
                                "items": buy_items}

        # Get buy options selection
        buy_options_frame = self.findChild(QFrame, "buy_options_frame_" + str(index))
        buy_options_list = buy_options_frame.findChildren(QCheckBox)
        for checkbox in buy_options_list:
            if checkbox.isChecked():
                if "Resources" in checkbox.text():
                    all_items_properties["all_rss"] = True
                elif "Gold" in checkbox.text():
                    all_items_properties["all_gold"] = True
        return all_items_properties

    def getTroopTrainingControls(self, index):
        try:
            table = self.findChild(QTableWidget, "troop_queue_table_" + str(index))
            military_camp = {"Mounted": "stables.png", "Ranged": "archercamp.png", "Ground": "barracks.png",
                             "Siege": "workshop.png"}
            troops = []
            for row in range(table.rowCount() - 1):
                troop = {"building": "_" + military_camp[table.item(row, 0).text()],
                         "tier": table.item(row, 1).text(),
                         "train_times": table.item(row, 2).text()}
                troops.append(troop)
        except Exception as e:
            print(e)
        return troops

    def getJoinRallyControls(self, index):
        global all_boss_monsters
        # print(all_boss_monsters)
        logic_one_frame = self.findChild(QFrame, "boss_monster_body_frame_" + str(index))
        logic_two_frame = self.findChild(QFrame, "event_monster_body_frame_" + str(index))
        logic_three_frame = self.findChild(QFrame, "event_monster_combo_body_frame_" + str(index))
        # Logic 1
        checkbox_list = logic_one_frame.findChildren(QCheckBox)
        join_rally_list = {}
        monster_list = []
        # print("Before the loops")
        for checkbox in checkbox_list:
            if checkbox.isChecked() is False:
                monsters = None
                # print(checkbox.objectName())
                monsters = next(
                    (monster["levels"][0] for monster in all_boss_monsters if
                     monster['preview_name'] == checkbox.text()),
                    None)
                monsters["logic"] = 1
                monster_list.append(monsters)
        # Logic 2
        checkbox_list = logic_two_frame.findChildren(QCheckBox)
        for checkbox in checkbox_list:
            combo_box = self.findChild(CheckComboBox,
                                       checkbox.objectName().replace("checkbox_", "combobox_"))
            monsters = None
            # print(checkbox.objectName(), combo_box.objectName())
            # print(combo_box.unCheckedIndices(), combo_box.checkedIndices())#[0, 1, 4] [2, 3]
            # Get monster preview name from the combobox object id:combobox_cerberus_jr_1
            tmp_name = remove_number_from_string(combo_box.objectName().replace("combobox_", "").replace("_jr_", ""))
            preview_name = next(
                (monster["preview_name"] for monster in all_boss_monsters if
                 monster['preview_name'].lower().replace(" ", "") == tmp_name),
                None)
            # print(preview_name)
            for lv in combo_box.unCheckedIndices():
                if lv == 0 or lv == 1:
                    # Skipping first two elements in that combo box
                    continue
                for monster in all_boss_monsters:
                    if monster["preview_name"] == preview_name:
                        for level in monster["levels"]:
                            if level["level"] == lv - 1:
                                level['logic'] = 2
                                monster_list.append(level)
                                break
                        break

        # Logic 3
        checkbox_list = logic_three_frame.findChildren(QCheckBox)
        for checkbox in checkbox_list:
            combo_box = self.findChild(CheckComboBox,
                                       checkbox.objectName().replace("checkbox_", "combobox_"))
            monsters = None
            for monster in all_boss_monsters:
                monster_name = next(
                    (levels["name"] for levels in monster["levels"] if monster["preview_name"] == checkbox.text()),
                    None)
                if monster_name is not None:
                    for lv in combo_box.unCheckedIndices():
                        monsters = next(
                            (levels for levels in monster["levels"] if levels["level"] == (lv - 1)), None)
                        if monsters is not None:
                            monsters["logic"] = 3
                            # print(monsters)
                            monster_list.append(monsters)
        # print(monster_list)
        join_rally_list['monsters'] = monster_list
        other_settings_groupbox = self.findChild(QGroupBox, "join_rally_other_settings_groupbox_" + str(index))
        try:
            tmp = {'rotate_preset': other_settings_groupbox.findChild(QComboBox,
                                                                      "rotate_preset_" + str(index)).currentIndex() + 1,
                   'auto_use_stamina': other_settings_groupbox.findChild(QCheckBox,
                                                                         "auto_use_stamina_" + str(index)).isChecked(),
                   'attempt_preset_with_general': other_settings_groupbox.findChild(QCheckBox,
                                                                                    "attempt_preset_" + str(
                                                                                        index)).isChecked()
                   }
        except Exception as e:
            print(e)
        join_rally_list['other_settings'] = tmp
        return join_rally_list

    def getPatrolControls(self, index):
        patrol_groupbox = self.findChild(QGroupBox, "patrol_items_groupBox_" + str(index))
        checkbox_list = patrol_groupbox.findChildren(QCheckBox)
        patrol_list = []
        for checkbox in checkbox_list:
            if checkbox.isChecked():
                patrol_list.append(checkbox.text())
        patrol_controls = {'patrol_gem': self.findChild(QSpinBox, "patrol_gem_" + str(index)).value(),
                           'refresh_gold': self.findChild(QSpinBox, "refresh_gold_" + str(index)).value(),
                           'patrol_list': patrol_list}
        # print("Patrol Controls: ", patrol_list)
        return patrol_controls

    def deviceConsole(self):
        emulator_name = self.sender().emulator_name
        index = self.sender().index
        if len(emulator_name) == 0:
            emulator_name = f"Emulator {index}"
        log = self.sender().log
        emulator_console_txt = "[" + emulator_name + "]" if emulator_name is not None else ""
        emulator_console_txt += "[" + get_date_and_time() + "]: " + log
        console_emulator = self.findChild(QPlainTextEdit, "emulator_console_" + str(index))
        console_emulator.appendPlainText(emulator_console_txt)

    def logEmulatorConsole(self):
        emulator_name = self.sender().emulator_name
        log = self.sender().log
        emulator_console_txt = "[" + emulator_name + "]" if emulator_name is not None else ""
        emulator_console_txt += "[" + get_date_and_time() + "]: " + log
        widgets.emulator_console.appendPlainText(emulator_console_txt)

    def menuButtonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btn_name = btn.objectName()

        # SHOW ABOUT PAGE
        if btn_name == "btn_about":
            widgets.stackedWidget.setCurrentWidget(widgets.about)
            UIFunctions.resetStyle(self, btn_name)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        if btn_name == "ico_btn_support":
            widgets.btn_about.click()

        # SHOW CONFIG PAGE
        if btn_name == "btn_config":
            widgets.stackedWidget.setCurrentWidget(widgets.config)
            UIFunctions.resetStyle(self, btn_name)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        if btn_name == "btn_collective":
            widgets.stackedWidget.setCurrentWidget(widgets.collective)
            UIFunctions.resetStyle(self, btn_name)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # Show Emulator Pages
        if "btn_emu_" in btn_name:
            page_id = btn_name.replace("btn_", "")
            page = self.findChild(QWidget, page_id)
            widgets.stackedWidget.setCurrentWidget(page)  # SET PAGE
            UIFunctions.resetStyle(self, btn_name)  # RESET ANOTHERS BUTTONS SELECTED
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))  # SELECT MENU

        # SHOW Settings PAGE
        if btn_name == "btn_settings":
            widgets.stackedWidget.setCurrentWidget(widgets.settings)
            UIFunctions.resetStyle(self, btn_name)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # PRINT BTN NAME
        # print(f'Button "{btn_name}" pressed!')

    # RESIZE EVENTS
    # ///////////////////////////////////////////////////////////////
    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    # MOUSE CLICK EVENTS
    # ///////////////////////////////////////////////////////////////
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPos()

        # PRINT MOUSE EVENTS
        '''if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')
        '''


if __name__ == "__main__":
    # faulthandler.enable()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    # window = MainWindow()
    window = SplashScreen()
    sys.exit(app.exec())
