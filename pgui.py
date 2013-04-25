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
from operator import itemgetter

import facebook
import helpers

import logging

log = logging.getLogger('pg.%s' % __name__)

class ControlMainWindow(QtGui.QWizard):
    def __init__(self, parent=None):
        super(ControlMainWindow, self).__init__(parent)
        self.ui =  Ui_Wizard()
        self.ui.setupUi(self)

        # data
        self.graph = facebook.GraphAPI('')
        self.graph.start()
        self.peoplegrab = None
        self.albumgrab = None
        self.pool = helpers.DownloadPool()
        for i in range(15): self.pool.add_thread()
        self.token = ''
        self.config = {}
        self.adv_target = ""

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
        QtGui.QMessageBox.about(self, "About", "PhotoGrabber v2.100\n(C) 2013 Ourbunny\nGPLv3\n\nphotograbber.org\nView the LICENSE.txt file for full licensing information.")

    def loginPressed(self):
        facebook.request_token()

    def advancedPressed(self):
        self.adv_target, ok = QtGui.QInputDialog.getText(self, "Specify Target", "ID/username of target", text=self.adv_target)
        if ok:
            self.ui.targetTreeWidget.setEnabled(False)
        else:
            self.ui.targetTreeWidget.setEnabled(True)
        
    def errorMessage(self, error):
        log.exception(error)
        QtGui.QMessageBox.critical(self, "Error", '%s' % error)
    
    def validateLogin(self):
        # present progress modal
        progress = QtGui.QProgressDialog("Logging in...", "Abort", 0, 0, parent=self)
        #QtGui.qApp.processEvents() is unnecessary when dialog is Modal
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.show()

        self.token = self.ui.enterTokenLineEdit.text()
        
        # allow user to specify debug mode
        if self.token.endswith(":debug"):
            logging.getLogger("pg").setLevel(logging.DEBUG)
            log.info('DEBUG mode enabled.')
            self.token = self.token.split(":debug")[0]
        if self.token.endswith(":info"):
            logging.getLogger("pg").setLevel(logging.INFO)
            log.info('INFO mode enabled.')
            self.token = self.token.split(":info")[0]

        try:
            if not self.token.isalnum(): raise Exception("Please insert a valid token.")
            self.graph.set_token(self.token)
            
            # ensure token is removed from logs...
            log.info('Provided token: %s' % self.token)
            
            self.peoplegrab = helpers.PeopleGrabber(self.graph)
            self.albumgrab = helpers.AlbumGrabber(self.graph)
        except Exception as e:
            progress.close()
            self.errorMessage(e)
            return False

        data =  {}
        
        requests = []
        requests.append({'path':'me'})
        requests.append({'path':'me/friends'})
        requests.append({'path':'me/likes'})
        requests.append({'path':'me/subscribedto'})
        
        rids = self.graph.make_requests(requests)
        while self.graph.requests_active(rids):
            QtGui.qApp.processEvents()
            if progress.wasCanceled():
                progress.close()
                return False
        
        try:
            data['my_info'] = self.graph.get_data(rids[0])
            data['friends'] = sorted(self.graph.get_data(rids[1]), key=itemgetter('name'))
            data['likes'] = sorted(self.graph.get_data(rids[2]), key=itemgetter('name'))
            data['subscriptions'] = sorted(self.graph.get_data(rids[3]), key=itemgetter('name'))
        except Exception as e:
            progress.close()
            self.errorMessage(e)
            return False
        
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
            self.config['targets'].append(self.adv_target)
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
        progress = QtGui.QProgressDialog("Downloading...", "Abort", 0, 0, parent=self)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.show()
        
        # processing heavy function
        thread = helpers.ProcessThread(self.albumgrab, self.config, self.pool)
        thread.start()
        
        while thread.isAlive():
            QtGui.qApp.processEvents()
            #progress.setLabelText(thread.status())
            if progress.wasCanceled():
                sys.exit()
        
        #progress.setValue(total)
        #progress.setLabelText(thread.status())
        #QtGui.QMessageBox.information(self, "Done", "Download is complete.")
        QtGui.QMessageBox.information(self, "Done", thread.status())
        progress.close()
        return True

def start():
    app = QtGui.QApplication(sys.argv)
    mySW = ControlMainWindow()
    mySW.show()
    sys.exit(app.exec_())
