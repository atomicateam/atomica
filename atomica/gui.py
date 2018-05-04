# -*- coding: utf-8 -*-
"""
Atomica graphical user interface (GUI) file.
Contains back-end GUI wrappers for codebase functionality.
Note: Callback functions cannot be easily decorated, so logging is applied per method, not per class.
"""

from atomica.system import SystemSettings as SS
from atomica.structure_settings import FrameworkSettings as FS
from atomica.structure_settings import DataSettings as DS
from atomica.excel import ExcelSettings as ES

from atomica.system import log_usage, accepts, returns, logger
from atomica.framework import ProjectFramework
from atomica.workbook_export import WorkbookInstructions, writeWorkbook
from atomica.workbook_import import readWorkbook

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

    PIXEL_BUFFER_WIDTH = 20
    
    @classmethod
    @log_usage
    def updateUsingApp(cls, app):
        """ Some GUI settings cannot be determined without a PyQt application being generated first. """
        screen = app.desktop().availableGeometry()
        cls.SCREEN_WIDTH = screen.width()
        cls.SCREEN_HEIGHT = screen.height()

#%% Code for GUI convenience functions.

@log_usage
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

@log_usage
def getLoadPathFromUser(instance = None, title = None, file_filter = None):
    """ Convenience function that asks the user for a file-saving path. """
    try: path = getPathFromUser(instance = instance, load_not_save = True, title = title, file_filter = file_filter)
    except:
        logger.exception("An attempt to ask the user for a save-file path has failed.")
        raise
    return path

@log_usage
def getSavePathFromUser(instance = None, title = None, file_filter = None):
    """ Convenience function that asks the user for a file-loading path. """
    try: path = getPathFromUser(instance = instance, load_not_save = False, title = title, file_filter = file_filter)
    except:
        logger.exception("An attempt to ask the user for a load-file path has failed.")
        raise
    return path

@log_usage
@accepts(qtw.QWidget,float,float)
def resizeInScreen(widget, fraction_width, fraction_height):
    widget.resize(fraction_width*GUISettings.SCREEN_WIDTH, fraction_height*GUISettings.SCREEN_HEIGHT)

@log_usage
@accepts(qtw.QWidget)
def centerInScreen(widget):
    widget.setGeometry((GUISettings.SCREEN_WIDTH - widget.width())/2,
                       (GUISettings.SCREEN_HEIGHT - widget.height())/2,
                       widget.width(), widget.height())

@log_usage
@accepts(qtw.QLineEdit)
def resizeLineEditToContents(line_edit):
    """ Convenience function that resizes a line-edit text box to its contents. """
    font_metrics = line_edit.fontMetrics()
    line_edit.setMinimumWidth(font_metrics.boundingRect(line_edit.text()).width()+GUISettings.PIXEL_BUFFER_WIDTH)
    #line_edit.setFixedSize(font_metrics.boundingRect(line_edit.text()).width(), font_metrics.height())


#%% Code for GUIs.

class GUIDemo(qtw.QWidget):
    """ A demo window that displays a series of buttons for launching other Atomica widgets. """

    @log_usage
    def __init__(self):
        """ Initializes the demo GUI. """
        super(GUIDemo, self).__init__()
        self.initUIDemo()

    @log_usage
    def initUIDemo(self):
        """ Initializes all UI elements for the demo GUI. """

        self.setWindowTitle("GUI Demo")

        self.button_framework_file_creation = qtw.QPushButton("Create Framework Template", self)
        self.button_framework_file_creation.clicked.connect(self.slotRunGUIFrameworkFileCreation)

        self.button_databook_creation = qtw.QPushButton("Create Databook", self)
        self.button_databook_creation.clicked.connect(self.slotRunGUIDatabookCreation)

        layout = qtw.QVBoxLayout(self)
        layout.addWidget(self.button_framework_file_creation)
        layout.addWidget(self.button_databook_creation)
        self.setLayout(layout)

        centerInScreen(self)

        self.show()
        
    def slotRunGUIFrameworkFileCreation(self):
        """ Launches the sub-GUI for constructing a framework template. """
        self.subgui = GUIFrameworkFileCreation()

    def slotRunGUIDatabookCreation(self):
        """ Launches the sub-GUI for constructing a databook. """
        self.subgui = GUIDatabookCreation()
        
