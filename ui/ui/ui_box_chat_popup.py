# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'box_chat_popupBapltp.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QSizePolicy,
    QWidget)

class Ui_box_chat_translate_form(object):
    def setupUi(self, box_chat_translate_form):
        if not box_chat_translate_form.objectName():
            box_chat_translate_form.setObjectName(u"box_chat_translate_form")
        box_chat_translate_form.resize(597, 193)
        self.gridLayout = QGridLayout(box_chat_translate_form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.result_label = QLabel(box_chat_translate_form)
        self.result_label.setObjectName(u"result_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.result_label.sizePolicy().hasHeightForWidth())
        self.result_label.setSizePolicy(sizePolicy)
        self.result_label.setMaximumSize(QSize(521, 241))
        font = QFont()
        font.setPointSize(14)
        self.result_label.setFont(font)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.result_label.setWordWrap(True)

        self.gridLayout.addWidget(self.result_label, 1, 0, 1, 1)


        self.retranslateUi(box_chat_translate_form)

        QMetaObject.connectSlotsByName(box_chat_translate_form)
    # setupUi

    def retranslateUi(self, box_chat_translate_form):
        box_chat_translate_form.setWindowTitle(QCoreApplication.translate("box_chat_translate_form", u"Form", None))
        self.result_label.setText(QCoreApplication.translate("box_chat_translate_form", u"TextLabel", None))
    # retranslateUi

