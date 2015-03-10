import nuke

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui

from nukescripts import panels

# just a quick subclass of the QLineEdit so that
# if you were to click in, it'll empty out the text.
class FocusClearLineEdit(QtGui.QLineEdit):

    def __init__(self, *args, **kwargs):
        super(FocusClearLineEdit, self).__init__(*args, **kwargs)
        self.inDefault = True
        self.default = args[0]

    def focusInEvent(self, event):
        if self.inDefault:
            self.setText(None)
            self.inDefault = False

    def reset_to_default(self):
        self.inDefault = True
        self.setText(self.default)


class SlateLookupWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(SlateLookupWindow, self).__init__(parent)

        # model section
        self._init_data()
        self._build_UI()

    def _init_data(self):
        self.results = {}
        self.database = 'test string'

    def foo(self, *args):
        print args
        print self
        print self.sender
        nuke.createNode('Read')

    def _build_UI(self):

        # this block defines the search area
        self.searchblockLayout = QtGui.QHBoxLayout()
        self.searchLabel = QtGui.QLabel('Slate Name:')
        self.searchBox = FocusClearLineEdit('e.g. : X-231-N0021, or X_1_sxs_312')
        self.searchGo = QtGui.QPushButton('search!')

        self.searchblockLayout.addWidget(self.searchLabel)
        self.searchblockLayout.addWidget(self.searchBox)
        self.searchblockLayout.addWidget(self.searchGo)

        # just a simple text reminder string so we can se who is using it
        self.dbinuse = QtGui.QLabel('using: {db})'.format(db=self.database))
        self.dbinuse.setDisabled(True)  # just for that lovely light grey :P

        # this is the result area - we're using a simple QListWidget.
        # items in the QLW follow the usual pattern - we have a
        self.results_label = QtGui.QLabel('Results')
        self.results_label.setDisabled(True)
        self.results_list = QtGui.QListWidget()

        # assemble main layout from pieces
        self.setLayout(QtGui.QVBoxLayout())  # master layout is vertical stacking
        self.layout().addLayout(self.searchblockLayout, alignment=QtCore.Qt.AlignTop)

        self.layout().addWidget(self.results_label, alignment=QtCore.Qt.AlignTop)
        self.layout().addWidget(self.results_list, alignment=QtCore.Qt.AlignTop)
        self.layout().addWidget(self.dbinuse, alignment=QtCore.Qt.AlignTop)

        # now assemble the event handlers
        self.searchGo.clicked.connect(self.do_search)
        self.searchBox.returnPressed.connect(self.searchGo.click)
        self.results_list.doubleClicked.connect(self.foo)

    def do_search(self):
        # sanitise the search text
        self.searchBox.setText(self.searchBox.text().lstrip().rstrip())

        # probably should do more sanitisation like drop table etc
        # remove anything that's not a letter, number, dash, or underscore

        # set up the results area
        self.results = {}

        x = QtGui.QListWidgetItem()
        x.setText('001_ALEXA_X231_123_A')
        self.results_list.addItem(x)


panels.registerWidgetAsPanel('SlateLookupWindow', 'Slate Lookup', 'com.flamingwidget.furyfx.slatelookupwindow')


#x = SlateLookupWindow()
# x.show()
