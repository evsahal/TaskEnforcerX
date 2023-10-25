#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QCheckBox

from modules.GeneralUtils import generateObjectName
from modules.ui.ui_monster_profile import Ui_Form


class MonsterProfile(QWidget, Ui_Form):
    def __init__(self, monster_property, parent=None):
        super(MonsterProfile, self).__init__(parent)
        self.setupUi(self)
        #print(monster_property)
        self.monster_icon_label.setPixmap(QPixmap(monster_property["img_path"]))
        self.monster_name_label.setText(monster_property["name"])
        self.delete_item.setObjectName(generateObjectName(monster_property["name"])+"delete")
        self.delete_item.setEnabled(monster_property["system"])
        #print("Fetching: ",self.delete_item.objectName())


class FlowContainer(QListWidget):
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

    def addMonsters(self, monster_property):
        item = QListWidgetItem()
        item.setFlags(item.flags() & ~(Qt.ItemIsSelectable | Qt.ItemIsEnabled))
        self.addItem(item)
        frame = MonsterProfile(monster_property)
        item.setSizeHint(frame.sizeHint())
        self.setItemWidget(item, frame)



