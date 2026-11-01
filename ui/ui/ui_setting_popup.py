# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'setting_popuptUXenn.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QLabel, QPushButton,
    QSizePolicy, QTextEdit, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(725, 363)
        self.promt_llm_textEdit = QTextEdit(Form)
        self.promt_llm_textEdit.setObjectName(u"promt_llm_textEdit")
        self.promt_llm_textEdit.setGeometry(QRect(240, 10, 481, 200))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.promt_llm_textEdit.sizePolicy().hasHeightForWidth())
        self.promt_llm_textEdit.setSizePolicy(sizePolicy)
        self.promt_llm_textEdit.setMinimumSize(QSize(0, 200))
        self.promt_llm_textEdit.setMaximumSize(QSize(16777215, 200))
        self.promt_label = QLabel(Form)
        self.promt_label.setObjectName(u"promt_label")
        self.promt_label.setGeometry(QRect(20, 10, 200, 200))
        sizePolicy.setHeightForWidth(self.promt_label.sizePolicy().hasHeightForWidth())
        self.promt_label.setSizePolicy(sizePolicy)
        self.promt_label.setMinimumSize(QSize(200, 200))
        self.promt_label.setMaximumSize(QSize(200, 50))
        font = QFont()
        font.setPointSize(14)
        self.promt_label.setFont(font)
        self.source_label = QLabel(Form)
        self.source_label.setObjectName(u"source_label")
        self.source_label.setGeometry(QRect(20, 250, 200, 26))
        self.source_label.setMinimumSize(QSize(200, 10))
        self.source_label.setFont(font)
        self.source_language_comboBox = QComboBox(Form)
        self.source_language_comboBox.addItem("")
        self.source_language_comboBox.addItem("")
        self.source_language_comboBox.addItem("")
        self.source_language_comboBox.addItem("")
        self.source_language_comboBox.addItem("")
        self.source_language_comboBox.setObjectName(u"source_language_comboBox")
        self.source_language_comboBox.setGeometry(QRect(240, 250, 150, 36))
        self.source_language_comboBox.setFont(font)
        self.setting_apply_btn = QPushButton(Form)
        self.setting_apply_btn.setObjectName(u"setting_apply_btn")
        self.setting_apply_btn.setGeometry(QRect(600, 310, 111, 41))
        self.setting_apply_btn.setFont(font)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.promt_label.setText(QCoreApplication.translate("Form", u"Promt LLM", None))
        self.source_label.setText(QCoreApplication.translate("Form", u"Ng\u00f4n ng\u1eef ngu\u1ed3n", None))
        self.source_language_comboBox.setItemText(0, QCoreApplication.translate("Form", u"T\u1ef1 \u0111\u1ed9ng", None))
        self.source_language_comboBox.setItemText(1, QCoreApplication.translate("Form", u"Ti\u1ebfng Anh", None))
        self.source_language_comboBox.setItemText(2, QCoreApplication.translate("Form", u"Ti\u1ebfng Trung", None))
        self.source_language_comboBox.setItemText(3, QCoreApplication.translate("Form", u"Ti\u1ebfng H\u00e0n", None))
        self.source_language_comboBox.setItemText(4, QCoreApplication.translate("Form", u"Ti\u1ebfng Nh\u1eadt", None))

        self.setting_apply_btn.setText(QCoreApplication.translate("Form", u"Apply", None))
    # retranslateUi

