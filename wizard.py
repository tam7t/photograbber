# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ourbunny
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Form implementation generated from reading ui file 'wizard.ui'
#
# Created: Mon Mar 11 17:55:52 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.1

from PySide import QtCore, QtGui

class Ui_Wizard(object):
    def setupUi(self, Wizard):
        Wizard.setObjectName("Wizard")
        Wizard.resize(500, 360)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Wizard.sizePolicy().hasHeightForWidth())
        Wizard.setSizePolicy(sizePolicy)
        Wizard.setMaximumSize(QtCore.QSize(524287, 524287))
        Wizard.setWizardStyle(QtGui.QWizard.ModernStyle)
        Wizard.setOptions(QtGui.QWizard.NoBackButtonOnStartPage|QtGui.QWizard.NoCancelButton|QtGui.QWizard.NoDefaultButton)
        self.wizardPageLogin = QtGui.QWizardPage()
        self.wizardPageLogin.setSubTitle("")
        self.wizardPageLogin.setObjectName("wizardPageLogin")
        self.gridLayout_1 = QtGui.QGridLayout(self.wizardPageLogin)
        self.gridLayout_1.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.gridLayout_1.setObjectName("gridLayout_1")
        self.loginPushButton = QtGui.QPushButton(self.wizardPageLogin)
        self.loginPushButton.setDefault(True)
        self.loginPushButton.setObjectName("loginPushButton")
        self.gridLayout_1.addWidget(self.loginPushButton, 1, 0, 1, 1)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.enterTokenLabel = QtGui.QLabel(self.wizardPageLogin)
        self.enterTokenLabel.setObjectName("enterTokenLabel")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.enterTokenLabel)
        self.enterTokenLineEdit = QtGui.QLineEdit(self.wizardPageLogin)
        self.enterTokenLineEdit.setObjectName("enterTokenLineEdit")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.enterTokenLineEdit)
        self.gridLayout_1.addLayout(self.formLayout, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_1.addItem(spacerItem, 0, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_1.addItem(spacerItem1, 3, 0, 1, 1)
        self.aboutPushButton = QtGui.QPushButton(self.wizardPageLogin)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.aboutPushButton.sizePolicy().hasHeightForWidth())
        self.aboutPushButton.setSizePolicy(sizePolicy)
        self.aboutPushButton.setAutoDefault(True)
        self.aboutPushButton.setDefault(False)
        self.aboutPushButton.setFlat(False)
        self.aboutPushButton.setObjectName("aboutPushButton")
        self.gridLayout_1.addWidget(self.aboutPushButton, 5, 0, 1, 1)
        Wizard.addPage(self.wizardPageLogin)
        self.wizardPageTarget = QtGui.QWizardPage()
        self.wizardPageTarget.setObjectName("wizardPageTarget")
        self.gridLayout = QtGui.QGridLayout(self.wizardPageTarget)
        self.gridLayout.setObjectName("gridLayout")
        self.targetTreeWidget = QtGui.QTreeWidget(self.wizardPageTarget)
        self.targetTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.targetTreeWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.targetTreeWidget.setAutoExpandDelay(-1)
        self.targetTreeWidget.setObjectName("targetTreeWidget")
        item_0 = QtGui.QTreeWidgetItem(self.targetTreeWidget)
        item_0 = QtGui.QTreeWidgetItem(self.targetTreeWidget)
        item_0 = QtGui.QTreeWidgetItem(self.targetTreeWidget)
        self.targetTreeWidget.header().setVisible(False)
        self.targetTreeWidget.header().setHighlightSections(False)
        self.gridLayout.addWidget(self.targetTreeWidget, 1, 0, 1, 1)
        self.allPhotosCheckBox = QtGui.QCheckBox(self.wizardPageTarget)
        self.allPhotosCheckBox.setTristate(False)
        self.allPhotosCheckBox.setObjectName("allPhotosCheckBox")
        self.gridLayout.addWidget(self.allPhotosCheckBox, 2, 0, 1, 1)
        self.allAlbumsCheckBox = QtGui.QCheckBox(self.wizardPageTarget)
        self.allAlbumsCheckBox.setObjectName("allAlbumsCheckBox")
        self.gridLayout.addWidget(self.allAlbumsCheckBox, 3, 0, 1, 1)
        self.fullAlbumsCheckBox = QtGui.QCheckBox(self.wizardPageTarget)
        self.fullAlbumsCheckBox.setObjectName("fullAlbumsCheckBox")
        self.gridLayout.addWidget(self.fullAlbumsCheckBox, 4, 0, 1, 1)
        self.commentsCheckBox = QtGui.QCheckBox(self.wizardPageTarget)
        self.commentsCheckBox.setObjectName("commentsCheckBox")
        self.gridLayout.addWidget(self.commentsCheckBox, 5, 0, 1, 1)
        self.advancedPushButton = QtGui.QPushButton(self.wizardPageTarget)
        self.advancedPushButton.setSizePolicy(sizePolicy)
        self.advancedPushButton.setAutoDefault(True)
        self.advancedPushButton.setDefault(False)
        self.advancedPushButton.setFlat(False)
        self.advancedPushButton.setObjectName("advancedPushButton")
        self.gridLayout.addWidget(self.advancedPushButton, 6, 0, 1, 1)
        Wizard.addPage(self.wizardPageTarget)
        self.wizardPageLocation = QtGui.QWizardPage()
        self.wizardPageLocation.setObjectName("wizardPageLocation")
        self.gridLayout_4 = QtGui.QGridLayout(self.wizardPageLocation)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.pathLineEdit = QtGui.QLineEdit(self.wizardPageLocation)
        self.pathLineEdit.setObjectName("pathLineEdit")
        self.pathLineEdit.setReadOnly(True)
        self.gridLayout_4.addWidget(self.pathLineEdit, 1, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem2, 0, 0, 1, 2)
        spacerItem3 = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem3, 2, 0, 1, 2)
        self.browseToolButton = QtGui.QToolButton(self.wizardPageLocation)
        self.browseToolButton.setObjectName("browseToolButton")
        self.gridLayout_4.addWidget(self.browseToolButton, 1, 1, 1, 1)
        Wizard.addPage(self.wizardPageLocation)

        self.retranslateUi(Wizard)
        QtCore.QMetaObject.connectSlotsByName(Wizard)
        Wizard.setTabOrder(self.loginPushButton, self.enterTokenLineEdit)
        Wizard.setTabOrder(self.enterTokenLineEdit, self.targetTreeWidget)
        Wizard.setTabOrder(self.targetTreeWidget, self.allPhotosCheckBox)
        Wizard.setTabOrder(self.allPhotosCheckBox, self.allAlbumsCheckBox)
        Wizard.setTabOrder(self.allAlbumsCheckBox, self.fullAlbumsCheckBox)
        Wizard.setTabOrder(self.fullAlbumsCheckBox, self.commentsCheckBox)
        Wizard.setTabOrder(self.commentsCheckBox, self.advancedPushButton)
        Wizard.setTabOrder(self.advancedPushButton, self.pathLineEdit)
        Wizard.setTabOrder(self.pathLineEdit, self.browseToolButton)

    def retranslateUi(self, Wizard):
        Wizard.setWindowTitle(QtGui.QApplication.translate("Wizard", "PhotoGrabber", None, QtGui.QApplication.UnicodeUTF8))
        import res
        Wizard.setWindowIcon(QtGui.QIcon(res.getpath('dep/pg.png')))
        self.wizardPageLogin.setTitle(QtGui.QApplication.translate("Wizard", "Login to Facebook", None, QtGui.QApplication.UnicodeUTF8))
        self.loginPushButton.setText(QtGui.QApplication.translate("Wizard", "Login", None, QtGui.QApplication.UnicodeUTF8))
        self.enterTokenLabel.setText(QtGui.QApplication.translate("Wizard", "Enter Token", None, QtGui.QApplication.UnicodeUTF8))
        self.aboutPushButton.setText(QtGui.QApplication.translate("Wizard", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.wizardPageTarget.setTitle(QtGui.QApplication.translate("Wizard", "Select Target(s)", None, QtGui.QApplication.UnicodeUTF8))
        self.targetTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("Wizard", "Target", None, QtGui.QApplication.UnicodeUTF8))
        __sortingEnabled = self.targetTreeWidget.isSortingEnabled()
        self.targetTreeWidget.setSortingEnabled(False)
        self.targetTreeWidget.topLevelItem(0).setText(0, QtGui.QApplication.translate("Wizard", "Friends", None, QtGui.QApplication.UnicodeUTF8))
        self.targetTreeWidget.topLevelItem(1).setText(0, QtGui.QApplication.translate("Wizard", "Likes", None, QtGui.QApplication.UnicodeUTF8))
        self.targetTreeWidget.setSortingEnabled(__sortingEnabled)
        self.allPhotosCheckBox.setText(QtGui.QApplication.translate("Wizard", "All tagged photos", None, QtGui.QApplication.UnicodeUTF8))
        self.fullAlbumsCheckBox.setText(QtGui.QApplication.translate("Wizard", "Full albums of tagged photos", None, QtGui.QApplication.UnicodeUTF8))
        self.commentsCheckBox.setText(QtGui.QApplication.translate("Wizard", "Complete comment/tag data", None, QtGui.QApplication.UnicodeUTF8))
        self.allAlbumsCheckBox.setText(QtGui.QApplication.translate("Wizard", "Uploaded albums", None, QtGui.QApplication.UnicodeUTF8))
        self.advancedPushButton.setText(QtGui.QApplication.translate("Wizard", "Advanced", None, QtGui.QApplication.UnicodeUTF8))

        self.wizardPageLocation.setTitle(QtGui.QApplication.translate("Wizard", "Select Download Location", None, QtGui.QApplication.UnicodeUTF8))
        self.browseToolButton.setText(QtGui.QApplication.translate("Wizard", "Browse ...", None, QtGui.QApplication.UnicodeUTF8))

