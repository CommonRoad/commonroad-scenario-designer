import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from crmapconverter.io.scenario_designer.gui_src import CR_Scenario_Designer
from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking



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
        self.button_traffic_signs.setText("Traffic sign")
        layout1.addWidget(self.button_traffic_signs, 0, 0)

        self.button_traffic_signs_settings = QPushButton()
        self.button_traffic_signs_settings.setText("Settings")
        layout1.addWidget(self.button_traffic_signs_settings, 0, 1)

        self.button_traffic_light = QPushButton()
        self.button_traffic_light.setText("Traffic light")
        layout1.addWidget(self.button_traffic_light, 1, 0)

        self.edit_button_traffic_light = QPushButton()
        self.edit_button_traffic_light.setText("edit Traffic light")
        layout1.addWidget(self.edit_button_traffic_light, 1, 1)

        self.delete_traffic_sign = QPushButton()
        self.delete_traffic_sign.setText("delete Traffic element")
        layout1.addWidget(self.delete_traffic_sign,2,0)

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
        #layout1.addWidget(self.button_lanlist, 2, 0)
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

        self.button_X = QPushButton()
        self.button_X.setText("X")
        self.button_X.setIcon(QIcon(":/icons/forwards.PNG"))
        layoutintersection.addWidget(self.button_X, 1, 0)

        self.button_T = QPushButton()
        self.button_T.setText("T")
        layoutintersection.addWidget(self.button_T, 1, 1)
        self.button_T.setIcon(QIcon(":/gui_src/forwards.PNG"))

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


class LaneletInformationToolbox(QWidget):

    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.setLayout(layout)
        self.laneletID = QLineEdit()
        self.laneletID.setReadOnly(True)
        self.laneletID.setValidator(QIntValidator())
        self.laneletID.setAlignment(Qt.AlignRight)

        self.length = QLineEdit()
        self.length.setValidator(QIntValidator())
        self.length.setMaxLength(4)
        self.length.setAlignment(Qt.AlignRight)

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.number_vertices = QLineEdit()
        self.number_vertices.setValidator(QIntValidator())
        self.number_vertices.setMaxLength(2)
        self.number_vertices.setAlignment(Qt.AlignRight)

        self.radius = QLineEdit()
        self.radius.setValidator(QIntValidator())
        self.radius.setMaxLength(4)
        self.radius.setAlignment(Qt.AlignRight)

        self.angle = QLineEdit()
        self.angle.setValidator(QIntValidator())
        self.angle.setMaxLength(4)
        self.angle.setAlignment(Qt.AlignRight)

        self.roaduser_oneway = CheckableComboBox()
        self.roaduser_oneway_list = [r.value for r in RoadUser]
        for i in range(0, len(self.roaduser_oneway_list) - 1):
            self.roaduser_oneway.addItem(self.roaduser_oneway_list[i])
            item = self.roaduser_oneway.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.roaduser_bidirectional = CheckableComboBox()
        self.roaduser_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0, len(self.roaduser_bidirectional_list) - 1):
            self.roaduser_bidirectional.addItem(self.roaduser_bidirectional_list[i])
            item = self.roaduser_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.type = CheckableComboBox()
        self.enumlist = [e.value for e in LaneletType]
        for i in range(0, len(self.enumlist) - 1):
            # adding item
            self.type.addItem(self.enumlist[i])
            item = self.type.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.traffic_sign_ids = QLineEdit()
        self.traffic_sign_ids.setAlignment(Qt.AlignRight)

        self.traffic_light_ids = QLineEdit()
        self.traffic_light_ids.setAlignment(Qt.AlignRight)

        self.refresh_button = QPushButton()
        self.refresh_button.setText("refresh")
        self.edit_button = QPushButton()
        self.edit_button.setText("edit")


        layout.addRow("Lanelet ID", self.laneletID)
        layout.addRow("Lanelet width", self.width)
        layout.addRow("Lanelet length", self.length)
        layout.addRow("Number Vertices", self.number_vertices)
        layout.addRow("Curve radius", self.radius)
        layout.addRow("Curve angle", self.angle)
        layout.addRow("Type", self.type)
        layout.addRow("Roaduser oneway", self.roaduser_oneway)
        layout.addRow("Roaduser bidirectional", self.roaduser_bidirectional)
        layout.addRow("Traffic Sign Ids", self.traffic_sign_ids)
        layout.addRow("Traffic Light Ids", self.traffic_light_ids)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.edit_button)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UpperToolbox()
    window.show()
    sumo = SumoTool()
    sumo.show()
    sys.exit(app.exec_())


class CheckableComboBox(QComboBox):
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QStandardItemModel(self))

        # when any item get pressed

    def handle_item_pressed(self, index):

        # getting which item is pressed
        item = self.model().itemFromIndex(index)

        # make it check if unchecked and vice-versa
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

            # calling method
        self.check_items()

        # method called by check_items

    def item_checked(self, index):

        # getting item at index
        item = self.model().item(index, 0)

        # return true if checked else false
        return item.checkState() == Qt.Checked



    def get_checked_items(self):
        # blank list
        checkedItems = []

        # traversing the items
        for i in range(self.count()):

            # if item is checked add it to the list
            if self.item_checked(i):
                checkedItems.append(i)

        return checkedItems

    def check_items(self):
        # blank list
        checkedItems = []

        # traversing the items
        for i in range(self.count()):

            # if item is checked add it to the list
            if self.item_checked(i):
                checkedItems.append(i)

                # call this method
        self.update_labels(checkedItems)

        # method to update the label

    def update_labels(self, item_list):

        n = ''
        count = 0

        # traversing the list
        for i in item_list:

            # if count value is 0 don't add comma
            if count == 0:
                n += ' % s' % i
                # else value is greater then 0
            # add comma
            else:
                n += ', % s' % i

                # increment count
            count += 1


