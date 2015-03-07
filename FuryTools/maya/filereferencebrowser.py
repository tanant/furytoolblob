import os
import sys
import re
import shutil

import PyQt4
import PyQt4.QtGui as QtGui
from PyQt4 import uic as uic
from PyQt4.QtCore import Qt as Qt
import pymel.core as pm

import TT_utilities.maya_tools as tt_mt

class FileReferenceBrowser(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        # column 0 is always the file type
        # column 1 is the filepath
        # column 2 is use frame/frame extension option
        
        super(FileReferenceBrowser,self).__init__(*args, **kwargs)
        
        self.default_column_widths = [300,550,50]
        self.uifile =  r'H:\user\anthony.tan\DEVELOPMENT\FuryTools\resources\ref_ed.ui'
        self.categories = { 'filetex': 'File textures',
                            'references': 'file references',
                            'implane': 'image planes',
                            'caches': 'Dynamics caches',
                            'other': 'Other stuff',
                            }
        
        self.holding_pen = r'O:\DeliveryHolding\deliveriesOut\delivery_prep\{seq}_{shot}'
        
        self.category_dict = {}
        for key, value in self.categories.items():
            self.category_dict[key] = QtGui.QTreeWidgetItem()
            self.category_dict[key].setText(0,value)
        self.build_UI()
       
       
        # click and action handlers
        self.UI.nodeTree.doubleClicked.connect(self.row_doubleclick)
        self.UI.nodeTree.itemSelectionChanged.connect(self.foo2)
        self.UI.refreshButton.clicked.connect(self.populate_all)
        self.UI.togglerenderthumbButton.clicked.connect(tt_mt.toggle_renderthumbs)
        
        self.UI.localiseButton.clicked.connect(self.localiseButton_clicked)
        self.UI.repathPenButton.clicked.connect(self.repathPenButton_clicked)
        # right click is the RE thing
        # mopts = find/replace (no re)
        self.references_dict = {}
    
   
    def repathPenButton_clicked(self):
        
        root_replacement_pairs = [ (r'(?i)H:/shots/{seq}/{seq}_{shot}',r'N:/DeliveryHolding/deliveriesOut/delivery_prep/{seq}_{shot}'),
                                   (r'(?i)//vfx/fury/shots/{seq}/{seq}_{shot}',r'N:/DeliveryHolding/deliveriesOut/delivery_prep/{seq}_{shot}'), 
                                   ]         
        shot= str(self.UI.shotWidget.text())
        seq= str(self.UI.seqWidget.text())
        
        current_item = self.UI.nodeTree.currentItem()
        source_file = str(self.UI.nodeTree.itemWidget(current_item, 1).text())
        
        node_attrib_name = source_file.split(':')[0]    # first thing before the colon
        
        for pair in root_replacement_pairs:
            print pair
            print seq
            print shot
            print source_file
            print re.search(pair[0].format(shot=shot, seq=seq), source_file)
            if re.search(pair[0].format(shot=shot, seq=seq), source_file):
                # do the pm replacement
                # new string
                new_text = ':'.join(re.sub(pair[0].format(shot=shot, seq=seq), pair[1].format(shot=shot, seq=seq), source_file).split(':')[1:])
                print new_text
                pm.PyNode(str(current_item.text(0))).attr(node_attrib_name).set(new_text)
                
        
     
        
    def localiseButton_clicked(self):
        shot= str(self.UI.shotWidget.text())
        seq= str(self.UI.seqWidget.text())
        

    
        for x in self.UI.nodeTree.selectedItems(): 
            #current_item = self.UI.nodeTree.currentItem()
            #source_file = str(self.UI.nodeTree.itemWidget(current_item, 1).text())
            current_item = x
            source_file = str(self.UI.nodeTree.itemWidget(x, 1).text())
            
            # get the selected item, print text in col 0
            
            
            # what's the rule?
            # assuming it's not a sequence for now..
            # shutil.copy the source file to the holding pen
            # dest dir  = 
            # \components\textures\{filename_stripped}\
             
            file_name = os.path.basename(source_file)   # assuming we don't have too many colons..
            target_dir = os.path.join(self.holding_pen.format(shot=shot, seq=seq), "components", "textures", '.'.join(os.path.basename(source_file).split('.')[0:-1]))
            file_sourcedir = os.path.dirname(':'.join(source_file.split(':')[1:]))
            node_attrib_name = source_file.split(':')[0]    # first thing before the colon
            
            print target_dir
            print file_name
            print file_sourcedir
            print node_attrib_name
            
            if str(self.UI.nodeTree.itemWidget(current_item, 2)) == 'sequence':
                print "sequence detected, copying anything that looks roughly right"
            else:
                try: 
                    os.makedirs(target_dir)
                except:
                    pass
            
                # check col 2
                try:
                    shutil.copy(os.path.join(file_sourcedir, file_name), target_dir)
                except:
                    pass
                
            pm.PyNode(str(current_item.text(0))).attr(node_attrib_name).set(os.path.join(target_dir,file_name))
        
        

        
    def row_doubleclick(self, *args, **kwargs):
        clicked_item = self.sender().selectedItems()[0]
        if not self.is_category_master(clicked_item):
            pm.select(str(clicked_item.text(0)))
        pass
        
    def foo2(self, *args, **kwargs):
        #print self.sender()
        #print self.sender().selectedItems()
        
        for x in self.sender().selectedItems():
            for child_index in xrange(0, x.childCount()):
                # print x.child(child_index).text(0)
                pass
                # it's a top level, therefore we must select children category or do something
        pass
    
    
    def is_category_master(self, widget):
        if widget in self.category_dict.values():
            return True
        else: 
            return False
    
    def get_children(self, cat_header_widget_item):
        
        children = []
        for child_index in xrange(0,cat_header_widget_item.childCount()):
            children.append(cat_header_widget_item.child(child_index))
        return children

        
        
    def foo(self, *args, **kwargs):
        print self
        print self.sender()
        
    def bar(self):
        print 'bar ' + str(self)
        
    def build_UI(self):
        self.UI = uic.loadUi(self.uifile)
        self.UI.nodeTree.clear()
        for key, value in self.category_dict.items():
            self.UI.nodeTree.addTopLevelItem(value)

    def resize_cols_default(self):
        for x,width in enumerate(self.default_column_widths):
            self.UI.nodeTree.setColumnWidth(x, width)        

    def clear_all(self):
        
        pass

    def clear_category(self, category_key):
        
        category_head = self.category_dict[category_key]
        category_head.clear()
        
        pass
    
    def populate_all(self):
        self.clear()
        self.populate_references()
        self.populate_implanes()
        self.populate_filetex()
        self.populate_cachefile()
        
        # now try guess the shot/sequence from the filename.
        # the regexp tries to match as late in the string as possible
        #x = re.search(r'.*([a-zA-Z0-9]{3}_[0-9]{3})',pm.sceneName())
        
        # updated regexp to match EARLY in the seqshot, so we don't get faked by people with scene from elsewhere.
        # basically, trust the root.
        x = re.search(r'([a-zA-Z0-9]{3}_[0-9]{3}).*',pm.sceneName())
        print pm.sceneName()
        try:
            self.UI.seqWidget.setText(x.group(1).split('_')[0])
            self.UI.shotWidget.setText(x.group(1).split('_')[1])
        except:
            raise
        
        
    def show(self):
        self.resize_cols_default()
        self.UI.show()

    def clear(self):
        for x in self.category_dict.values():
            for child_index in xrange(0,x.childCount()):
                x.removeChild(x.child(0))
            

    def populate_cachefile(self):
        self.cachefile_dict = {}
        
        category_head = self.category_dict['caches']
        cachefile = pm.ls(type = pm.nt.CacheFile)
        for x in cachefile:
            new_widget = QtGui.QTreeWidgetItem(category_head)   # create a new widget under the cat head, parenting (puts in the right area)
            new_widget.setText(0,x.name())                      # give it a name in column zero - this is text
            try:
                new_line_edit = QtGui.QLabel('cachePath:' + x.attr('cachePath').get())  # create a line_edit item, which holds text
            except:
                new_line_edit = QtGui.QLabel('cachePath:UNKNOWN')  # create a line_edit item, which holds text
            self.UI.nodeTree.setItemWidget(new_widget,1,new_line_edit)  # and the bind the line edit into the table for col 1, and whereever new_widget is

            
        cachefile = pm.ls(type = pm.nt.DynGlobals)
        for x in cachefile:
            new_widget = QtGui.QTreeWidgetItem(category_head)   # create a new widget under the cat head, parenting (puts in the right area)
            new_widget.setText(0,x.name())                      # give it a name in column zero - this is text
            try:
                new_line_edit = QtGui.QLabel('cacheDirectory:' + x.attr('cacheDirectory').get())  # create a line_edit item, which holds text
            except:
                new_line_edit = QtGui.QLabel('cacheDirectory:UNKNOWN')  # create a line_edit item, which holds text
            self.UI.nodeTree.setItemWidget(new_widget,1,new_line_edit)  # and the bind the line edit into the table for col 1, and whereever new_widget is


        
    def populate_filetex(self):
        self.filetex_dict = {}
        
        category_head = self.category_dict['filetex']
        
        filetex = pm.ls(type = pm.nt.File)
        for x in filetex:
            new_widget = QtGui.QTreeWidgetItem(category_head)   # create a new widget under the cat head, parenting (puts in the right area)
            new_widget.setText(0,x.name())                      # give it a name in column zero - this is text
            
            new_line_edit = QtGui.QLabel('fileTextureName:' + x.attr('fileTextureName').get())  # create a line_edit item, which holds text

            self.UI.nodeTree.setItemWidget(new_widget,1,new_line_edit)  # and the bind the line edit into the table for col 1, and whereever new_widget is
            if x.attr('useFrameExtension').get():
                new_widget.setText(2,'sequence')

                
    def populate_implanes(self):
        self.implanes_dict = {}
        
        category_head = self.category_dict['implane']
        filetex = pm.ls(type = pm.nt.ImagePlane)
        for x in filetex:
            new_widget = QtGui.QTreeWidgetItem(category_head)   # create a new widget under the cat head, parenting (puts in the right area)
            new_widget.setText(0,x.name())                      # give it a name in column zero - this is text
            
            new_line_edit = QtGui.QLabel('imageName:' + x.attr('imageName').get())  # create a line_edit item, which holds text

            self.UI.nodeTree.setItemWidget(new_widget,1,new_line_edit)  # and the bind the line edit into the table for col 1, and whereever new_widget is
            if x.attr('useFrameExtension').get():
                new_widget.setText(2,'sequence')

         
    def populate_references(self):
        self.references_dict = {}
                
        category_head = self.category_dict['references']
        
        references = pm.listReferences()
        for x in references:
            new_widget = QtGui.QTreeWidgetItem(category_head)
            new_widget.setText(0,x.refNode.name())
            new_widget.setText(1,x.path)          
        


