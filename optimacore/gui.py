# -*- coding: utf-8 -*-
"""
Optima Core graphical user interface (GUI) file.
Contains back-end GUI wrappers for codebase functionality.
Note: Callback functions cannot be easily decorated, so logging is applied per method, not per class.
"""

from optimacore.system import logUsage, accepts, returns, logger, SystemSettings
from optimacore.framework_settings import FrameworkSettings
from optimacore.framework_io import FrameworkTemplateInstructions, createFrameworkTemplate

import sys

def importPyQt():
    """ Try to import PyQt, either PyQt4 or PyQt5, but allow it to fail. """
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
            error_message = "PyQt could not be imported: %s" % E.__repr__()
            raise Exception(error_message)
    return  qtc, qtw, FigureCanvasQTAgg
qtc, qtw, FigureCanvasQTAgg = importPyQt()

#%% Code for GUI settings variables.

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

#%% Code for GUI convenience functions.

@logUsage
def getPathFromUser(instance = None, load_not_save = True, title = None, file_filter = None):
    """
    Get a path from a file dialog, either related to opening or saving a file.
    The file filter allows control over the file type being saved or loaded, e.g.: "*.xlsx"
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

#%% Code for GUIs.

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
        self.button_framework_template.clicked.connect(self.slotRunGUIFrameworkFileCreation)

        layout = qtw.QVBoxLayout(self)
        layout.addWidget(self.button_framework_template)
        self.setLayout(layout)

        centerInScreen(self)

        self.show()
        
    def slotRunGUIFrameworkFileCreation(self):
        """ Launches the sub-GUI for constructing a framework template. """
        self.subgui = GUIFrameworkFileCreation()
        
class GUIFrameworkFileCreation(qtw.QWidget):
    """ A widget for constructing an Excel-based template framework file. """

    @logUsage
    def __init__(self):
        """ Initializes the framework template GUI. """
        super(GUIFrameworkFileCreation, self).__init__()
        self.initUIFrameworkFileCreation()

    @logUsage
    def initUIFrameworkFileCreation(self):
        """ Initializes all UI elements for the framework template GUI. """
        self.setWindowTitle("Framework Template Construction")
        self.resetAttributes()
        self.developLayout()
        self.show()
        
    @logUsage
    def resetAttributes(self):   
        """ Resets all attributes related to this GUI; must be called once at initialization. """
        # This widget is attached to an instructions object that the user can modify prior to producing a template framework.
        self.framework_instructions = FrameworkTemplateInstructions()

    @logUsage
    def developLayout(self):
        """ Lays out components of the framework template GUI. """
        # Produce a layout and memory space to store GUI components related to modifying instructions.
        layout_framework_instructions = qtw.QGridLayout()
        self.list_label_item_descriptors = []
        self.list_spinbox_item_numbers = []
        # Cycle through all page-item types referenced in the instructions object.
        # Develop appropriate text for label widgets that describe each page-item type..
        item_type_number = 0
        for item_type in self.framework_instructions.num_items:
            descriptor = FrameworkSettings.ITEM_TYPE_SPECS[item_type]["descriptor"]
            text_extra = "' items: "
            if not FrameworkSettings.ITEM_TYPE_SPECS[item_type]["superitem_type"] is None:
                superitem_type = FrameworkSettings.ITEM_TYPE_SPECS[item_type]["superitem_type"]
                descriptor_extra = FrameworkSettings.ITEM_TYPE_SPECS[superitem_type]["descriptor"]
                text_extra = "' subitems per '" + descriptor_extra + "' item: "
            text = "Number of '" + descriptor + text_extra
            self.list_label_item_descriptors.append(qtw.QLabel(text))
            # Generate integer-input spinboxes and give them default values associated with the instructions object.
            self.list_spinbox_item_numbers.append(qtw.QSpinBox())
            self.list_spinbox_item_numbers[-1].setValue(self.framework_instructions.num_items[item_type])
            # Ensure that user value changes are immediately propagated to the callback that updates the instructions object.
            # Note: The lambda must include item_type definition to avoid closure issues, i.e. all spinboxes referencing the last page-item.
            self.list_spinbox_item_numbers[-1].valueChanged.connect(lambda number, item_type=item_type: 
                                                                    self.slotUpdateFrameworkInstructions(item_type=item_type, number=number))
            # Arrange the label and spinbox components into the appropriate grid layout.
            layout_framework_instructions.addWidget(self.list_label_item_descriptors[item_type_number],
                                                    item_type_number, 0)
            layout_framework_instructions.addWidget(self.list_spinbox_item_numbers[item_type_number],
                                                    item_type_number, 1)
            item_type_number += 1

        # Create a template framework creation button and link it to the correct callback.
        self.button_create = qtw.QPushButton("Create Framework Template", self)
        self.button_create.clicked.connect(self.slotCreateFrameworkTemplate)

        # Arrange the instruction-related components and the button in a layout surrounded by spacers.
        # This ensures the widget is maximally compressed.
        layout_stretch_vertical = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Minimum, 
                                                        qtw.QSizePolicy.Expanding)
        layout_stretch_horizontal = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Expanding, 
                                                          qtw.QSizePolicy.Minimum)
        layout_horizontal = qtw.QHBoxLayout()
        layout_vertical = qtw.QVBoxLayout()
        layout_vertical.addItem(layout_stretch_vertical)
        
        layout_vertical.addLayout(layout_framework_instructions)
        layout_vertical.addWidget(self.button_create)
        
        layout_vertical.addItem(layout_stretch_vertical)
        layout_horizontal.addItem(layout_stretch_horizontal)
        layout_horizontal.addLayout(layout_vertical)
        layout_horizontal.addItem(layout_stretch_horizontal)
        self.setLayout(layout_horizontal)

        # Resize and center the GUI window as desired.
        # Note: If the window is not given a fixed size, it should compress tightly around its components.
#        resizeInScreen(self, fraction_width = GUISettings.DEFAULT_SCREEN_FRACTION_WIDTH, 
#                             fraction_height = GUISettings.DEFAULT_SCREEN_FRACTION_HEIGHT)
        centerInScreen(self)
        
    def slotUpdateFrameworkInstructions(self, item_type, number):
        """ Updates instructions relating to the amount of default framework items to produce in a template. """
        self.framework_instructions.updateNumberOfItems(item_type = item_type, number = number)
        
    def slotCreateFrameworkTemplate(self):
        """ Creates a template framework file at the location specified by the user. """
        framework_path = getSavePathFromUser(file_filter = "*"+SystemSettings.EXCEL_FILE_EXTENSION)
        if not framework_path.endswith(SystemSettings.EXCEL_FILE_EXTENSION):
            logger.warning("Abandoning framework template construction due to provided framework path not ending in '{0}'.".format(SystemSettings.EXCEL_FILE_EXTENSION))
            return
        try: createFrameworkTemplate(framework_path = framework_path, instructions = self.framework_instructions)
        except:
            logger.exception("Framework template construction has failed.")
            raise

#class GUIDatabookCreation(qtw.QWidget):
#    """ A widget for constructing an Excel-based databook file from a project framework. """

#    @logUsage
#    def __init__(self):
#        """ Initializes the databook creation GUI. """
#        super(GUIDatabookCreation, self).__init__()
#        self.initUIDatabookCreation()

#    @logUsage
#    def initUIDatabookCreation(self):
#        """ Initializes all UI elements for the databook creation GUI. """
#        self.setWindowTitle("Databook Construction")
#        self.resetAttributes()
#        self.developLayout()
#        self.show()
        
#    @logUsage
#    def resetAttributes(self):   
#        """ Resets all attributes related to this GUI; must be called once at initialization. """
#        # This widget is attached to an instructions object that the user can modify prior to producing a databook.
#        self.databook_instructions = DatabookInstructions()

#    @logUsage
#    def developLayout(self):
#        """ Lays out components of the databook creation GUI. """
#        # Produce a layout and memory space to store GUI components related to modifying instructions.
#        layout_databook_instructions = qtw.QGridLayout()
#        self.list_label_item_descriptors = []
#        self.list_spinbox_item_numbers = []
#        # Cycle through all page-item types referenced in the instructions object.
#        # Develop appropriate text for label widgets that describe each page-item type..
#        item_type_number = 0
#        for item_type in self.databook_instructions.num_items:
#            # STOP HERE.
#            descriptor = FrameworkSettings.ITEM_TYPE_SPECS[item_type]["descriptor"]
#            text_extra = "' items: "
#            if not FrameworkSettings.ITEM_TYPE_SPECS[item_type]["superitem_type"] is None:
#                superitem_type = FrameworkSettings.ITEM_TYPE_SPECS[item_type]["superitem_type"]
#                descriptor_extra = FrameworkSettings.ITEM_TYPE_SPECS[superitem_type]["descriptor"]
#                text_extra = "' subitems per '" + descriptor_extra + "' item: "
#            text = "Number of '" + descriptor + text_extra
#            self.list_label_item_descriptors.append(qtw.QLabel(text))
#            # Generate integer-input spinboxes and give them default values associated with the instructions object.
#            self.list_spinbox_item_numbers.append(qtw.QSpinBox())
#            self.list_spinbox_item_numbers[-1].setValue(self.framework_instructions.num_items[item_type])
#            # Ensure that user value changes are immediately propagated to the callback that updates the instructions object.
#            # Note: The lambda must include item_type definition to avoid closure issues, i.e. all spinboxes referencing the last page-item.
#            self.list_spinbox_item_numbers[-1].valueChanged.connect(lambda number, item_type=item_type: 
#                                                                    self.slotUpdateFrameworkInstructions(item_type=item_type, number=number))
#            # Arrange the label and spinbox components into the appropriate grid layout.
#            layout_framework_instructions.addWidget(self.list_label_item_descriptors[item_type_number],
#                                                    item_type_number, 0)
#            layout_framework_instructions.addWidget(self.list_spinbox_item_numbers[item_type_number],
#                                                    item_type_number, 1)
#            item_type_number += 1

#        # Create a template framework creation button and link it to the correct callback.
#        self.button_create = qtw.QPushButton("Create Framework Template", self)
#        self.button_create.clicked.connect(self.slotCreateFrameworkTemplate)

#        # Arrange the instruction-related components and the button in a layout surrounded by spacers.
#        # This ensures the widget is maximally compressed.
#        layout_stretch_vertical = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Minimum, 
#                                                        qtw.QSizePolicy.Expanding)
#        layout_stretch_horizontal = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Expanding, 
#                                                          qtw.QSizePolicy.Minimum)
#        layout_horizontal = qtw.QHBoxLayout()
#        layout_vertical = qtw.QVBoxLayout()
#        layout_vertical.addItem(layout_stretch_vertical)
        
#        layout_vertical.addLayout(layout_framework_instructions)
#        layout_vertical.addWidget(self.button_create)
        
#        layout_vertical.addItem(layout_stretch_vertical)
#        layout_horizontal.addItem(layout_stretch_horizontal)
#        layout_horizontal.addLayout(layout_vertical)
#        layout_horizontal.addItem(layout_stretch_horizontal)
#        self.setLayout(layout_horizontal)

#        centerInScreen(self)
        
#    def slotUpdateFrameworkInstructions(self, item_type, number):
#        """ Updates instructions relating to the amount of default framework items to produce in a template. """
#        self.framework_instructions.updateNumberOfItems(item_type = item_type, number = number)
        
#    def slotCreateFrameworkTemplate(self):
#        """ Creates a template framework file at the location specified by the user. """
#        framework_path = getSavePathFromUser(file_filter = "*"+SystemSettings.EXCEL_FILE_EXTENSION)
#        if not framework_path.endswith(SystemSettings.EXCEL_FILE_EXTENSION):
#            logger.warning("Abandoning framework template construction due to provided framework path not ending in '{0}'.".format(SystemSettings.EXCEL_FILE_EXTENSION))
#            return
#        try: createFrameworkTemplate(framework_path = framework_path, instructions = self.framework_instructions)
#        except:
#            logger.exception("Framework template construction has failed.")
#            raise

@logUsage
@returns(qtw.QWidget)
def runGUI():
    """ Function that launches all available back-end GUIs as they are developed. """
    app = qtw.QApplication(sys.argv)
    app.setApplicationName("Optima Core GUI")
    GUISettings.updateUsingApp(app)
    gui = GUIDemo()
    sys.exit(app.exec_())
    return gui      # Avoids pylint warning.