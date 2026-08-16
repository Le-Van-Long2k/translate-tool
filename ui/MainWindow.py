# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindowmdcuaX.ui'
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
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.Settings_btn.sizePolicy().hasHeightForWidth())
        self.Settings_btn.setSizePolicy(sizePolicy1)
        self.Settings_btn.setMinimumSize(QSize(50, 50))
        self.Settings_btn.setAutoFillBackground(False)
        icon = QIcon()
        icon.addFile(u"icons/setting.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.Settings_btn.setIcon(icon)
        self.Settings_btn.setIconSize(QSize(32, 32))

        self.horizontalLayout.addWidget(self.Settings_btn)

        self.Select_area_btn = QPushButton(self.centralwidget)
        self.Select_area_btn.setObjectName(u"Select_area_btn")
        sizePolicy1.setHeightForWidth(self.Select_area_btn.sizePolicy().hasHeightForWidth())
        self.Select_area_btn.setSizePolicy(sizePolicy1)
        self.Select_area_btn.setMinimumSize(QSize(50, 50))
        self.Select_area_btn.setMaximumSize(QSize(16777215, 16777215))
        self.Select_area_btn.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        icon1 = QIcon()
        icon1.addFile(u"icons/crop.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.Select_area_btn.setIcon(icon1)
        self.Select_area_btn.setIconSize(QSize(32, 32))

        self.horizontalLayout.addWidget(self.Select_area_btn)

        self.start_stop_btn = QPushButton(self.centralwidget)
        self.start_stop_btn.setObjectName(u"start_stop_btn")
        sizePolicy1.setHeightForWidth(self.start_stop_btn.sizePolicy().hasHeightForWidth())
        self.start_stop_btn.setSizePolicy(sizePolicy1)
        self.start_stop_btn.setMinimumSize(QSize(50, 50))
        self.start_stop_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        icon2 = QIcon()
        icon2.addFile(u"icons/start.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.start_stop_btn.setIcon(icon2)
        self.start_stop_btn.setIconSize(QSize(32, 32))

        self.horizontalLayout.addWidget(self.start_stop_btn)

        self.target_lang_setting = QComboBox(self.centralwidget)
        self.target_lang_setting.addItem("")
        self.target_lang_setting.setObjectName(u"target_lang_setting")
        self.target_lang_setting.setMinimumSize(QSize(100, 30))
        self.target_lang_setting.setMaximumSize(QSize(200, 16777215))

        self.horizontalLayout.addWidget(self.target_lang_setting)

        self.size_setting = QComboBox(self.centralwidget)
        self.size_setting.setObjectName(u"size_setting")
        self.size_setting.setMinimumSize(QSize(50, 30))
        self.size_setting.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout.addWidget(self.size_setting)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.graphicsView = QGraphicsView(self.centralwidget)
        self.graphicsView.setObjectName(u"graphicsView")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(1)
        sizePolicy2.setHeightForWidth(self.graphicsView.sizePolicy().hasHeightForWidth())
        self.graphicsView.setSizePolicy(sizePolicy2)

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
#if QT_CONFIG(tooltip)
        self.Settings_btn.setToolTip(QCoreApplication.translate("MainWindow", u"Settings", None))
#endif // QT_CONFIG(tooltip)
        self.Settings_btn.setText("")
#if QT_CONFIG(tooltip)
        self.Select_area_btn.setToolTip(QCoreApplication.translate("MainWindow", u"Select area", None))
#endif // QT_CONFIG(tooltip)
        self.Select_area_btn.setText("")
#if QT_CONFIG(tooltip)
        self.start_stop_btn.setToolTip(QCoreApplication.translate("MainWindow", u"Start OCR", None))
#endif // QT_CONFIG(tooltip)
        self.start_stop_btn.setText("")
        self.target_lang_setting.setItemText(0, QCoreApplication.translate("MainWindow", u"Ti\u1ebfng Vi\u1ec7t", None))

#if QT_CONFIG(tooltip)
        self.target_lang_setting.setToolTip(QCoreApplication.translate("MainWindow", u"Translate to", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.size_setting.setToolTip(QCoreApplication.translate("MainWindow", u"Scale text", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

