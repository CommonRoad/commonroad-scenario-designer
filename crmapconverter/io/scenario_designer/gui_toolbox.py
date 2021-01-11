import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from crmapconverter.io.scenario_designer.gui_src import CR_Scenario_Designer


class SectionExpandButton(QPushButton):
    """a QPushbutton that can expand or collapse its section"""

    def __init__(self, item, text="", parent=None):
        super().__init__(text, parent)
        self.section = item
        self.setStyleSheet("background-color: rgb(198, 198, 198);")
        self.section.setExpanded(True)
        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        """toggle expand/collapse of section by clicking"""
        if self.section.isExpanded():
            self.section.setExpanded(False)
        else:
            self.section.setExpanded(True)


class UpperToolbox(QWidget):
    """a dialog to which collapsible sections can be added;
    reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
        """
    button_sumo_simulation = None
    button_forwards = None

    def __init__(self):
        super().__init__()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.tree.setIndentation(0)
        self.setGeometry(0, 0, 250, 500)
        self.spacerItem = QSpacerItem(
            0, 50, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # layout.addItem(self.spacerItem)

        self.sections = []
        self.define_sections()
        self.add_sections()

    def add_sections(self):
        """adds a collapsible sections for every
            (title, widget) tuple in self.sections
            """
        for (title, widget) in self.sections:
            button1 = self.add_button(title)
            section1 = self.add_widget(button1, widget)
            button1.addChild(section1)

    #def clicked(self):
        #print("clicked")
       #click_curve(self, width=3, radius=50, angle=np.pi / 2, num_vertices=30, rot_angle=0):

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """

        """Section Traffic Signs/ Traffic Lights"""
        widget1 = QFrame(self.tree)
        layout1 = QGridLayout(widget1)

        self.button_traffic_signs = QPushButton()
        self.button_traffic_signs.setText("Traffic signs")
        layout1.addWidget(self.button_traffic_signs, 0, 0)

        self.button_traffic_signs_settings = QPushButton()
        self.button_traffic_signs_settings.setText("Settings")
        layout1.addWidget(self.button_traffic_signs_settings, 0, 1)

        """add Roundabout button
        button_roundabout = QPushButton()
        button_roundabout.setText("Roundabout")
        button_roundabout.setIcon(QIcon(":/icons/button_roundabout.png"))
        layout1.addWidget(button_roundabout, 0, 0)

        add traffic light button
        button_traffic_light = QPushButton()
        button_traffic_light.setText("Traffic Light")
        button_traffic_light.setIcon(QIcon(":/icons/button_traffic_light.png"))
        layout1.addWidget(button_traffic_light, 0, 1)

        button_stop = QPushButton()
        button_stop.setText("Stop")
        button_stop.setIcon(QIcon(":/icons/button_stop.png"))
        layout1.addWidget(button_stop, 1, 0)

       
        button_yield = QPushButton()
        button_yield.setText("Yield")
        button_yield.setIcon(QIcon(":/icons/button_yeld.png"))
        layout1.addWidget(button_yield, 1, 1)"""

        "add show more button for lanelets list"""
        self.button_lanlist = QPushButton("show more")
        self.button_lanlist.setToolTip("Show more Traffic Signs")
        layout1.addWidget(self.button_lanlist, 2, 0)
        # TODO: add list of more traffic signs

        layout1.addItem(self.spacerItem)
        title1 = "Traffic Signs"
        self.sections.append((title1, widget1))


        #--Section lanelets--

        widgetlanelets = QFrame(self.tree)
        layoutlanelets = QGridLayout(widgetlanelets)

        self.button_forwards = QPushButton()
        self.button_forwards.setText("forwards")
        self.button_forwards.setIcon(QIcon(":/forwards.PNG"))
        layoutlanelets.addWidget(self.button_forwards, 1, 0)

        self.button_lanelet_settings = QPushButton()
        self.button_lanelet_settings.setText("settings")
        layoutlanelets.addWidget(self.button_lanelet_settings, 1, 1)
        self.button_lanelet_settings.setIcon(QIcon(":/gui_src/forwards.PNG"))

        self.button_turn_right = QPushButton()
        self.button_turn_right.setText("curve")
        layoutlanelets.addWidget(self.button_turn_right, 2, 0)
        self.button_turn_right.setIcon(QIcon(":/gui_src/forwards.PNG"))

        self.button_curve_settings = QPushButton()
        self.button_curve_settings.setText("settings")
        layoutlanelets.addWidget(self.button_curve_settings, 2, 1)
        self.button_curve_settings.setIcon(QIcon(":/gui_src/forwards.PNG"))

        self.button_turn_left = QPushButton()
        self.button_turn_left.setText("turn left")
        #layoutlanelets.addWidget(self.button_turn_left, 3, 0)
        self.button_turn_left.setIcon(QIcon(":/gui_src/forwards.PNG"))

        self.button_curve_settings2 = QPushButton()
        self.button_curve_settings2.setText("settings")
        #layoutlanelets.addWidget(self.button_curve_settings2, 3, 1)
        self.button_curve_settings2.setIcon(QIcon(":/gui_src/forwards.PNG"))

        #Fit to Predecessor
        self.button_fit_to_predecessor = QPushButton()
        self.button_fit_to_predecessor.setText("Fit to Predecessor")
        layoutlanelets.addWidget(self.button_fit_to_predecessor, 4, 0)
        self.button_fit_to_predecessor.setIcon(QIcon(":/gui_src/forwards.PNG"))

        #adjacent
        self.button_adjacent = QPushButton()
        self.button_adjacent.setText("Create Adjacent\nLanelet")
        layoutlanelets.addWidget(self.button_adjacent, 5, 0)
        self.button_adjacent.setIcon(QIcon(":/gui_src/forwards.PNG"))

        # connect lanelets
        self.button_connect_lanelets = QPushButton()
        self.button_connect_lanelets.setText("Connect two Lanelets")
        layoutlanelets.addWidget(self.button_connect_lanelets, 6, 0)
        self.button_connect_lanelets.setIcon(QIcon(":/gui_src/forwards.PNG"))

        # remove lanelet
        self.button_remove_lanelet = QPushButton()
        self.button_remove_lanelet.setText("Remove Lanelet")
        layoutlanelets.addWidget(self.button_remove_lanelet, 7, 0)
        self.button_remove_lanelet.setIcon(QIcon(":/gui_src/forwards.PNG"))

        #button_turn_left_45 = QPushButton()
        #button_turn_left_45.setText("show more")
        # button_turn_right.setIcon(QIcon(":/icons/Groupe_2.png"))
        #layoutlanelets.addWidget(button_turn_left_45, 3, 0)
        # widgetlanelets.addItem(spacerItem)

        titlelanelets = "Lanelets"
        self.sections.append((titlelanelets, widgetlanelets))

        #--Section intersections--

        widgetintersection = QFrame(self.tree)
        layoutintersection = QGridLayout(widgetintersection)

        button_X = QPushButton()
        button_X.setText("X")
        button_X.setIcon(QIcon(":/icons/forwards.PNG"))
        layoutintersection.addWidget(button_X, 1, 0)

        button_T = QPushButton()
        button_T.setText("T")
        layoutintersection.addWidget(button_T, 1, 1)
        button_T.setIcon(QIcon(":/gui_src/forwards.PNG"))

        # button_T_2 = QPushButton()
        # button_T_2.setText("T_2")
        # button_turn_right.setIcon(QIcon(":/icons/Groupe_2.png"))
        # layoutintersection.addWidget(button_T_2, 1, 2)
        # button_T_2.setIcon(QIcon(":/gui_src/forwards.PNG"))

        button_T_3 = QPushButton()
        button_T_3.setText("T_3")
        layoutintersection.addWidget(button_T_3, 2, 0)
        button_T_3.setIcon(QIcon(":/gui_src/forwards.PNG"))

        button_T_4 = QPushButton()
        button_T_4.setText("T_4")
        layoutintersection.addWidget(button_T_4, 2, 1)
        button_T_4.setIcon(QIcon(":/gui_src/forwards.PNG"))

        button_T_5 = QPushButton()
        button_T_5.setText("show more")
        layoutintersection.addWidget(button_T_5, 3, 0)
        button_T_4.setIcon(QIcon(":/gui_src/forwards.PNG"))

        titleintersection = "Intersections"
        self.sections.append((titleintersection, widgetintersection))

        # --Section Obstacles--

        widgetobstacles = QFrame(self.tree)
        layoutobstacles = QGridLayout(widgetobstacles)

        button_obstacle1 = QPushButton()
        button_obstacle1.setText("Obstacle1")
        button_obstacle1.setIcon(QIcon(":/icons/forwards.PNG"))
        layoutobstacles.addWidget(button_obstacle1, 1, 0)

        button_obstacle2 = QPushButton()
        button_obstacle2.setText("Obstacle2")
        button_obstacle2.setIcon(QIcon(":/icons/forwards.PNG"))
        layoutobstacles.addWidget(button_obstacle2, 2, 0)

        button_obstacle3 = QPushButton()
        button_obstacle3.setText("Obstacle3")
        button_obstacle3.setIcon(QIcon(":/icons/forwards.PNG"))
        layoutobstacles.addWidget(button_obstacle3, 3, 0)

        titleobstacles = "Obstacles"
        self.sections.append((titleobstacles, widgetobstacles))

        """"""""""""""

        widget2 = QFrame(self.tree)
        layout2 = QGridLayout(widget2)
        """ add animation button """
        self.button_sumo_simulation = QPushButton()
        self.button_sumo_simulation.setText("Show SUMO Setting")
        self.button_sumo_simulation.setIcon(QIcon(":/icons/Groupe_2.png"))
        layout2.addWidget(self.button_sumo_simulation, 0, 0)

        """add Save menu"""
        self.lb = QLabel("")
        self.save_menu = QComboBox()
        self.save_menu.addItem("Save as mp4")
        self.save_menu.addItem("Save as gif")
        self.save_menu.currentIndexChanged.connect(self.selection_change)
        layout2.addWidget(self.save_menu)
        layout2.addWidget(self.lb)

        """add SAVE button"""
        self.button_save = QPushButton(self)
        self.button_save.setText("Save animation")
        self.button_save.setIcon(QIcon(":/icons/botton_save.png"))
        layout2.addWidget(self.button_save)

        layout2.addItem(self.spacerItem)

        # layout2.addItem(self.spacerItem)
        title2 = "Tools for Animation"
        self.sections.append((title2, widget2))

    def selection_change(self):
        self.lb.setText(self.save_menu.currentText())

    def add_button(self, title):
        """creates a QTreeWidgetItem containing a button
        to expand or collapse its section
        """
        item = QTreeWidgetItem()
        self.tree.addTopLevelItem(item)
        self.tree.setItemWidget(item, 0, SectionExpandButton(item, text=title))
        return item

    def add_widget(self, button, widget):
        """creates a QWidgetItem containing the widget,
        as child of the button-QWidgetItem
        """
        section = QTreeWidgetItem(button)
        section.setDisabled(True)
        self.tree.setItemWidget(section, 0, widget)
        return section


class SumoTool(QWidget):
    """a widget to config the sumo silmulation tools
            """

    def __init__(self, parent=None):
        super(SumoTool, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.tree.setIndentation(0)
        self.setGeometry(0, 0, 280, 800)
        self.spacerItem = QSpacerItem(
            0, 50, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # layout.addItem(self.spacerItem)

        self.sections = []
        self.define_sections()
        self.add_sections()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """


    def add_sections(self):
        """adds a collapsible sections for every
            (title, widget) tuple in self.sections
            """
        for (title, widget) in self.sections:
            button1 = self.add_button(title)
            section1 = self.add_widget(button1, widget)
            button1.addChild(section1)

    def add_button(self, title):
        """creates a QTreeWidgetItem containing a button
        to expand or collapse its section
        """
        item = QTreeWidgetItem()
        self.tree.addTopLevelItem(item)
        self.tree.setItemWidget(item, 0, SectionExpandButton(item, text=title))
        return item

    def add_widget(self, button, widget):
        """creates a QWidgetItem containing the widget,
        as child of the button-QWidgetItem
        """
        section = QTreeWidgetItem(button)
        section.setDisabled(True)
        self.tree.setItemWidget(section, 0, widget)
        return section


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UpperToolbox()
    window.show()
    sumo = SumoTool()
    sumo.show()
    sys.exit(app.exec_())
