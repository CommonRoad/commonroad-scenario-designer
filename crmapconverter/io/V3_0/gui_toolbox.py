import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from crmapconverter.io.V3_0.GUI_src import CR_Scenario_Designer


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

    def __init__(self):
        super().__init__()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.tree.setIndentation(0)
        self.setGeometry(0, 0, 280, 500)
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

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        widget1 = QFrame(self.tree)
        layout1 = QGridLayout(widget1)

        """add Roundabout button"""
        button_roundabout = QPushButton()
        button_roundabout.setText("Roundabout")
        button_roundabout.setIcon(QIcon(":/icons/button_roundabout.png"))
        layout1.addWidget(button_roundabout, 0, 0)

        """add traffic light button"""
        button_traffic_light = QPushButton()
        button_traffic_light.setText("Traffic Light")
        button_traffic_light.setIcon(QIcon(":/icons/button_traffic_light.png"))
        layout1.addWidget(button_traffic_light, 0, 1)

        """add stop button"""
        button_stop = QPushButton()
        button_stop.setText("Stop")
        button_stop.setIcon(QIcon(":/icons/button_stop.png"))
        layout1.addWidget(button_stop, 1, 0)

        """add yield button"""
        button_yield = QPushButton()
        button_yield.setText("Yield")
        button_yield.setIcon(QIcon(":/icons/button_yeld.png"))
        layout1.addWidget(button_yield, 1, 1)

        layout1.addItem(self.spacerItem)
        title1 = "Tools for Lanelet editing"
        self.sections.append((title1, widget1))

        """add button for lanelets list"""
        self.button_lanlist = QPushButton("Lanelets list")
        self.button_lanlist.setToolTip("Show Lanelets list")
        layout1.addWidget(self.button_lanlist, 2, 0)

        """add button for Intersection list"""
        self.button_intersection_list = QPushButton("Intersection list")
        self.button_intersection_list.setToolTip("Show Intersection list")
        layout1.addWidget(self.button_intersection_list, 2, 1)

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
