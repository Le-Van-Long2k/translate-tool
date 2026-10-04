# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'box_chat_popupQjIhDZ.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QLayout, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_box_chat_translate_form(object):
    def setupUi(self, box_chat_translate_form):
        if not box_chat_translate_form.objectName():
            box_chat_translate_form.setObjectName(u"box_chat_translate_form")
        box_chat_translate_form.resize(735, 455)
        self.verticalLayout = QVBoxLayout(box_chat_translate_form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.result_label = QLabel(box_chat_translate_form)
        self.result_label.setObjectName(u"result_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.result_label.sizePolicy().hasHeightForWidth())
        self.result_label.setSizePolicy(sizePolicy)
        self.result_label.setMaximumSize(QSize(16777215, 16777215))
        font = QFont()
        font.setPointSize(14)
        self.result_label.setFont(font)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.result_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.result_label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.font_size_label = QLabel(box_chat_translate_form)
        self.font_size_label.setObjectName(u"font_size_label")
        self.font_size_label.setMinimumSize(QSize(50, 0))
        self.font_size_label.setMaximumSize(QSize(16777215, 50))
        font1 = QFont()
        font1.setPointSize(12)
        self.font_size_label.setFont(font1)

        self.horizontalLayout.addWidget(self.font_size_label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.font_size_comboBox = QComboBox(box_chat_translate_form)
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.addItem("")
        self.font_size_comboBox.setObjectName(u"font_size_comboBox")
        self.font_size_comboBox.setMinimumSize(QSize(80, 0))
        self.font_size_comboBox.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout.addWidget(self.font_size_comboBox)

        self.horizontalSpacer = QSpacerItem(30, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(box_chat_translate_form)

        QMetaObject.connectSlotsByName(box_chat_translate_form)
    # setupUi

    def retranslateUi(self, box_chat_translate_form):
        box_chat_translate_form.setWindowTitle(QCoreApplication.translate("box_chat_translate_form", u"Form", None))
        self.result_label.setText(QCoreApplication.translate("box_chat_translate_form", u"TextLabel", None))
        self.font_size_label.setText(QCoreApplication.translate("box_chat_translate_form", u"Size", None))
        self.font_size_comboBox.setItemText(0, QCoreApplication.translate("box_chat_translate_form", u"10", None))
        self.font_size_comboBox.setItemText(1, QCoreApplication.translate("box_chat_translate_form", u"12", None))
        self.font_size_comboBox.setItemText(2, QCoreApplication.translate("box_chat_translate_form", u"14", None))
        self.font_size_comboBox.setItemText(3, QCoreApplication.translate("box_chat_translate_form", u"16", None))
        self.font_size_comboBox.setItemText(4, QCoreApplication.translate("box_chat_translate_form", u"18", None))
        self.font_size_comboBox.setItemText(5, QCoreApplication.translate("box_chat_translate_form", u"20", None))
        self.font_size_comboBox.setItemText(6, QCoreApplication.translate("box_chat_translate_form", u"22", None))
        self.font_size_comboBox.setItemText(7, QCoreApplication.translate("box_chat_translate_form", u"24", None))
        self.font_size_comboBox.setItemText(8, QCoreApplication.translate("box_chat_translate_form", u"26", None))
        self.font_size_comboBox.setItemText(9, QCoreApplication.translate("box_chat_translate_form", u"28", None))
        self.font_size_comboBox.setItemText(10, QCoreApplication.translate("box_chat_translate_form", u"30", None))
        self.font_size_comboBox.setItemText(11, QCoreApplication.translate("box_chat_translate_form", u"32", None))
        self.font_size_comboBox.setItemText(12, QCoreApplication.translate("box_chat_translate_form", u"34", None))
        self.font_size_comboBox.setItemText(13, QCoreApplication.translate("box_chat_translate_form", u"36", None))
        self.font_size_comboBox.setItemText(14, QCoreApplication.translate("box_chat_translate_form", u"38", None))
        self.font_size_comboBox.setItemText(15, QCoreApplication.translate("box_chat_translate_form", u"40", None))

    # retranslateUi

