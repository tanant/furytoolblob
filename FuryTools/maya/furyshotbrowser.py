import sys
import os

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic
from PyQt4 import Qt
from PyQt4.QtCore import Qt as Qt

import subprocess

import FuryTools
reload(FuryTools)

from TT_utilities import maya_tools as FTmaya
reload(FTmaya)

# create us up a shot manager to manage raw data

class FuryShotBrowser(QtGui.QWidget):
    def __init__(self, shotManager):
        QtGui.QWidget.__init__(self)
        
        self.NEWFILE = '(NEW SCENE)'

        # bind to a copy of a shot manager and init variables
        self.shotManager = shotManager
        
        self.repopulateMaps()
      
    
        # load interface
        self.browser_widget = uic.loadUi(os.path.join(FuryTools.__pkgroot__, 'resources', 'TT_FuryShotBrowser.ui'))
        #self.browser_widget = uic.loadUi(r"\\vfx\fury\tools\maya\qt\TT_FuryShotBrowser.ui")

        
    
        # initial populate interface

        
        # set click/change handlers
        # note - itemChanged is when the DATA changes.
        #      - itemSelectionChanged just fires a binary signal
        #      - currentItemChanged will return in the args slot the current object and item
        self.browser_widget.seqWidget.currentItemChanged.connect(self.seq_updated)
        self.browser_widget.shotWidget.currentItemChanged.connect(self.shot_updated)
        self.browser_widget.userWidget.currentIndexChanged.connect(self.user_updated)
        
        self.browser_widget.fileWidget.doubleClicked.connect(self.doubleClick_file)
        self.browser_widget.otherFiles.doubleClicked.connect(self.doubleClick_otheruser)
        self.browser_widget.shotWidget.doubleClicked.connect(self.set_project)
        
        self.updateUserList()
        self.updateSequence()

        
        # set the refresh button up.
        self.browser_widget.refreshButton.clicked.connect(self.doubleClick_refresh)
        
        
        self.browser_widget.filepathWidget.setReadOnly(True)
        self.setWindowTitle("Fury Maya Shot Browser v1.02")
        
        self.setGeometry(self.geometry().left()+50, self.geometry().top()+50, self.browser_widget.geometry().width(), self.browser_widget.geometry().height())
        self.browser_widget.setGeometry(0,0,self.width(),self.height())
        
        
        # you need to set the context (i.e. right click) menu policy to fire the custom signal

        self.browser_widget.shotWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.browser_widget.shotWidget.customContextMenuRequested.connect(self.contextclick_pkg)       
        self.browser_widget.fileWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.browser_widget.fileWidget.customContextMenuRequested.connect(self.contextclick_pkg)       
        self.browser_widget.seqWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.browser_widget.seqWidget.customContextMenuRequested.connect(self.contextclick_pkg)       
        


        self.custom_context_menu = QtGui.QMenu(self)
        self.showBrowser = QtGui.QAction("Browse to file", self,
                                    triggered=self.contextclick_handler,
                                    )        
        self.showHeadshot= QtGui.QAction("open seq/shot in Headshot", self,
                                    triggered=self.contextclick_handler,
                                    )        
        self.browser_widget.setParent(self)

    def set_project(self, *args, **kwargs):
        try:
            seq= str(self.browser_widget.seqWidget.currentItem().text())
            shot= str(self.browser_widget.shotWidget.currentItem().text())
            user = str(self.browser_widget.userWidget.currentText())
            FTmaya.setProject(self.shotManager.mayaprojectpathFromSeqShot(shot, seq, 'maya', user))
        except:
            pass
           
    def contextclick_handler(self, *args, **kwargs):
        sender = self.sender()
        
        if sender == self.showBrowser:
            subproc = r'explorer "{0}"'
            try:
                shot = self.browser_widget.shotWidget.selectedItems()[0].text()
                seq = self.browser_widget.seqWidget.selectedItems()[0].text()
                usr= self.browser_widget.userWidget.currentText()

                # finalpath = 
                finalPath = os.path.join('{root}',
                                         '{seq}',
                                         '{seq}_{shot}',
                                         'work',
                                         'maya', 
                                         '{user}',
                                         'scenes',)
        
                subprocess.Popen(subproc.format(finalPath.format(root=self.shotPath,
                                                                 shot = shot,
                                                                 seq = seq,
                                                                 user = usr,).replace('/','\\')))
    
            except IndexError:
                # we don't have enough selected, die!
                pass
        elif sender == self.showHeadshot:
            subproc = r'explorer "{0}"'
            try:
                shot = self.browser_widget.shotWidget.selectedItems()[0].text()
                seq = self.browser_widget.seqWidget.selectedItems()[0].text()
                usr= self.browser_widget.userWidget.currentText()
                finalPath = os.path.join(r'http://headshot.kmm.int/shots/view',
                                         '{seq}_{shot}',)
        
                subprocess.Popen(subproc.format(finalPath.format(root=self.shotPath,
                                                                 shot = shot,
                                                                 seq = seq,
                                                                 user = usr,).replace('/','\\')))
    
            except IndexError:
                # we don't have enough selected, die!
                pass


        
        pass

    def contextclick_pkg(self, *args, **kwargs):
        self.custom_context_menu.popup(QtGui.QCursor.pos())
        
    def updateUserList(self, *args, **kwargs):
        # user widget taken from userList
        self.browser_widget.userWidget.clear()
        self.browser_widget.userWidget.addItems(sorted([value for key,value in self.machineUserMap.items()]))

        self.browser_widget.userWidget.setCurrentIndex( self.browser_widget.userWidget.findText(self.shotManager.mapMachineToUser()))
        # major version widget just a flat number, but won't actually change so it can be static
        # self.browser_widget.majorWidget.addItems(self.shotManager.versionList())

    def updateSequence(self, *args, **kwargs):
        # populate the sequence
        self.browser_widget.seqWidget.clear()
        self.browser_widget.seqWidget.addItems(sorted([key for key,value in self.seqShotDict.items()]))
        # fire a sequence start/selection
        self.browser_widget.seqWidget.setCurrentRow(0)
        
    def doubleClick_refresh(self, *args, **kwargs):
        self.repopulateMaps()
        self.updateUserList()
        self.updateSequence()

    def doubleClick_otheruser(self, *args, **kwargs):
        seq= str(self.browser_widget.seqWidget.currentItem().text())
        shot= str(self.browser_widget.shotWidget.currentItem().text())
        filename = str(self.browser_widget.otherFiles.currentItem().text().split(':')[1])
        user = str(self.browser_widget.otherFiles.currentItem().text().split(':')[0])
        self.open_file(seq,shot,filename, user)

        
    def repopulateMaps(self):
        self.machineUserMap = self.shotManager.populateMachineUserMap()
        self.seqShotDict = self.shotManager.populateShotDict()

        
    def foo(self, *args, **kwargs):
        print "\n-------foo"
        print self
        print args
        print kwargs
        pass

    def open_file(self, seq, shot, filename, user):
        if filename == self.NEWFILE:
            result = FTmaya.newFile()
        else:
            result = FTmaya.loadFile(os.path.join(self.shotManager.softwarepathFromSeqShot(shot, seq, 'maya', user),filename))
        
        if result :
            FTmaya.setProject(self.shotManager.mayaprojectpathFromSeqShot(shot, seq, 'maya', user))

        
    def doubleClick_file(self, *args, **kwargs):
        
        # firing off a doubleclick should pass to a handler that will just do what needs 
        # to be done for setting projects and stuff
        seq= str(self.browser_widget.seqWidget.currentItem().text())
        shot= str(self.browser_widget.shotWidget.currentItem().text())
        filename= str(self.browser_widget.fileWidget.currentItem().text())
        user = str(self.browser_widget.userWidget.currentText())
        self.open_file(seq,shot,filename, user)
        
        self.close()

    def user_updated(self, *args, **kwargs):
        if args[0] is None:
            # do nothing since there is nothing selected
            # this is a rare case for a QComboBox. Might actually not be possible?
            pass
        else:
            # print self.browser_widget.userWidget.itemText(args[0])
            self.shotcode_changed()

    def seq_updated(self, *args, **kwargs):
        try:
            self.populate_shots_from_seq(args[0].text())
        except AttributeError:
            pass
        
    def shot_updated(self, *args, **kwargs):
        if args[0] is None:
            # print ("nargs")
            # do nothing since there is nothing selected
            pass
        else:
            self.shotcode_changed()
            pass
        
    def shotcode_changed(self):
        try:
            shot = str(self.browser_widget.seqWidget.currentItem().text())
            seq = str(self.browser_widget.shotWidget.currentItem().text())
            usr = str(self.browser_widget.userWidget.currentText())
            # print ("shotcode: {shot}:{seq}:{usr}".format(shot=shot,seq=seq,usr=usr))
            
            shotfiles = self.shotManager.getShotFilesForAll(shot=shot,seq=seq,software='maya',stripEmpties=True)
            
            self.browser_widget.fileWidget.clear()
            self.browser_widget.fileWidget.addItem(self.NEWFILE)
            try:
                self.browser_widget.fileWidget.addItems(shotfiles[usr])
            except KeyError:
                pass

            self.browser_widget.otherFiles.clear()
            self.browser_widget.otherFiles.addItems(self.shotManager.getShotVersionsForAll(shot=shot,seq=seq,software='maya'))
            
                
            self.browser_widget.filepathWidget.setText(self.shotManager.softwarepathFromSeqShot(seq,shot, 'maya', usr))
        except AttributeError:
            pass

    def populate_shots_from_seq(self, seq_code):
        try:
            #QT uses unicode, and we're using unicode as labels. This isn't ideal, but should work
            seq_code = str(seq_code)
            self.browser_widget.shotWidget.clear()
            self.browser_widget.shotWidget.addItems(self.seqShotDict[seq_code])
            self.browser_widget.shotWidget.setCurrentRow(0)
        except AttributeError:
            pass

