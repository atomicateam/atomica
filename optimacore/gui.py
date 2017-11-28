# -*- coding: utf-8 -*-
"""
Optima Core graphical user interface (GUI) file.
Contains back-end GUI wrappers for codebase functionality.
Note: Callback functions cannot be easily decorated, so logging is applied per method, not per class.
"""

from optimacore.system import logUsage, accepts, returns, logger
from optimacore.framework_io import createFrameworkTemplate

import sys

def importPyQt():
    """ Try to import pyqt, either PyQt4 or PyQt5, but allow it to fail. """
    try:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        from PyQt5 import QtCore as qtc
        from PyQt5 import QtWidgets as qtw
    except:
        try:
            from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
            from PyQt4 import QtCore as qtc
            from PyQt4 import QtGui as qtw
        except Exception as E:
            errormsg = "PyQt could not be imported: %s" % E.__repr__()
            raise Exception(errormsg)
    return  qtc, qtw, FigureCanvasQTAgg
qtc, qtw, FigureCanvasQTAgg = importPyQt()

@logUsage
def getPathFromUser(instance = None, load_not_save = True, title = None, file_filter = None):
    """
    Get a path from a file dialog, either related to opening or saving a file.
    """
    try:
        if load_not_save:
            try:    path = str(qtw.QFileDialog.getOpenFileNameAndFilter(instance, title, filter = file_filter)[0])
            except: path = str(qtw.QFileDialog.getOpenFileName(instance, title, filter = file_filter)[0])
        else:
            try:    path = str(qtw.QFileDialog.getSaveFileNameAndFilter(instance, title, filter = file_filter)[0])
            except: path = str(qtw.QFileDialog.getSaveFileName(instance, title, filter = file_filter)[0])
    except:
        raise
    return path

@logUsage
def getLoadPathFromUser(instance = None, title = None, file_filter = None):
    """ Convenience function that asks the user for a file-saving path. """
    try: path = getPathFromUser(instance = instance, load_not_save = True, title = title, file_filter = file_filter)
    except:
        logger.exception("An attempt to ask the user for a save-file path has failed.")
        raise
    return path

@logUsage
def getSavePathFromUser(instance = None, title = None, file_filter = None):
    """ Convenience function that asks the user for a file-loading path. """
    try: path = getPathFromUser(instance = instance, load_not_save = False, title = title, file_filter = file_filter)
    except:
        logger.exception("An attempt to ask the user for a load-file path has failed.")
        raise
    return path

class GUISettings(object):
    """ Stores settings relevant to GUI construction. """
    
    SCREEN_WIDTH = 0
    SCREEN_HEIGHT = 0
    DEFAULT_SCREEN_FRACTION_WIDTH = 0.9
    DEFAULT_SCREEN_FRACTION_HEIGHT = 0.9
    
    @classmethod
    @logUsage
    def updateUsingApp(cls, app):
        """ Some GUI settings cannot be determined without a PyQt application being generated first. """
        screen = app.desktop().availableGeometry()
        cls.SCREEN_WIDTH = screen.width()
        cls.SCREEN_HEIGHT = screen.height()

@logUsage
@accepts(qtw.QWidget,float,float)
def resizeInScreen(widget, fraction_width, fraction_height):
    widget.resize(fraction_width*GUISettings.SCREEN_WIDTH, fraction_height*GUISettings.SCREEN_HEIGHT)

@logUsage
@accepts(qtw.QWidget)
def centerInScreen(widget):
    widget.setGeometry((GUISettings.SCREEN_WIDTH - widget.width())/2,
                       (GUISettings.SCREEN_HEIGHT - widget.height())/2,
                       widget.width(), widget.height())

class GUIDemo(qtw.QWidget):
    """ A demo window that displays a series of buttons for launching other Optima Core widgets. """

    @logUsage
    def __init__(self):
        """ Initializes the demo GUI. """
        super(GUIDemo, self).__init__()
        self.initUIDemo()

    @logUsage
    def initUIDemo(self):
        """ Initializes all UI elements for the demo GUI. """

        self.setWindowTitle("GUI Demo")

        self.button_framework_template = qtw.QPushButton("Create Framework Template", self)
        self.button_framework_template.clicked.connect(self.slotRunGUIFrameworkTemplate)

        layout = qtw.QVBoxLayout(self)
        layout.addWidget(self.button_framework_template)
        self.setLayout(layout)

        centerInScreen(self)

        self.show()
        
    def slotRunGUIFrameworkTemplate(self):
        """ Launches the sub-GUI for constructing a framework template. """
        self.subgui = GUIFrameworkTemplate()
        
class GUIFrameworkTemplate(qtw.QWidget):
    """ A widget for constructing an Excel-based template framework file. """

    @logUsage
    def __init__(self):
        """ Initializes the framework template GUI. """
        super(GUIFrameworkTemplate, self).__init__()
        self.initUIFrameworkTemplate()

    @logUsage
    def initUIFrameworkTemplate(self):
        """ Initializes all UI elements for the framework template GUI. """

        self.setWindowTitle("Framework Template Construction")

        self.button_create = qtw.QPushButton("Create Framework Template", self)
        self.button_create.clicked.connect(self.slotCreateFrameworkTemplate)

        layout = qtw.QVBoxLayout(self)
        layout.addWidget(self.button_create)
        self.setLayout(layout)

        resizeInScreen(self, fraction_width = GUISettings.DEFAULT_SCREEN_FRACTION_WIDTH, 
                             fraction_height = GUISettings.DEFAULT_SCREEN_FRACTION_HEIGHT)
        centerInScreen(self)

        self.show()
        
    def slotCreateFrameworkTemplate(self):
        """ Creates a template framework file at the location specified by the user. """
        framework_path = getSavePathFromUser(file_filter = "*.xlsx")
        try: createFrameworkTemplate(framework_path = framework_path)
        except:
            logger.exception("Framework template construction has failed.")
            raise

@logUsage
@returns(qtw.QWidget)
def runGUI():
    """ Function that launches all available back-end GUIs as they are developed. """
    gui = None
    app = qtw.QApplication(sys.argv)
    app.setApplicationName("Optima Core GUI")
    GUISettings.updateUsingApp(app)
    gui = GUIDemo()
    sys.exit(app.exec_())
    return gui      # Avoids pylint warning.