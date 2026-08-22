# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'translate_comic_popupuEHdrq.ui'
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
from PySide6.QtWidgets import (QApplication, QGraphicsView, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_ComicPopup(object):
    def setupUi(self, ComicPopup):
        if not ComicPopup.objectName():
            ComicPopup.setObjectName(u"ComicPopup")
        ComicPopup.resize(1101, 891)
        self.verticalLayout = QVBoxLayout(ComicPopup)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.title_label = QLabel(ComicPopup)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setStyleSheet(u"font-weight: 600; font-size: 14px; color: #F8FAFC;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.title_label)

        self.graphicsView = QGraphicsView(ComicPopup)
        self.graphicsView.setObjectName(u"graphicsView")

        self.verticalLayout.addWidget(self.graphicsView)

        self.select_btn = QPushButton(ComicPopup)
        self.select_btn.setObjectName(u"select_btn")

        self.verticalLayout.addWidget(self.select_btn)

        self.download_btn = QPushButton(ComicPopup)
        self.download_btn.setObjectName(u"download_btn")

        self.verticalLayout.addWidget(self.download_btn)


        self.retranslateUi(ComicPopup)

        QMetaObject.connectSlotsByName(ComicPopup)
    # setupUi

    def retranslateUi(self, ComicPopup):
        ComicPopup.setWindowTitle(QCoreApplication.translate("ComicPopup", u"Translate Comic", None))
        self.title_label.setText(QCoreApplication.translate("ComicPopup", u"Translate Comic", None))
        self.select_btn.setText(QCoreApplication.translate("ComicPopup", u"Select image(s)", None))
        self.download_btn.setText(QCoreApplication.translate("ComicPopup", u"Download", None))
    # retranslateUi

