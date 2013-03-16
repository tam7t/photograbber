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

# Req for building on Win7
# Python 2.7.3 - win32
# PySide 1.1.2 win32 py2.7
# pywin32-218.win32-py2.7
# PyInstaller

import sys
from PySide import QtCore, QtGui
from wizard import Ui_Wizard

import facebook
import helpers
import downloader

import logging
import threading

class ControlMainWindow(QtGui.QWizard):
    def __init__(self, parent=None):
        super(ControlMainWindow, self).__init__(parent)
        self.ui =  Ui_Wizard()
        self.ui.setupUi(self)

        # data
        self.logger = logging.getLogger('PhotoGrabberGUI')
        self.helper = None
        self.token = ''
        self.config = {}
        self.config['sleep_time'] = 0.1
        self.advancedTarget = ""

        # connect signals and validate pages
        self.ui.aboutPushButton.clicked.connect(self.aboutPressed)
        self.ui.loginPushButton.clicked.connect(self.loginPressed)
        self.ui.advancedPushButton.clicked.connect(self.advancedPressed)
        self.ui.browseToolButton.clicked.connect(self.openFolder)
        self.ui.wizardPageLogin.registerField("token*", self.ui.enterTokenLineEdit)
        self.ui.wizardPageLogin.validatePage = self.validateLogin
        self.ui.wizardPageTarget.validatePage = self.validateTarget
        self.ui.wizardPageLocation.validatePage = self.beginDownload

    def aboutPressed(self):
        QtGui.QMessageBox.about(self, "About", "PhotoGrabber v100\n(C) 2013 Ourbunny\nGPLv3\n\nphotograbber.com\nFor full licensing information view the LICENSE.txt file.")

    def loginPressed(self):
        facebook.request_token()

    def advancedPressed(self):
        self.advancedTarget, ok = QtGui.QInputDialog.getText(self, "Specify Target", "ID/username of target", text=self.advancedTarget)
        if ok:
            self.ui.targetTreeWidget.setEnabled(False)
        else:
            self.ui.targetTreeWidget.setEnabled(True)
        
    def validateLogin(self):
        # present progress modal
        progress = QtGui.QProgressDialog("Logging in...", "Abort", 0, 5, parent=self)
        #QtGui.qApp.processEvents() is unnecessary when dialog is Modal
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.show()

        # attempt to login
        self.token = self.ui.enterTokenLineEdit.text()
        try:
            if not self.token.isalnum(): raise Exception("Please insert a valid token")
            self.helper = helpers.Helper(facebook.GraphAPI(self.token))
            my_info = self.helper.get_me()
        except Exception as e:
            progress.close()
            QtGui.QMessageBox.warning(self, "PhotoGrabber", unicode(e))
            return False

        progress.setValue(1)
        if progress.wasCanceled(): return False
        
        # clear list
        self.ui.targetTreeWidget.topLevelItem(0).takeChildren()
        self.ui.targetTreeWidget.topLevelItem(1).takeChildren()
        self.ui.targetTreeWidget.topLevelItem(2).takeChildren()
        
        # populate list
        try:
            friends = self.helper.get_friends('me')
        except Exception as e:
            progress.close()
            QtGui.QMessageBox.warning(self, "PhotoGrabber", unicode(e))
            return False
        
        progress.setValue(2)
        if progress.wasCanceled(): return False
        
        try:
            likes = self.helper.get_likes('me')
        except Exception as e:
            progress.close()
            QtGui.QMessageBox.warning(self, "PhotoGrabber", unicode(e))
            return False
        
        progress.setValue(3)
        if progress.wasCanceled(): return False
        
        try:
            subscriptions = self.helper.get_subscriptions('me')
        except Exception as e:
            progress.close()
            QtGui.QMessageBox.warning(self, "PhotoGrabber", unicode(e))
            return False
            
        progress.setValue(4)
        if progress.wasCanceled(): return False
        
        item = QtGui.QTreeWidgetItem()
        item.setText(0, my_info['name'])
        item.setData(1, 0, my_info)
        self.ui.targetTreeWidget.topLevelItem(0).addChild(item)
        
        for p in friends:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, p['name'])
            item.setData(1, 0, p)
            self.ui.targetTreeWidget.topLevelItem(0).addChild(item)

        for p in likes:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, p['name'])
            item.setData(1, 0, p)
            self.ui.targetTreeWidget.topLevelItem(1).addChild(item)

        for p in subscriptions:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, p['name'])
            item.setData(1, 0, p)
            self.ui.targetTreeWidget.topLevelItem(2).addChild(item)

        progress.setValue(5)
        progress.close()
        return True
    
    def validateTarget(self):
        # setup next page to current directory
        self.config['dir'] = QtGui.QFileDialog().directory().absolutePath()
        self.ui.pathLineEdit.setText(self.config['dir'])
        
        self.config['u'] = self.ui.allAlbumsCheckBox.isChecked()
        self.config['t'] = self.ui.allPhotosCheckBox.isChecked()
        self.config['c'] = self.ui.commentsCheckBox.isChecked()
        self.config['a'] = self.ui.fullAlbumsCheckBox.isChecked()
        
        # ensure check boxes will work
        if not self.config['t'] and not self.config['u']:
            QtGui.QMessageBox.warning(self, "PhotoGrabber", "Invalid option combination, please choose to download tagged photos or uploaded albums.")
            return False

        # make sure a real item is selected
        self.config['targets'] = []
        if not self.ui.targetTreeWidget.isEnabled():
            self.config['targets'].append(self.advancedTarget)
            #get info on target?
            return True
            
        for i in self.ui.targetTreeWidget.selectedItems():
            if i.data(1,0) is not None: self.config['targets'].append(i.data(1,0)['id'])

        if len(self.config['targets']) > 0: return True
            
        QtGui.QMessageBox.warning(self, "PhotoGrabber", "Please select a valid target")
        return False

    def openFolder(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly)
        if dialog.exec_():
            self.config['dir'] = dialog.selectedFiles()[0]
            self.ui.pathLineEdit.setText(self.config['dir'])

    def beginDownload(self):
        # present progress modal
        total = len(self.config['targets'])
        self.progress = QtGui.QProgressDialog("Downloading...", "Abort", 0, total, parent=self)
        self.progress.setWindowModality(QtCore.Qt.WindowModal)
        self.progress.show()
        
        # processing heavy function
        try:
            self.helper.process(self.config, self.updateProgress)
        except Exception as e:
            QtGui.QMessageBox.critical(self, "Error", '%s - more info in pg.log' % e)
        
        self.progress.setValue(total)
        QtGui.QMessageBox.information(self, "Done", "Download is complete")
        self.progress.close()
        return True
        
    def updateProgress(self, text):
        QtGui.qApp.processEvents()
        if self.progress.wasCanceled():
            # hard quit
            sys.exit()
            
        if text:
            if text.endswith('downloaded!'):
                self.progress.setValue(self.progress.value() + 1)
            self.progress.setLabelText(text)

def start():
    app = QtGui.QApplication(sys.argv)
    mySW = ControlMainWindow()
    mySW.show()
    sys.exit(app.exec_())


