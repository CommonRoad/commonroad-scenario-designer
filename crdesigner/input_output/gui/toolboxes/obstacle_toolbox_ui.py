from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crdesigner.input_output.gui.toolboxes.toolbox_ui import Toolbox

from commonroad.scenario.obstacle import ObstacleType

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import logging

# try to import sumo functionality
try:
    from crdesigner.map_conversion.sumo_map.config import SumoConfig
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
    from sumocr.interface.sumo_simulation import SumoSimulation
    from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMOSimulation
    SUMO_AVAILABLE = True
except ImportError:
    logging.warning("Cannot import SUMO, simulation will not be offered in Scenario Designer")
    SUMO_AVAILABLE = False


class ObstacleToolboxUI(Toolbox):
    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        #TODO somehow create a validator that checks so can only input 2 doubles
        #this validator always has the format with a dot as decimal separator
        self.float_validator = QDoubleValidator()
        self.float_validator.setLocale(QLocale("en_US"))

        #  Lanelet Section
        widget_obstacles = QFrame(self.tree)
        layout_obstacles = QVBoxLayout(widget_obstacles)

        label_general = QLabel("Obstacle Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Bold))

        self.obstacle_shape = QComboBox()
        self.obstacle_shape.addItem("Rectangle")
        self.obstacle_shape.addItem("Circle")
        self.obstacle_shape.addItem("Polygon")

        self.obstacle_type = QComboBox()
        obstalce_type_list = [e.value for e in ObstacleType]
        self.obstacle_type.addItems(obstalce_type_list)

        self.obstacle_state_variable = QComboBox()
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.selected_obstacle = QComboBox()
        self.button_update_obstacle = QPushButton("Update")
        self.button_remove_obstacle = QPushButton("Remove")
        self.button_add_static_obstacle = QPushButton("Add")

        self.layout_obstacle_information_groupbox = QFormLayout()
        self.init_rectangle_fields()
        self.obstacle_information_groupbox = QGroupBox()
        self.obstacle_information_groupbox.setLayout(self.layout_obstacle_information_groupbox)
        self.layout_obstacle_information_groupbox.insertRow(0, label_general)
        self.layout_obstacle_information_groupbox.insertRow(1, "Shape", self.obstacle_shape)
        self.layout_obstacle_information_groupbox.insertRow(5, "Type", self.obstacle_type)
        self.init_position()

        layout_obstacle_state_vis_groupbox = QFormLayout()
        obstacle_state_vis_groupbox = QGroupBox()
        obstacle_state_vis_groupbox.setLayout(layout_obstacle_state_vis_groupbox)
        layout_vis_selection = QFormLayout()
        layout_vis_selection.insertRow(8, "Visualized State:", self.obstacle_state_variable)
        layout_obstacle_state_vis_groupbox.addRow(layout_vis_selection)
        layout_obstacle_state_vis_groupbox.addWidget(self.toolbar)
        layout_obstacle_state_vis_groupbox.addWidget(self.canvas)
        self.layout_obstacle_information_groupbox.addRow(obstacle_state_vis_groupbox)
        layout_obstacles.addWidget(self.obstacle_information_groupbox)

        layout_obstacle_buttons = QFormLayout()
        layout_obstacle_buttons.addRow("Selected Obstacle ID:", self.selected_obstacle)
        layout_obstacle_buttons.addRow(self.button_update_obstacle)
        layout_obstacle_buttons.addRow(self.button_remove_obstacle)
        layout_obstacle_buttons.addRow(self.button_add_static_obstacle)
        layout_obstacles.addLayout(layout_obstacle_buttons)

        title_obstacle = "Obstacle"
        self.sections.append((title_obstacle, widget_obstacles))

        # --Section SUMO Simulation-
        if SUMO_AVAILABLE:
            widget_sumo = SUMOSimulation(self.tree)
            layout_sumo = QFormLayout(widget_sumo)

            self.button_start_simulation = QPushButton("Simulate")
            self.sumo_simulation_length = QSpinBox()
            self.sumo_simulation_length.setMinimum(10)
            self.sumo_simulation_length.setMaximum(10000)
            self.sumo_simulation_length.setValue(200)

            layout_sumo.addRow("Number Time Steps:", self.sumo_simulation_length)
            layout_sumo.addRow(self.button_start_simulation)

            title_sumo = "Sumo Simulation"
            self.sections.append((title_sumo, widget_sumo))
    
    def init_rectangle_fields(self):
    #function that creates the fields for the rectangle shape
            self.obstacle_length = QLineEdit()
            self.obstacle_length.setValidator(self.float_validator)
            self.obstacle_length.setMaxLength(6)
            self.obstacle_length.setAlignment(Qt.AlignRight)

            self.obstacle_width = QLineEdit()
            self.obstacle_width.setValidator(self.float_validator)
            self.obstacle_width.setMaxLength(4)
            self.obstacle_width.setAlignment(Qt.AlignRight)

            self.obstacle_orientation = QLineEdit()
            self.obstacle_orientation.setValidator(QIntValidator())
            self.obstacle_orientation.setMaxLength(4)
            self.obstacle_orientation.setAlignment(Qt.AlignRight)

            self.layout_obstacle_information_groupbox.insertRow(2, "Width [m]", self.obstacle_width)
            self.layout_obstacle_information_groupbox.insertRow(3, "Length [m]", self.obstacle_length)
            self.layout_obstacle_information_groupbox.insertRow(4, "Orientation [deg]",self.obstacle_orientation)
    
    def remove_rectangle_fields(self):
    #function that removes the fields unique to the rectangle shape
        try:
            self.layout_obstacle_information_groupbox.removeRow(self.obstacle_width)
            self.layout_obstacle_information_groupbox.removeRow(self.obstacle_length)
            self.layout_obstacle_information_groupbox.removeRow(self.obstacle_orientation)
        except:
            pass
    
    def init_circle_fields(self):
    #function that creates the fields for the circle shape
        self.obstacle_radius = QLineEdit()
        self.obstacle_radius.setValidator(self.float_validator)
        self.obstacle_radius.setMaxLength(4)
        self.obstacle_radius.setAlignment(Qt.AlignRight)

        self.layout_obstacle_information_groupbox.insertRow(2, "Radius [m]", self.obstacle_radius)

    def remove_circle_fields(self):
    #function that removes the fields for the circle shape
        try:
            self.layout_obstacle_information_groupbox.removeRow(self.obstacle_radius)
        except:
            pass
    def remove_polygon_fields(self):
    #function that removes the fields for the polygon shape
        try:
            for i in range(self.amount_vertices):
                self.layout_obstacle_information_groupbox.removeRow(self.polygon_row[i])
                
            self.layout_obstacle_information_groupbox.removeRow(self.add_vertice_btn)
        except:
            pass
    
    def init_position(self):
    #function that adds the position fields
        self.obstacle_x_Position = QLineEdit()
        self.obstacle_x_Position.setValidator(self.float_validator)
        self.obstacle_x_Position.setMaxLength(4)
        self.obstacle_x_Position.setAlignment(Qt.AlignRight)

        self.obstacle_y_Position = QLineEdit()
        self.obstacle_y_Position.setValidator(self.float_validator)
        self.obstacle_y_Position.setMaxLength(4)
        self.obstacle_y_Position.setAlignment(Qt.AlignRight)

        if self.obstacle_shape.currentText() == "Rectangle":
            self.layout_obstacle_information_groupbox.insertRow(6, "X-Position", self.obstacle_x_Position)
            self.layout_obstacle_information_groupbox.insertRow(7, "Y-Position", self.obstacle_y_Position)
        elif self.obstacle_shape.currentText() == "Circle":
            self.layout_obstacle_information_groupbox.insertRow(4, "X-Position", self.obstacle_x_Position)
            self.layout_obstacle_information_groupbox.insertRow(5, "Y-Position", self.obstacle_y_Position)
    
    def remove_position(self):
    #function that adds the position fields
        try:
            self.layout_obstacle_information_groupbox.removeRow(self.obstacle_x_Position)
            self.layout_obstacle_information_groupbox.removeRow(self.obstacle_y_Position)
        except:
            pass

    def toggle_sections(self):
    #changes toolbox based on what shapes that are selected
        if self.obstacle_shape.currentText() == "Circle":
            
            self.remove_rectangle_fields()
            self.remove_polygon_fields()
            self.remove_position()
            
            self.init_circle_fields()
            self.init_position()

        elif self.obstacle_shape.currentText() == "Rectangle":
            
            self.remove_circle_fields()
            self.remove_polygon_fields()
            self.remove_position()

            self.init_rectangle_fields()
            self.init_position()

        elif self.obstacle_shape.currentText() == "Polygon":
            
            self.remove_circle_fields()
            self.remove_rectangle_fields()
            self.remove_position()

            self.vertices_x = []
            self.vertices_y = []
            self.polygon_row = []
            self.remove_vertice_btn = []
            self.polygon_label = []
            self.amount_vertices = 0

            for i in range(3): 
                self.add_vertice()
            
            self.add_vertice_btn = QPushButton("Add Vertice")
            self.add_vertice_btn.clicked.connect(
                lambda: self.add_vertice())
            self.layout_obstacle_information_groupbox.insertRow(len(self.vertices_x) + 2, self.add_vertice_btn)

    #add vertices for the polygon shape, i is the place in the array
    def add_vertice(self):
        i = len(self.vertices_x)
        self.polygon_row.append(QHBoxLayout())

        self.polygon_label.append(QLabel("Vertice " + str(i)))
        
        self.vertices_x.append(QLineEdit())
        self.vertices_x[i].setValidator(self.float_validator)
        self.vertices_x[i].setMaxLength(6)
        self.vertices_x[i].setAlignment(Qt.AlignRight)

        self.vertices_y.append(QLineEdit())
        self.vertices_y[i].setValidator(self.float_validator)
        self.vertices_y[i].setMaxLength(6)
        self.vertices_y[i].setAlignment(Qt.AlignRight)

        self.polygon_row[i].addWidget(self.polygon_label[i])
        self.polygon_row[i].addWidget(self.vertices_x[i])
        self.polygon_row[i].addWidget(self.vertices_y[i])

        self.remove_vertice_btn.append(QPushButton())
        self.remove_vertice_btn[i].setIcon(QIcon(":icons/iconmonstr-trash-can-1.svg"))
        self.remove_vertice_btn[i].clicked.connect(
            lambda: self.remove_vertice())
        self.polygon_row[i].addWidget(self.remove_vertice_btn[i])

        self.layout_obstacle_information_groupbox.insertRow(i+2, self.polygon_row[i])
        self.amount_vertices = self.amount_vertices + 1

    def remove_vertice(self, i = None):
        #check so there is at least 3 vertices
        if len(self.vertices_x) <= 3:
            #TODO add some kind of warning message that you have to have at least 3 vertices
            return
        if i == None:
            sending_button = self.sender()
            i = self.remove_vertice_btn.index(sending_button)

        self.layout_obstacle_information_groupbox.removeRow(self.polygon_row[i])
        self.vertices_x.pop(i)
        self.vertices_y.pop(i)
        self.remove_vertice_btn.pop(i)
        self.polygon_label.pop(i)
        self.polygon_row.pop(i)
        self.amount_vertices = self.amount_vertices - 1

        for j in range(self.amount_vertices):
            self.polygon_label[j].setText("Vertice " + str(j)) 

            
            

        


        