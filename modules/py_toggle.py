#################################################################################
#Copyright (c) 2023, MwoNuZzz
#All rights reserved.
#
#This source code is licensed under the GNU General Public License as found in the
#LICENSE file in the root directory of this source tree.
#################################################################################

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class PyToggle(QCheckBox):
    def __init__(self,
                 width=40,
                 height=20,
                 tooltip="",
                 bg_color="#777",
                 circle_color="#DDD",
                 active_color="#FF79C6",
                 animation_curve=QEasingCurve.OutBounce
                 ):
        QCheckBox.__init__(self)

        # SET DEFAULT PARAMETERS
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)

        # COLORS
        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color

        # CREATE ANIMATION
        self._circle_position = 3
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(500)

        # CONNECT STATE CHANGED
        self.stateChanged.connect(self.start_transition)

    # CREATE NEW SET AND GET PROPERTY
    @pyqtProperty(float)  # GET
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def start_transition(self, value):
        self.animation.stop()  # stop animation if running
        if value:
            self.animation.setEndValue(self.width() - 26)
        else:
            self.animation.setEndValue(3)

        # START ANIMATION
        self.animation.start()

        #print(f"Status : {self.isChecked()}")

    # SET NEW HIT AREA
    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    # DRAW NEW ITEMS
    def paintEvent(self, e):
        # SET PAINTER
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # SET AS NO PEN
        p.setPen(Qt.NoPen)

        # DRAW RECTANGLE
        rect = QRect(0, 0, self.width(), self.height())

        # CHECK IF IT IS CHECKED
        if not self.isChecked():
            # DRAW BG
            p.setBrush(QColor(self._bg_color))
            p.drawRoundedRect(0, 0, rect.width(), rect.height(), self.height() / 2, self.height() / 2)

            # DRAW CIRCLE
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._circle_position, 3, self.height()-6, self.height()-6)
        else:
            # DRAW BG
            p.setBrush(QColor(self._active_color))
            p.drawRoundedRect(0, 0, rect.width(), rect.height(), self.height() / 2, self.height() / 2 )

            # DRAW CIRCLE
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._circle_position+9, 3, self.height()-6, self.height()-6)

        # END DRAW
        p.end()
