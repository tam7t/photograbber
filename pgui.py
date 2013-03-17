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

class LoginSignal(QtCore.QObject):
    sig = QtCore.Signal(int)
    err = QtCore.Signal(str)
    msg = QtCore.Signal(str)

class LoginThread(QtCore.QThread):  
    def __init__(self, helper, data, parent=None):
        QtCore.QThread.__init__(self, parent)
        
        self.mutex = QtCore.QMutex()
        self.abort = False #accessed by both threads
        self.data_ready = False
        
        self.helper = helper
        self.data = data
        self.status = LoginSignal()
    
    def run(self):
        try:
            self.mutex.lock()
            if self.abort:
                self.mutex.unlock()
                return
            self.mutex.unlock()
            
            self.data['my_info'] = self.helper.get_me()
            
            self.mutex.lock()
            if self.abort:
                self.mutex.unlock()
                return
            self.status.sig.emit(1)
            self.mutex.unlock()
            
            self.data['friends'] = self.helper.get_friends('me')
            
            self.mutex.lock()
            if self.abort:
                self.mutex.unlock()
                return
            self.status.sig.emit(2)
            self.mutex.unlock()
            
            self.data['likes'] = self.helper.get_likes('me')
            
            self.mutex.lock()
            if self.abort:
                self.mutex.unlock()
                return
            self.status.sig.emit(3)
            self.mutex.unlock()
            
            self.data['subscriptions'] = self.helper.get_subscriptions('me')
            self.status.sig.emit(4)
            
            self.data_ready = True
        except Exception as e:
            print "error: %s" % e
            self.status.err.emit('%s' % e)
            
    def stop(self):
        self.mutex.lock()
        self.abort = True
        self.mutex.unlock()

class DownloadThread(QtCore.QThread):  
    def __init__(self, helper, config, parent=None):
        QtCore.QThread.__init__(self, parent)

        self.helper = helper
        self.config = config
        self.status = LoginSignal()

    def run(self):
        try:
            self.helper.process(self.config, self.status.msg.emit)
        except Exception as e:
            print "error: %s" % e
            self.status.err.emit('%s' % e)
        
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
        
    def errorMessage(self, error):
        QtGui.QMessageBox.critical(self, "Error", '%s - more info in pg.log' % error)
    
    def validateLogin(self):
        # present progress modal
        progress = QtGui.QProgressDialog("Logging in...", "Abort", 0, 4, parent=self)
        #QtGui.qApp.processEvents() is unnecessary when dialog is Modal
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.show()

        # attempt to login
        self.token = self.ui.enterTokenLineEdit.text()
        try:
            if not self.token.isalnum(): raise Exception("Please insert a valid token")
            self.helper = helpers.Helper(facebook.GraphAPI(self.token))
        except Exception as e:
            progress.close()
            self.errorMessage(e)
            return False

        data =  {}
        thread = LoginThread(self.helper, data)
        thread.status.sig.connect(progress.setValue)
        thread.status.err.connect(self.errorMessage)
        thread.status.err.connect(progress.cancel)
        thread.start()
        
        while thread.isRunning():
            QtGui.qApp.processEvents()
            if progress.wasCanceled():
                thread.stop()
                thread.wait()
                return False
        
        if progress.wasCanceled() or not thread.data_ready: return False
        
        # clear list
        self.ui.targetTreeWidget.topLevelItem(0).takeChildren()
        self.ui.targetTreeWidget.topLevelItem(1).takeChildren()
        self.ui.targetTreeWidget.topLevelItem(2).takeChildren()
        
        # populate list
        item = QtGui.QTreeWidgetItem()
        item.setText(0, data['my_info']['name'])
        item.setData(1, 0, data['my_info'])
        self.ui.targetTreeWidget.topLevelItem(0).addChild(item)
        
        for p in data['friends']:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, p['name'])
            item.setData(1, 0, p)
            self.ui.targetTreeWidget.topLevelItem(0).addChild(item)

        for p in data['likes']:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, p['name'])
            item.setData(1, 0, p)
            self.ui.targetTreeWidget.topLevelItem(1).addChild(item)

        for p in data['subscriptions']:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, p['name'])
            item.setData(1, 0, p)
            self.ui.targetTreeWidget.topLevelItem(2).addChild(item)

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
        thread = DownloadThread(self.helper, self.config)
        thread.status.msg.connect(self.updateProgress)
        thread.status.err.connect(self.errorMessage)
        thread.status.err.connect(self.progress.cancel)
        thread.start()
        
        while thread.isRunning():
            QtGui.qApp.processEvents()
            if self.progress.wasCanceled():
                thread.stop()
                sys.exit()
        
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


