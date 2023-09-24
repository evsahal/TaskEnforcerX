#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

# MAIN FILE
# ///////////////////////////////////////////////////////////////
from PyQt5.QtWidgets import QComboBox, QWidget, QLineEdit, QLabel, QCheckBox, QPushButton

from main import *
from modules import extract_numbers_from_string, create_connection, execute_query, add_profile_query, \
    update_profile_query, remove_number_from_string, PyToggle, delete_profile_by_id_query, \
    update_profile_control_by_name_query, update_emulator_mode, update_emulator_profile
import json


# WITH ACCESS TO MAIN WINDOW WIDGETS
# ///////////////////////////////////////////////////////////////
class Profile(MainWindow):

    # Create New Profile
    def createNewProfile(self):
        index = extract_numbers_from_string(self.sender().objectName())
        new_profile = self.findChild(QLineEdit, "create_profile_lineedit_" + str(index))
        new_profile_name = new_profile.text().strip()
        profile_status_text = self.findChild(QLabel, "profile_status_" + str(index))
        if new_profile_name.isspace() or len(new_profile_name) == 0:
            profile_status_text.setText("Profile Name should not be blank")
            return False
        # Check profile name exists or not
        for profile in self.all_profiles:
            if profile['name'].lower() == new_profile_name.lower():
                profile_status_text.setText("Profile Name already exists")
                return False
        try:
            conn = create_connection("main.db")
            controls = json.dumps(Profile.getCurrentControlsData(self, index))
            execute_query(conn, add_profile_query,
                          {'profile_name': new_profile_name, 'controls': controls})
            conn.commit()
            # Copy selected profiles
            emulator_profiles = Profile.getEmulatorProfile(self)
            # Update New Profile Names
            self.loadProfileNames()
            profile_status_text.setText("Successfully created new profile")
            # Assign Copied profiles back to the emulators modes
            Profile.setEmulatorProfile(self, emulator_profiles)
            new_profile.clear()
            self.findChild(QWidget, "profile_edit_widget_" + str(index)).hide()
        except Exception as e:
            profile_status_text.setText("Error while creating new profile")

    def setEmulatorProfile(self, emulator_profiles):
        for index in range(1, self.total_emulator + 1):
            profile_name = [profile['profile'] for profile in emulator_profiles if profile['index'] == index][0]
            if profile_name == '':
                continue
            combo_box_profile = self.findChild(QComboBox, "comboBoxProfile_" + str(index))
            combo_box_index = combo_box_profile.findText(profile_name)
            combo_box_profile.setCurrentIndex(combo_box_index)

    def getEmulatorProfile(self):
        profile_list = []
        for index in range(1, self.total_emulator + 1):
            combo_box_profile = self.findChild(QComboBox, "comboBoxProfile_" + str(index)).currentText()
            emulator_profiles = {'index': index, 'profile': combo_box_profile}
            profile_list.append(emulator_profiles)
        # print(profile_list)  # [{'index': 1, 'profile': 'Farm'}, {'index': 2, 'profile': ''}]
        return profile_list

    def saveProfile(self):
        index = extract_numbers_from_string(self.sender().objectName())
        profile_status_text = self.findChild(QLabel, "profile_status_" + str(index))
        edit_profile_name = self.findChild(QLineEdit, "edit_profile_lineedit_" + str(index)).text()
        profile_status_text.setText("Please wait...")
        if edit_profile_name.isspace() or len(edit_profile_name) == 0:
            profile_status_text.setText("Profile Name should not be blank")
            return False
        load_profile = self.findChild(QComboBox, "load_profile_combo_" + str(index))
        current_profile_name = load_profile.currentText()

        # Check profile name exists or not
        for profile in self.all_profiles:
            if profile['name'].lower() == edit_profile_name.lower():
                if current_profile_name.lower() == profile['name'].lower():
                    continue
                profile_status_text.setText("Profile Name already exists")
                return False
        # Get the ID of the exisiting Profile
        profile_id = [profile['id'] for profile in self.all_profiles if profile['name'] == current_profile_name][0]
        try:
            conn = create_connection("main.db")
            controls = json.dumps(Profile.getCurrentControlsData(self, index))
            execute_query(conn, update_profile_query,
                          {'profile_name': edit_profile_name, 'controls': controls,
                           'id': profile_id})
            conn.commit()
            # Copy selected profiles
            emulator_profiles = Profile.getEmulatorProfile(self)
            # Update current_profile_name with current_profile_name in copied profiles
            for profile in emulator_profiles:
                # print(profile) #{'index': 1, 'profile': ''}
                if profile['profile'] == current_profile_name:
                    profile['profile'] = edit_profile_name
            # Update New Profile Names
            self.loadProfileNames()
            # Assign Copied profiles back to the emulators modes
            Profile.setEmulatorProfile(self, emulator_profiles)
            # Re select Load Profile Value
            load_profile.setCurrentIndex(load_profile.findText(edit_profile_name))
            profile_status_text.setText("Successfully updated the Profile")
        except Exception as e:
            print(e)
            profile_status_text.setText("Error while Updating the Profile")

    def copyProfile(self):
        print(self.sender().objectName())
        index = extract_numbers_from_string(self.sender().objectName())
        profile_status_text = self.findChild(QLabel, "profile_status_" + str(index))
        copy_profile = self.findChild(QComboBox, "copy_profile_combo_" + str(index))
        copy_profile_name = copy_profile.currentText()
        if copy_profile.currentIndex() == -1:
            profile_status_text.setText("Please select a Profile to copy")
            return False
        profile_controls = \
            [profile['controls'] for profile in self.all_profiles if profile['name'] == copy_profile_name][0]
        load_profile = self.findChild(QComboBox, "load_profile_combo_" + str(index))
        load_profile_name = load_profile.currentText()
        try:
            conn = create_connection("main.db")
            execute_query(conn, update_profile_control_by_name_query,
                          {'name': load_profile_name, 'controls': profile_controls})
            conn.commit()
            # Copy selected profiles
            emulator_profiles = Profile.getEmulatorProfile(self)
            # Update New Profile Names
            self.loadProfileNames()
            # Assign Copied profiles back to the emulators modes
            Profile.setEmulatorProfile(self, emulator_profiles)
            # Re select Load Profile Value
            load_profile.setCurrentIndex(load_profile.findText(load_profile_name))
            profile_status_text.setText("Successfully copied the controls")
        except Exception as e:
            print(e)
            profile_status_text.setText("Error while copying the controls")

    def deleteProfile(self):
        # print(self.sender().objectName())
        index = extract_numbers_from_string(self.sender().objectName())
        profile_status_text = self.findChild(QLabel, "profile_status_" + str(index))
        load_profile = self.findChild(QComboBox, "load_profile_combo_" + str(index))
        current_profile_name = load_profile.currentText()
        # Get the ID of the Profile
        profile_id = [profile['id'] for profile in self.all_profiles if profile['name'] == current_profile_name][0]
        # print(profile_id, " : ", current_profile_name)
        try:
            conn = create_connection("main.db")
            execute_query(conn, delete_profile_by_id_query, {'id': profile_id})
            conn.commit()
            emulator_profiles = Profile.getEmulatorProfile(self)
            # Update Profile Names
            self.loadProfileNames()
            profile_status_text.setText("Successfully deleted the Profile")
            # Assign Copied profiles back to the emulators modes
            Profile.setEmulatorProfile(self, emulator_profiles)
            self.findChild(QWidget, "profile_edit_widget_" + str(index)).hide()
        except Exception as e:
            print(e)
            profile_status_text.setText("Error while deleting the Profile")

    def getCurrentControlsData(self, index):
        controls = {}
        # General Controls
        widget = self.findChild(QGroupBox, "game_settings_" + str(index))
        elements = widget.findChildren(QSpinBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QSpinBox', 'value': element.value()}
            controls[object_name] = tmp
        widget = self.findChild(QGroupBox, "game_settings_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        widget = self.findChild(QGroupBox, "game_settings_" + str(index))
        elements = widget.findChildren(QTimeEdit)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QTimeEdit', 'value': element.time().toString("hh:mm")}
            controls[object_name] = tmp
        # JOIN RALLY CONTROLS
        widget = self.findChild(QFrame, "boss_monster_body_frame_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        widget = self.findChild(QFrame, "event_monster_combo_body_frame_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            if element.isChecked():
                combobox = self.findChild(QComboBox, element.objectName().replace("checkbox_", "combobox_"))
                object_name = remove_number_from_string(combobox.objectName())
                tmp = {'type': 'CheckComboBox', 'value': combobox.checkedIndices()}
                controls[object_name] = tmp
            else:
                object_name = remove_number_from_string(element.objectName())
                tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
                controls[object_name] = tmp
        widget = self.findChild(QFrame, "event_monster_body_frame_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            if element.isChecked():
                combobox = self.findChild(QComboBox, element.objectName().replace("checkbox_", "combobox_"))
                object_name = remove_number_from_string(combobox.objectName())
                tmp = {'type': 'CheckComboBox', 'value': combobox.checkedIndices()}
                controls[object_name] = tmp
            else:
                object_name = remove_number_from_string(element.objectName())
                tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
                controls[object_name] = tmp
        # Join Rally Other Settings CONTROLS
        widget = self.findChild(QGroupBox, "join_rally_other_settings_groupbox_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        elements = widget.findChildren(QComboBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QComboBox', 'value': element.currentText()}
            controls[object_name] = tmp
        # WORLD MAP SCAN
        # SCAN SETTINGS CONTROLS
        widget = self.findChild(QGroupBox, "scan_settings_groupbox_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            if element.isChecked():
                object_name = remove_number_from_string(element.objectName())
                tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
                controls[object_name] = tmp
        elements = widget.findChildren(QRadioButton)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QRadioButton', 'value': element.isChecked()}
            controls[object_name] = tmp
        elements = widget.findChildren(QLineEdit)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QLineEdit', 'value': element.text()}
            controls[object_name] = tmp
        # SCAN BOSS CONTROLS
        widget = self.findChild(QFrame, "boss_monster_scan_frame_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        widget = self.findChild(QFrame, "other_monster_scan_frame_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            if element.isChecked():
                combobox = self.findChild(QComboBox, element.objectName().replace("checkbox_", "combobox_"))
                object_name = remove_number_from_string(combobox.objectName())
                tmp = {'type': 'CheckComboBox', 'value': combobox.checkedIndices()}
                controls[object_name] = tmp
            else:
                object_name = remove_number_from_string(element.objectName())
                tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
                controls[object_name] = tmp
        # SCAN NORMAL MONSTER CONTROLS
        widget = self.findChild(QFrame, "normal_monster_scan_frame_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        # SCAN SCOUTABLES CONTROLS
        widget = self.findChild(QFrame, "scoutables_scan_frame_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        # PATROL CONTROLS
        widget = self.findChild(QGroupBox, "patrol_general_groupbox_" + str(index))
        elements = widget.findChildren(QSpinBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QSpinBox', 'value': element.value()}
            controls[object_name] = tmp
        widget = self.findChild(QGroupBox, "patrol_items_groupBox_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        # BLACK MARKET CONTROLS
        widget = self.findChild(QGroupBox, "black_market_general_groupBox_" + str(index))
        elements = widget.findChildren(QSpinBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QSpinBox', 'value': element.value()}
            controls[object_name] = tmp
        widget = self.findChild(QGroupBox, "black_market_items_groupBox_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        elements = widget.findChildren(QPushButton)
        for element in elements:
            if element.isCheckable():
                object_name = remove_number_from_string(element.objectName())
                tmp = {'type': 'QPushButton', 'value': element.isChecked()}
                controls[object_name] = tmp
        elements = widget.findChildren(PyToggle)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'PyToggle', 'value': element.isChecked()}
            controls[object_name] = tmp

        # More Activities Controls
        widget = self.findChild(QGroupBox, "activity_select_" + str(index))
        elements = widget.findChildren(QRadioButton)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QRadioButton', 'value': element.isChecked()}
            controls[object_name] = tmp
        # More Activity Settings
        widget = self.findChild(QGroupBox, "activity_settings_" + str(index))
        elements = widget.findChildren(QCheckBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QCheckBox', 'value': element.isChecked()}
            controls[object_name] = tmp
        elements = widget.findChildren(QSpinBox)
        for element in elements:
            object_name = remove_number_from_string(element.objectName())
            tmp = {'type': 'QSpinBox', 'value': element.value()}
            controls[object_name] = tmp
        # print(controls)
        return controls

    def updateProfileToDB(self, index, profile_name):
        try:
            # print("Profile to DB")
            conn = create_connection("main.db")
            execute_query(conn, update_emulator_profile, {'emulator_profile': profile_name, 'id': index})
            conn.commit()
        except Exception as e:
            print(e)

    def updateModeToDB(self, index, mode_name):
        try:
            # print("Mode to DB")
            conn = create_connection("main.db")
            execute_query(conn, update_emulator_mode, {'emulator_mode': mode_name, 'id': index})
            conn.commit()
        except Exception as e:
            print(e)

    # Load_Profile Change
    def changeLoadProfile(self):
        # print(self.sender().objectName())
        index = extract_numbers_from_string(self.sender().objectName())
        # print("Test 123 :: ", index)
        self.findChild(QLabel, "profile_status_" + str(index)).setText("")
        load_profile_combo = self.findChild(QComboBox, "load_profile_combo_" + str(index))
        self.findChild(QWidget, "profile_edit_widget_" + str(index)).show()
        selected_item = load_profile_combo.currentText()
        self.findChild(QLineEdit, "edit_profile_lineedit_" + str(index)).setText(selected_item)
        Profile.loadCopyProfileCombo(self, selected_item, index)

    def loadCopyProfileCombo(self, current_profile, index):
        copy_profile_combo = self.findChild(QComboBox, "copy_profile_combo_" + str(index))
        copy_profile_combo.clear()
        for profile in self.all_profiles:
            if profile['name'] != current_profile:
                copy_profile_combo.addItem(profile['name'])

    def changeProfile(self):
        # print("change profile")
        index = extract_numbers_from_string(self.sender().objectName())
        profile_name = self.findChild(QComboBox, self.sender().objectName()).currentText()
        Profile.updateProfileToDB(self, index, profile_name)
        # print(profile_name)
        if profile_name == "":
            return False
        object_name = remove_number_from_string(self.sender().objectName())
        # print(object_name)
        if object_name != "emu_profile_":
            emu_profile = self.findChild(QComboBox, "emu_profile_" + str(index))
            emu_profile.blockSignals(True)
            emu_profile.setCurrentText(profile_name)
            emu_profile.blockSignals(False)
        if object_name != "comboBoxProfile_":
            combo_box_profile = self.findChild(QComboBox, "comboBoxProfile_" + str(index))
            combo_box_profile.blockSignals(True)
            combo_box_profile.setCurrentText(profile_name)
            combo_box_profile.blockSignals(False)
        load_profile_combo = self.findChild(QComboBox, "load_profile_combo_" + str(index))
        # load_profile_combo.blockSignals(True)
        load_profile_combo.setCurrentText(profile_name)
        # load_profile_combo.blockSignals(False)
        # Profile.changeLoadProfile(self, index)
        # Load all the controls
        try:
            profile_control = json.loads(
                [profile['controls'] for profile in self.all_profiles if profile['name'] == profile_name][
                    0])
            for key in profile_control:
                value = profile_control[key]
                # print(key, ':', value)  # market_refresh_ : {'type': 'QSpinBox', 'value': 99999}
                if value['type'] == "QCheckBox":
                    widget = self.findChild(QCheckBox, key + str(index))
                    if widget is not None:
                        widget.setChecked(value['value'])
                elif value['type'] == "QSpinBox":
                    widget = self.findChild(QSpinBox, key + str(index))
                    if widget is not None:
                        widget.setValue(value['value'])
                elif value['type'] == "QLineEdit":
                    widget = self.findChild(QLineEdit, key + str(index))
                    if widget is not None:
                        widget.setText(value['value'])
                elif value['type'] == "QRadioButton":
                    widget = self.findChild(QRadioButton, key + str(index))
                    if widget is not None:
                        widget.setChecked(value['value'])
                elif value['type'] == "QComboBox":
                    widget = self.findChild(QComboBox, key + str(index))
                    if widget is not None:
                        widget.setCurrentText(value['value'])
                elif value['type'] == "QPushButton":
                    widget = self.findChild(QPushButton, key + str(index))
                    if widget is not None:
                        widget.setChecked(value['value'])
                elif value['type'] == "PyToggle":
                    widget = self.findChild(PyToggle, key + str(index))
                    if widget is not None:
                        widget.setChecked(value['value'])
                elif value['type'] == "CheckComboBox":
                    widget = self.findChild(CheckComboBox, key + str(index))
                    if widget is not None:
                        checkbox = self.findChild(QCheckBox,
                                                  widget.objectName().replace("combobox_", "checkbox_"))
                        if checkbox is not None:
                            checkbox.setChecked(True)
                        for combo_index in value['value']:
                            widget.setItemCheckState(combo_index, Qt.Checked)
                elif value['type'] == "QTimeEdit":
                    widget = self.findChild(QTimeEdit, key + str(index))
                    if widget is not None:
                        widget.setTime(QTime.fromString(value['value'], "hh:mm"))
                        # widget.setTime(value['value'])
        except Exception as e:
            print(e)

    def changeMode(self):
        # print("change mode")
        index = extract_numbers_from_string(self.sender().objectName())
        mode_name = self.findChild(QComboBox, self.sender().objectName()).currentText()
        Profile.updateModeToDB(self, index, mode_name)
        object_name = remove_number_from_string(self.sender().objectName())
        if object_name != "emu_mode_":
            emu_mode = self.findChild(QComboBox, "emu_mode_" + str(index))
            emu_mode.blockSignals(True)
            emu_mode.setCurrentText(mode_name)
            emu_mode.blockSignals(False)
        if object_name != "comboBoxMode_":
            combo_box_mode = self.findChild(QComboBox, "comboBoxMode_" + str(index))
            combo_box_mode.blockSignals(True)
            combo_box_mode.setCurrentText(mode_name)
            combo_box_mode.blockSignals(False)

        # ADD MODE DESCRIPTION
        description = self.findChild(QPlainTextEdit, "mode_description_" + str(index))
        description.clear()
        mode_descriptions = {}
        mode_descriptions['Join Rally'] = "Skip Monsters:\nSelected monsters will be excluded from joining " \
                                          "rallies\n\nRotate Preset:\nSet the total number of presets to use when " \
                                          "joining rallies\n\nAttempt Preset with General:\nIt will attempt to select " \
                                          "a preset with general\n\nAuto Use Stamina:\nRefill stamina by " \
                                          "automatically consuming 100 Vit, 50 Vit, 25 Vit, or 10 Vit when needed "
        mode_descriptions['World Map Scan'] = "World Map Scan"
        mode_descriptions['Patrol'] = "Patrol"
        mode_descriptions['Black Market'] = "Black Market"
        mode_descriptions['Troop Training'] = "Troop Training"
        mode_descriptions['More Activities'] = "More Activities"
        description.setPlainText(mode_descriptions[mode_name])


# THREAD REMOVED DUE TO ISSUES WHEN SAVING THE PROFILE
# class LoadProfileThread(QThread):
#     def __init__(self, parent=None, index=0, profile_ui=None):
#         super(LoadProfileThread, self).__init__(parent)
#         self.index = index
#         self.profile_ui = profile_ui
#
#     finished = pyqtSignal()
#
#     def run(self):
#         try:
#             print("Inside run")
#             profile_combo = self.profile_ui.findChild(QComboBox, "comboBoxProfile_" + str(self.index))
#             current_profile = profile_combo.currentText()
#             print(current_profile)
#             if current_profile == "":
#                 return False
#             profile_control = json.loads(
#                 [profile['controls'] for profile in self.profile_ui.all_profiles if profile['name'] == current_profile][0])
#             for key in profile_control:
#                 value = profile_control[key]
#                 print(key, ':', value)  # market_refresh_ : {'type': 'QSpinBox', 'value': 99999}
#                 if value['type'] == "QCheckBox":
#                     widget = self.profile_ui.findChild(QCheckBox, key + str(self.index))
#                     if widget is not None:
#                         widget.setChecked(value['value'])
#                 elif value['type'] == "QSpinBox":
#                     widget = self.profile_ui.findChild(QSpinBox, key + str(self.index))
#                     if widget is not None:
#                         widget.setValue(value['value'])
#                 elif value['type'] == "QLineEdit":
#                     widget = self.profile_ui.findChild(QLineEdit, key + str(self.index))
#                     if widget is not None:
#                         widget.setText(value['value'])
#                 elif value['type'] == "QRadioButton":
#                     widget = self.profile_ui.findChild(QRadioButton, key + str(self.index))
#                     if widget is not None:
#                         widget.setChecked(value['value'])
#                 elif value['type'] == "QComboBox":
#                     widget = self.profile_ui.findChild(QComboBox, key + str(self.index))
#                     if widget is not None:
#                         widget.setCurrentText(value['value'])
#                 elif value['type'] == "QPushButton":
#                     widget = self.profile_ui.findChild(QPushButton, key + str(self.index))
#                     if widget is not None:
#                         widget.setChecked(value['value'])
#                 elif value['type'] == "PyToggle":
#                     widget = self.profile_ui.findChild(PyToggle, key + str(self.index))
#                     if widget is not None:
#                         widget.setChecked(value['value'])
#                 elif value['type'] == "CheckComboBox":
#                     widget = self.profile_ui.findChild(CheckComboBox, key + str(self.index))
#                     if widget is not None:
#                         checkbox = self.profile_ui.findChild(QCheckBox,
#                                                              widget.objectName().replace("combobox_", "checkbox_"))
#                         if checkbox is not None:
#                             checkbox.setChecked(True)
#                         for combo_index in value['value']:
#                             widget.setItemCheckState(combo_index, Qt.Checked)
#             self.finished.emit()
#         except Exception as e:
#             print(e)
