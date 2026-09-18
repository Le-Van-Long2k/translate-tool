# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'comic_popupmFKItn.ui'
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
from PySide6.QtWidgets import (QApplication, QGraphicsView, QHBoxLayout, QLabel,
    QLayout, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_form_comic(object):
    def setupUi(self, form_comic):
        if not form_comic.objectName():
            form_comic.setObjectName(u"form_comic")
        form_comic.resize(1056, 890)
        self.verticalLayout_2 = QVBoxLayout(form_comic)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        self.graphicsView = QGraphicsView(form_comic)
        self.graphicsView.setObjectName(u"graphicsView")

        self.verticalLayout.addWidget(self.graphicsView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.select_img_btn = QPushButton(form_comic)
        self.select_img_btn.setObjectName(u"select_img_btn")
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setPointSize(14)
        self.select_img_btn.setFont(font)

        self.horizontalLayout.addWidget(self.select_img_btn)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.status_label = QLabel(form_comic)
        self.status_label.setObjectName(u"status_label")
        font1 = QFont()
        font1.setPointSize(14)
        self.status_label.setFont(font1)

        self.horizontalLayout.addWidget(self.status_label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.download_btn = QPushButton(form_comic)
        self.download_btn.setObjectName(u"download_btn")
        self.download_btn.setFont(font1)

        self.horizontalLayout.addWidget(self.download_btn)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addLayout(self.verticalLayout)


        self.retranslateUi(form_comic)

        QMetaObject.connectSlotsByName(form_comic)
    # setupUi

    def retranslateUi(self, form_comic):
        form_comic.setWindowTitle(QCoreApplication.translate("form_comic", u"Dịch truyện tranh", None))
        self.select_img_btn.setText(QCoreApplication.translate("form_comic", u"Chọn ảnh", None))
        self.status_label.setText(QCoreApplication.translate("form_comic", u"Vui lòng chọn ảnh", None))
        self.download_btn.setText(QCoreApplication.translate("form_comic", u"Tải xuống", None))
    # retranslateUi

