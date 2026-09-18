# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'splash_screen.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QProgressBar,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)
import resources_rc

class Ui_SplashScreen(object):
    def setupUi(self, SplashScreen):
        if not SplashScreen.objectName():
            SplashScreen.setObjectName(u"SplashScreen")
        SplashScreen.resize(450, 200)
        SplashScreen.setMinimumSize(QSize(450, 200))
        SplashScreen.setMaximumSize(QSize(450, 200))
        SplashScreen.setAutoFillBackground(False)
        SplashScreen.setStyleSheet(u"\n"
"\n"
"QWidget#SplashScreen {\n"
"    background: transparent;\n"
"}\n"
"\n"
"QWidget#backgroundWidget {\n"
"    background: transparent;\n"
"    border-image: url(:/icons/splash_background.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"\n"
"QWidget#darkOverlay {\n"
"    background-color: rgba(0, 0, 0, 115);\n"
"}\n"
"\n"
"QWidget#contentWidget {\n"
"    background: transparent;\n"
"}\n"
"\n"
"QLabel {\n"
"    background: transparent;\n"
"}\n"
"\n"
"QLabel#labelTitle {\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"QLabel#labelDescription {\n"
"    color: #e2e8f0;\n"
"}\n"
"\n"
"QLabel#labelStatus {\n"
"    color: #f8fafc;\n"
"}\n"
"\n"
"QLabel#labelVersion {\n"
"    color: #cbd5e1;\n"
"}\n"
"\n"
"QProgressBar#progressBar {\n"
"    background-color: rgba(255, 255, 255, 45);\n"
"    border: none;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QProgressBar#progressBar::chunk {\n"
"    background-color: #60a5fa;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"   ")
        self.gridLayout = QGridLayout(SplashScreen)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.backgroundWidget = QWidget(SplashScreen)
        self.backgroundWidget.setObjectName(u"backgroundWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.backgroundWidget.sizePolicy().hasHeightForWidth())
        self.backgroundWidget.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.backgroundWidget, 0, 0, 1, 1)

        self.darkOverlay = QWidget(SplashScreen)
        self.darkOverlay.setObjectName(u"darkOverlay")
        sizePolicy.setHeightForWidth(self.darkOverlay.sizePolicy().hasHeightForWidth())
        self.darkOverlay.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.darkOverlay, 0, 0, 1, 1)

        self.contentWidget = QWidget(SplashScreen)
        self.contentWidget.setObjectName(u"contentWidget")
        sizePolicy.setHeightForWidth(self.contentWidget.sizePolicy().hasHeightForWidth())
        self.contentWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.contentWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(30, 25, 30, 18)
        self.labelTitle = QLabel(self.contentWidget)
        self.labelTitle.setObjectName(u"labelTitle")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.labelTitle.sizePolicy().hasHeightForWidth())
        self.labelTitle.setSizePolicy(sizePolicy1)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.labelTitle.setFont(font)
        self.labelTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.labelTitle)

        self.labelDescription = QLabel(self.contentWidget)
        self.labelDescription.setObjectName(u"labelDescription")
        sizePolicy1.setHeightForWidth(self.labelDescription.sizePolicy().hasHeightForWidth())
        self.labelDescription.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setPointSize(10)
        self.labelDescription.setFont(font1)
        self.labelDescription.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.labelDescription)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.labelStatus = QLabel(self.contentWidget)
        self.labelStatus.setObjectName(u"labelStatus")
        sizePolicy1.setHeightForWidth(self.labelStatus.sizePolicy().hasHeightForWidth())
        self.labelStatus.setSizePolicy(sizePolicy1)
        self.labelStatus.setFont(font1)
        self.labelStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.labelStatus)

        self.progressBar = QProgressBar(self.contentWidget)
        self.progressBar.setObjectName(u"progressBar")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progressBar.setSizePolicy(sizePolicy2)
        self.progressBar.setMinimumSize(QSize(0, 8))
        self.progressBar.setMaximumSize(QSize(16777215, 8))
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)

        self.verticalLayout.addWidget(self.progressBar)

        self.verticalSpacerBottom = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacerBottom)

        self.labelVersion = QLabel(self.contentWidget)
        self.labelVersion.setObjectName(u"labelVersion")
        sizePolicy1.setHeightForWidth(self.labelVersion.sizePolicy().hasHeightForWidth())
        self.labelVersion.setSizePolicy(sizePolicy1)
        font2 = QFont()
        font2.setPointSize(8)
        self.labelVersion.setFont(font2)
        self.labelVersion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.labelVersion)


        self.gridLayout.addWidget(self.contentWidget, 0, 0, 1, 1)


        self.retranslateUi(SplashScreen)

        QMetaObject.connectSlotsByName(SplashScreen)
    # setupUi

    def retranslateUi(self, SplashScreen):
        SplashScreen.setWindowTitle(QCoreApplication.translate("SplashScreen", u"OCR Translator", None))
        self.labelTitle.setText(QCoreApplication.translate("SplashScreen", u"OCR Translator", None))
        self.labelDescription.setText(QCoreApplication.translate("SplashScreen", u"D\u1ecbch m\u00e0n h\u00ecnh \u2022 Chat \u2022 Truy\u1ec7n", None))
        self.labelStatus.setText(QCoreApplication.translate("SplashScreen", u"\u0110ang kh\u1edfi \u0111\u1ed9ng \u1ee9ng d\u1ee5ng...", None))
        self.labelVersion.setText(QCoreApplication.translate("SplashScreen", u"Phi\u00ean b\u1ea3n 1.0", None))
    # retranslateUi