class GUIFrameworkFileCreation(qtw.QWidget):
    """ A widget for constructing an Excel-based template framework file. """

    @log_usage
    def __init__(self):
        """ Initializes the framework template GUI. """
        super(GUIFrameworkFileCreation, self).__init__()
        self.initUIFrameworkFileCreation()

    @log_usage
    def initUIFrameworkFileCreation(self):
        """ Initializes all UI elements for the framework template GUI. """
        self.setWindowTitle("Framework Template Construction")
        self.resetAttributes()
        self.developLayout()
        self.show()
        
    @log_usage
    def resetAttributes(self):   
        """ Resets all attributes related to this GUI; must be called once at initialization. """
        # This widget is attached to an instructions object that the user can modify prior to producing a template framework.
        self.framework_instructions = WorkbookInstructions(workbook_type = SS.STRUCTURE_KEY_FRAMEWORK)

    @log_usage
    def developLayout(self):
        """ Lays out components of the framework template GUI. """
        # Produce a layout and memory space to store GUI components related to modifying instructions.
        layout_framework_instructions = qtw.QGridLayout()
        self.list_label_item_descriptors = []
        self.list_spinbox_item_numbers = []
        # Cycle through all page-item types referenced in the instructions object.
        # Develop appropriate text for label widgets that describe each page-item type.
        item_type_number = 0
        for item_type in self.framework_instructions.num_items:
            descriptor = FS.ITEM_TYPE_SPECS[item_type]["descriptor"]
            text_extra = "' items: "
            if not FS.ITEM_TYPE_SPECS[item_type]["superitem_type"] is None:
                superitem_type = FS.ITEM_TYPE_SPECS[item_type]["superitem_type"]
                descriptor_extra = FS.ITEM_TYPE_SPECS[superitem_type]["descriptor"]
                text_extra = "' subitems per '" + descriptor_extra + "' item: "
            text = "Number of '" + descriptor + text_extra
            self.list_label_item_descriptors.append(qtw.QLabel(text))
            # Generate integer-input spinboxes and give them default values associated with the instructions object.
            self.list_spinbox_item_numbers.append(qtw.QSpinBox())
            self.list_spinbox_item_numbers[-1].set_value(self.framework_instructions.num_items[item_type])
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
        framework_path = getSavePathFromUser(file_filter = "*"+ES.FILE_EXTENSION)
        if not framework_path.endswith(ES.FILE_EXTENSION):
            logger.warning("Abandoning framework template construction due to provided framework path not ending in '{0}'.".format(ES.FILE_EXTENSION))
            return
        try: writeWorkbook(workbook_path = framework_path, instructions = self.framework_instructions, workbook_type = SS.STRUCTURE_KEY_FRAMEWORK)
        except:
            logger.exception("Framework template construction has failed.")
            raise

