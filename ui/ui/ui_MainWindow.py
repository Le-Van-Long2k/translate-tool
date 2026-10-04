# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindowkPYKeC.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QLabel, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)
import resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(608, 200)
        Form.setMinimumSize(QSize(608, 200))
        Form.setMaximumSize(QSize(608, 200))
        self.mainLayout = QVBoxLayout(Form)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(24, 18, 24, 14)
        self.settingsLayout = QVBoxLayout()
        self.settingsLayout.setSpacing(12)
        self.settingsLayout.setObjectName(u"settingsLayout")
        self.engineLayout = QHBoxLayout()
        self.engineLayout.setSpacing(16)
        self.engineLayout.setObjectName(u"engineLayout")
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(170, 36))
        self.label.setMaximumSize(QSize(170, 36))
        font = QFont()
        font.setPointSize(18)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.engineLayout.addWidget(self.label)

        self.comboBox_translate_engine = QComboBox(Form)
        self.comboBox_translate_engine.addItem("")
        self.comboBox_translate_engine.addItem("")
        self.comboBox_translate_engine.setObjectName(u"comboBox_translate_engine")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_translate_engine.sizePolicy().hasHeightForWidth())
        self.comboBox_translate_engine.setSizePolicy(sizePolicy)
        self.comboBox_translate_engine.setMinimumSize(QSize(0, 36))
        self.comboBox_translate_engine.setMaximumSize(QSize(16777215, 36))
        self.comboBox_translate_engine.setFont(font)

        self.engineLayout.addWidget(self.comboBox_translate_engine)


        self.settingsLayout.addLayout(self.engineLayout)

        self.modeLayout = QHBoxLayout()
        self.modeLayout.setSpacing(16)
        self.modeLayout.setObjectName(u"modeLayout")
        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(170, 36))
        self.label_2.setMaximumSize(QSize(170, 36))
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.modeLayout.addWidget(self.label_2)

        self.comboBox_mode = QComboBox(Form)
        self.comboBox_mode.addItem("")
        self.comboBox_mode.addItem("")
        self.comboBox_mode.addItem("")
        self.comboBox_mode.addItem("")
        self.comboBox_mode.setObjectName(u"comboBox_mode")
        sizePolicy.setHeightForWidth(self.comboBox_mode.sizePolicy().hasHeightForWidth())
        self.comboBox_mode.setSizePolicy(sizePolicy)
        self.comboBox_mode.setMinimumSize(QSize(0, 36))
        self.comboBox_mode.setMaximumSize(QSize(16777215, 36))
        self.comboBox_mode.setFont(font)

        self.modeLayout.addWidget(self.comboBox_mode)


        self.settingsLayout.addLayout(self.modeLayout)


        self.mainLayout.addLayout(self.settingsLayout)

        self.separatorSpacer = QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.mainLayout.addItem(self.separatorSpacer)

        self.line = QFrame(Form)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Plain)

        self.mainLayout.addWidget(self.line)

        self.backendStatusLayout = QHBoxLayout()
        self.backendStatusLayout.setSpacing(8)
        self.backendStatusLayout.setObjectName(u"backendStatusLayout")
        self.backendSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.backendStatusLayout.addItem(self.backendSpacer)

        self.label_radio_check_backend = QLabel(Form)
        self.label_radio_check_backend.setObjectName(u"label_radio_check_backend")
        self.label_radio_check_backend.setMinimumSize(QSize(12, 30))
        self.label_radio_check_backend.setMaximumSize(QSize(12, 30))
        font1 = QFont()
        font1.setPointSize(11)
        self.label_radio_check_backend.setFont(font1)
        self.label_radio_check_backend.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.backendStatusLayout.addWidget(self.label_radio_check_backend)

        self.label_check_status_backend = QLabel(Form)
        self.label_check_status_backend.setObjectName(u"label_check_status_backend")
        self.label_check_status_backend.setMinimumSize(QSize(200, 30))
        self.label_check_status_backend.setMaximumSize(QSize(200, 30))
        self.label_check_status_backend.setFont(font1)
        self.label_check_status_backend.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.backendStatusLayout.addWidget(self.label_check_status_backend)


        self.mainLayout.addLayout(self.backendStatusLayout)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"OCR - D\u1ecbch thu\u1eadt", None))
        self.label.setText(QCoreApplication.translate("Form", u"C\u00f4ng c\u1ee5 d\u1ecbch", None))
        self.comboBox_translate_engine.setItemText(0, QCoreApplication.translate("Form", u"AI (model Hy-MT2)", None))
        self.comboBox_translate_engine.setItemText(1, QCoreApplication.translate("Form", u"Google D\u1ecbch", None))

        self.label_2.setText(QCoreApplication.translate("Form", u"Mode", None))
        self.comboBox_mode.setItemText(0, QCoreApplication.translate("Form", u"Click ch\u1ecdn mode", None))
        self.comboBox_mode.setItemText(1, QCoreApplication.translate("Form", u"D\u1ecbch truy\u1ec7n tranh", None))
        self.comboBox_mode.setItemText(2, QCoreApplication.translate("Form", u"D\u1ecbch m\u00e0n h\u00ecnh", None))
        self.comboBox_mode.setItemText(3, QCoreApplication.translate("Form", u"D\u1ecbch chat game", None))

        self.label_radio_check_backend.setText(QCoreApplication.translate("Form", u"\u25cf", None))
        self.label_check_status_backend.setText(QCoreApplication.translate("Form", u"Backend \u0111ang ch\u1ea1y", None))
    # retranslateUi

