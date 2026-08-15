# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindowFHazUe.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGraphicsView, QHBoxLayout,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1373, 792)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.Settings_btn = QPushButton(self.centralwidget)
        self.Settings_btn.setObjectName(u"Settings_btn")
        self.Settings_btn.setAutoFillBackground(False)
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentProperties))
        self.Settings_btn.setIcon(icon)

        self.horizontalLayout.addWidget(self.Settings_btn)

        self.Select_area_btn = QPushButton(self.centralwidget)
        self.Select_area_btn.setObjectName(u"Select_area_btn")
        self.Select_area_btn.setMaximumSize(QSize(200, 50))
        self.Select_area_btn.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self.horizontalLayout.addWidget(self.Select_area_btn)

        self.Start_btn = QPushButton(self.centralwidget)
        self.Start_btn.setObjectName(u"Start_btn")
        self.Start_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout.addWidget(self.Start_btn)

        self.Stop_btn = QPushButton(self.centralwidget)
        self.Stop_btn.setObjectName(u"Stop_btn")

        self.horizontalLayout.addWidget(self.Stop_btn)

        self.size_setting = QComboBox(self.centralwidget)
        self.size_setting.setObjectName(u"size_setting")

        self.horizontalLayout.addWidget(self.size_setting)

        self.source_lang_setting = QComboBox(self.centralwidget)
        self.source_lang_setting.addItem("")
        self.source_lang_setting.addItem("")
        self.source_lang_setting.setObjectName(u"source_lang_setting")

        self.horizontalLayout.addWidget(self.source_lang_setting)

        self.target_lang_setting = QComboBox(self.centralwidget)
        self.target_lang_setting.addItem("")
        self.target_lang_setting.setObjectName(u"target_lang_setting")

        self.horizontalLayout.addWidget(self.target_lang_setting)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.graphicsView = QGraphicsView(self.centralwidget)
        self.graphicsView.setObjectName(u"graphicsView")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(self.graphicsView.sizePolicy().hasHeightForWidth())
        self.graphicsView.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.graphicsView)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1373, 23))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.Settings_btn.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.Select_area_btn.setText(QCoreApplication.translate("MainWindow", u"Area", None))
        self.Start_btn.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.Stop_btn.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.source_lang_setting.setItemText(0, QCoreApplication.translate("MainWindow", u"Auto", None))
        self.source_lang_setting.setItemText(1, QCoreApplication.translate("MainWindow", u"English", None))

        self.target_lang_setting.setItemText(0, QCoreApplication.translate("MainWindow", u"Vietnamese", None))

    # retranslateUi