class GUIDatabookCreation(qtw.QWidget):
    """ A widget for constructing an Excel-based databook file from a project framework. """

    @log_usage
    def __init__(self):
        """ Initializes the databook creation GUI. """
        super(GUIDatabookCreation, self).__init__()
        self.initUIDatabookCreation()

    @log_usage
    def initUIDatabookCreation(self):
        """ Initializes all UI elements for the databook creation GUI. """
        self.setWindowTitle("Databook Construction")
        self.resetAttributes()
        self.developLayout()
        self.show()
        
    @log_usage
    def resetAttributes(self):   
        """ Resets all attributes related to this GUI; must be called once at initialization. """
        # This widget is attached to an instructions object that the user can modify prior to producing a databook.
        self.databook_instructions = WorkbookInstructions(workbook_type = SS.STRUCTURE_KEY_DATA)
        self.framework = ProjectFramework()

    @log_usage
    def developLayout(self):
        """ Lays out components of the databook creation GUI. """
        # Produce a layout and memory space to store GUI components related to modifying instructions.
        layout_databook_instructions = qtw.QGridLayout()
        self.list_label_item_descriptors = []
        self.list_spinbox_item_numbers = []
        # Cycle through all page-item types referenced in the instructions object.
        # Develop appropriate text for label widgets that describe each page-item type.
        item_type_number = 0
        for item_type in self.databook_instructions.num_items:
            descriptor = DS.ITEM_TYPE_SPECS[item_type]["descriptor"]
            text_extra = "' items: "
            text = "Number of '" + descriptor + text_extra
            self.list_label_item_descriptors.append(qtw.QLabel(text))
            # Generate integer-input spinboxes and give them default values associated with the instructions object.
            self.list_spinbox_item_numbers.append(qtw.QSpinBox())
            self.list_spinbox_item_numbers[-1].set_value(self.databook_instructions.num_items[item_type])
            # Ensure that user value changes are immediately propagated to the callback that updates the instructions object.
            # Note: The lambda must include item_type definition to avoid closure issues, i.e. all spinboxes referencing the last databook item.
            self.list_spinbox_item_numbers[-1].valueChanged.connect(lambda number, item_type=item_type: 
                                                                    self.slotUpdateDatabookInstructions(item_type=item_type, number=number))
            # Arrange the label and spinbox components into the appropriate grid layout.
            layout_databook_instructions.addWidget(self.list_label_item_descriptors[item_type_number],
                                                    item_type_number, 0)
            layout_databook_instructions.addWidget(self.list_spinbox_item_numbers[item_type_number],
                                                    item_type_number, 1)
            item_type_number += 1

        # Create a framework loading button and link it to the correct callback.
        # Also create a read-only line-edit label for the framework name, as well as an appropriate label.
        self.button_import_framework = qtw.QPushButton("Import Framework", self)
        self.button_import_framework.clicked.connect(self.slotImportFramework)
        self.label_framework_name = qtw.QLabel("Framework: ")
        self.label_framework_name.setVisible(self.framework.name != "")
        self.edit_framework_name = qtw.QLineEdit()
        self.edit_framework_name.setReadOnly(True)
        self.edit_framework_name.setAlignment(qtc.Qt.AlignCenter)
        self.edit_framework_name.setText(self.framework.name)
        self.edit_framework_name.setVisible(self.framework.name != "")
        layout_import_framework = qtw.QVBoxLayout()
        layout_framework_name = qtw.QHBoxLayout()
        layout_framework_name.addWidget(self.label_framework_name)
        layout_framework_name.addWidget(self.edit_framework_name)
        layout_import_framework.addWidget(self.button_import_framework)
        layout_import_framework.addLayout(layout_framework_name)
            
        # Create a databook creation button and link it to the correct callback.
        self.button_create = qtw.QPushButton("Create Databook", self)
        self.button_create.clicked.connect(self.slotCreateDatabook)

        # Arrange the instruction-related components and the button in a layout surrounded by spacers.
        # This ensures the widget is maximally compressed.
        layout_stretch_vertical = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Minimum, 
                                                        qtw.QSizePolicy.Expanding)
        layout_stretch_horizontal = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Expanding, 
                                                          qtw.QSizePolicy.Minimum)
        layout_horizontal = qtw.QHBoxLayout()
        layout_vertical = qtw.QVBoxLayout()
        layout_vertical.addItem(layout_stretch_vertical)
        
        layout_vertical.addLayout(layout_import_framework)
        layout_vertical.addLayout(layout_databook_instructions)
        layout_vertical.addWidget(self.button_create)
        
        layout_vertical.addItem(layout_stretch_vertical)
        layout_horizontal.addItem(layout_stretch_horizontal)
        layout_horizontal.addLayout(layout_vertical)
        layout_horizontal.addItem(layout_stretch_horizontal)
        self.setLayout(layout_horizontal)

        centerInScreen(self)
        
    def slotUpdateDatabookInstructions(self, item_type, number):
        """ Updates instructions relating to the amount of default items to produce in a databook. """
        self.databook_instructions.updateNumberOfItems(item_type = item_type, number = number)

    def slotImportFramework(self):
        """ Imports a framework file from the location specified by the user. """
        framework_path = getLoadPathFromUser(file_filter = "*"+ES.FILE_EXTENSION)
        if not framework_path.endswith(ES.FILE_EXTENSION):
            logger.warning("Abandoning framework file import due to provided framework path not ending in '{0}'.".format(ES.FILE_EXTENSION))
            return
        try:
            readWorkbook(workbook_path = framework_path, framework = self.framework, workbook_type = SS.STRUCTURE_KEY_FRAMEWORK)
            self.edit_framework_name.setText(self.framework.name)
            resizeLineEditToContents(self.edit_framework_name)
            self.label_framework_name.setVisible(self.framework.name != "")
            self.edit_framework_name.setVisible(self.framework.name != "")
        except:
            logger.exception("Framework file import has failed.")
            raise
        
    def slotCreateDatabook(self):
        """ Creates a databook at the location specified by the user. """
        databook_path = getSavePathFromUser(file_filter = "*"+ES.FILE_EXTENSION)
        if not databook_path.endswith(ES.FILE_EXTENSION):
            logger.warning("Abandoning databook construction due to provided databook path not ending in '{0}'.".format(ES.FILE_EXTENSION))
            return
        try: writeWorkbook(workbook_path = databook_path, framework = self.framework, instructions = self.databook_instructions, workbook_type = SS.STRUCTURE_KEY_DATA)
        except:
            logger.exception("Databook construction has failed.")
            raise

@log_usage
@returns(qtw.QWidget)
def runGUI():
    """ Function that launches all available back-end GUIs as they are developed. """
    app = qtw.QApplication(sys.argv)
    app.setApplicationName("Atomica GUI")
    GUISettings.updateUsingApp(app)
    gui = GUIDemo()
    sys.exit(app.exec_())
    return gui      # Avoids pylint warning.