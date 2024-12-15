from PyQt6 import QtGui
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QPushButton,
    QRadioButton,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from crdesigner.common.config.gui_config import gui_config as config


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class SectionExpandButton(QPushButton):
    """a QPushbutton that can expand or collapse its section"""

    def __init__(self, item, text="", parent=None, mwindow=None):
        super().__init__(text, parent)
        self.mwindow = mwindow
        self.section = item
        self.section.setExpanded(False)
        self.clicked.connect(self.on_clicked)
        self.update_window()

    def update_window(self):
        self.setStyleSheet(
            "background-color:"
            + self.mwindow.mwindow_ui.colorscheme().highlight
            + "; color:"
            + self.mwindow.mwindow_ui.colorscheme().highlight_text
            + "; font-size:"
            + self.mwindow.mwindow_ui.colorscheme().font_size
        )

    def on_clicked(self):
        """toggle expand/collapse of section by clicking"""
        if self.section.isExpanded():
            self.mwindow.road_network_toolbox.disable_show_of_curved_lanelet()
            self.section.setExpanded(False)
        else:
            self.mwindow.road_network_toolbox.disable_show_of_curved_lanelet(self.text())
            self.section.setExpanded(True)


class CheckableComboBox(QComboBox):
    def __init__(self, mwindow=None, pred_suc=False):
        super(CheckableComboBox, self).__init__()
        self.mwindow = mwindow
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QStandardItemModel(self))
        # self.update_window()

    def handle_item_pressed(self, index):
        # getting which item is pressed
        item = self.model().itemFromIndex(index)

        # make it check if unchecked and vice-versa
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

        self.check_items()

    def item_checked(self, index):
        # getting item at index
        item = self.model().item(index, 0)

        # return true if checked else false
        return item.checkState() == Qt.CheckState.Checked

    def get_checked_items(self):
        # blank list
        checked_items = []

        # traversing the items
        for i in range(self.count()):
            # if item is checked add it to the list
            if self.item_checked(i):
                checked_items.append(self.itemText(i))

        return checked_items

    def get_items(self):
        # blank list
        items = []

        # traversing the items
        for i in range(self.count()):
            items.append(self.itemText(i))

        return items

    def set_checked_items(self, checked_items):
        for index in range(self.count()):
            item = self.model().item(index, 0)
            if item.text() in checked_items:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

    def uncheck_items(self, uncheck_item):
        """
        Unchecks item from list
        """
        for index in range(self.count()):
            item = self.model().item(index, 0)
            if item.text() in uncheck_item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def check_items(self):
        # blank list
        checked_items = []

        # traversing the items
        for i in range(self.count()):
            # if item is checked add it to the list
            if self.item_checked(i):
                checked_items.append(i)

                # call this method
        CheckableComboBox.update_labels(checked_items)

    @staticmethod
    def update_labels(item_list):
        # method to update the label
        n = ""
        count = 0

        # traversing the list
        for i in item_list:
            # if count value is 0 don't add comma
            if count == 0:
                n += " % s" % i  # else value is greater then 0
            # add comma
            else:
                n += ", % s" % i

                # increment count
            count += 1

    def update_window(self):
        if self.mwindow:
            p = QtGui.QPalette()
            p.setColor(
                QtGui.QPalette.ColorRole.Window,
                QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().background),
            )
            p.setColor(
                QtGui.QPalette.ColorRole.Base,
                QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().color),
            )
            p.setColor(
                QtGui.QPalette.ColorRole.Button,
                QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().background),
            )
            p.setColor(
                QtGui.QPalette.ColorRole.ButtonText,
                QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().color),
            )
            p.setColor(
                QtGui.QPalette.ColorRole.Text,
                QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().color),
            )
            p.setColor(
                QtGui.QPalette.ColorRole.WindowText,
                QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().color),
            )
            p.setColor(
                QtGui.QPalette.ColorRole.AlternateBase,
                QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().background),
            )
            self.setPalette(p)


class CollapsibleCheckBox(QCheckBox):
    """CollapsibleCheckBox which can hide or show its content (which is inside the layout)"""

    def __init__(self, title, layout, adding_to_layout, index, parent=None):
        super().__init__(parent)
        self.button = QCheckBox(title)
        self.button.clicked.connect(lambda: self.button_clicked())

        self.box = QGroupBox()
        self.layout = layout
        self.box.setLayout(self.layout)

        self.box.setMaximumSize(0, 0)
        adding_to_layout.insertRow(index, self.button)
        adding_to_layout.insertRow(index + 1, self.box)
        self.adding_to_layout = adding_to_layout

    def button_clicked(self):
        if self.button.isChecked():
            self.box.setMaximumSize(1000, 1000)
        else:
            self.box.setMaximumSize(0, 0)

    def remove(self):
        self.adding_to_layout.removeRow(self.button)
        self.adding_to_layout.removeRow(self.box)

    def isChecked(self):
        return self.button.isChecked()

    def setChecked(self, bool):
        self.button.setChecked(bool)
        if bool:
            self.box.setMaximumSize(1000, 1000)
        else:
            self.box.setMaximumSize(0, 0)


class CollapsibleButtonBox(QRadioButton):
    """
    CollapsibleButtonBox which can hide or show its content (which is inside the layout)
    """

    def __init__(self, title, layout, adding_to_layout, index, parent=None):
        super().__init__(parent)
        self.button = QRadioButton(title)
        self.button.setChecked(False)
        self.button.setAutoExclusive(False)
        self.button.clicked.connect(lambda: self.button_clicked())

        self.box = QGroupBox()
        self.layout = layout
        self.box.setLayout(self.layout)

        self.box.setMaximumSize(0, 0)
        adding_to_layout.insertRow(index, self.button)
        adding_to_layout.insertRow(index + 1, self.box)
        self.adding_to_layout = adding_to_layout

    def button_clicked(self):
        if self.button.isChecked():
            self.box.setMaximumSize(1000, 1000)
        else:
            self.box.setMaximumSize(0, 0)

    def remove(self):
        self.adding_to_layout.removeRow(self.button)
        self.adding_to_layout.removeRow(self.box)

    def isChecked(self):
        return self.button.isChecked()

    def setChecked(self, bool):
        self.button.setChecked(bool)
        if bool:
            self.box.setMaximumSize(1000, 1000)
        else:
            self.box.setMaximumSize(0, 0)


class CollapsibleArrowBox(QToolButton):
    """
    CollapsibleArrowBox which can hide or show its content (which is inside the layout)
    """

    def __init__(self, title, layout, adding_to_layout, index, mwindow, toolbox, parent=None):
        super().__init__(parent)
        self.button = QToolButton()
        self.button.setText(title)
        self.mwindow = mwindow

        self.button = QToolButton()
        toolbox.arrowButtons.append(self.button)
        self.toolbox = toolbox
        self.button.setStyleSheet(
            "QToolButton {border: none; color: "
            + self.mwindow.mwindow_ui.colorscheme().color
            + ";}"
        )
        self.button.setText(title)
        self.button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.button.setArrowType(Qt.ArrowType.RightArrow)

        self.toggle_checked = False
        self.button.clicked.connect(lambda: self.pressed())

        self.box = QGroupBox()
        self.layout = layout
        self.box.setLayout(self.layout)

        self.box.setMaximumSize(0, 0)

        adding_to_layout.insertRow(index, self.button)
        adding_to_layout.insertRow(index + 1, self.box)
        self.adding_to_layout = adding_to_layout

    def pressed(self):
        if not self.toggle_checked:
            self.box.setMaximumSize(1000, 1000)
            self.button.setArrowType(Qt.ArrowType.DownArrow)
            self.toggle_checked = True
        else:
            self.box.setMaximumSize(0, 0)
            self.button.setArrowType(Qt.ArrowType.RightArrow)
            self.toggle_checked = False

    def remove(self):
        self.adding_to_layout.removeRow(self.button)
        self.adding_to_layout.removeRow(self.box)
        if self.button in self.toolbox.arrowButtons:
            self.toolbox.arrowButtons.remove(self.button)


class PosB:
    """PosB is used for connecting PositionButton with functionallity of retrieving the coordinates.
    It saves the x and y position of the last position of the mouse pressed event"""

    def __init__(self, x_position, y_position, parent=None):
        self.x_position = x_position
        self.y_position = y_position


class PositionButton(QPushButton):
    """PositionButton is used to select a position on the canvas and insert it in the
    x_position and y_position QLineEdit"""

    def __init__(self, x_position, y_position, toolbox, parent=None):
        super().__init__("", parent)
        self.setIcon(QIcon(":/icons/target.png"))
        self.setIconSize(QSize(25, 25))
        self.setFlat(True)
        self.setAutoFillBackground(True)

        toolbox.position_buttons.append(self)
        self.setToolTip("Click button and afterwards on canvas to select position")

        self.toolbox = toolbox
        self.x_position = x_position
        self.y_position = y_position
        self.clicked.connect(self.button_press)
        self.button_pressed = False
        self.update_window()

    def button_press(self):
        if self.button_pressed:
            self.button_release()
            return

        self.button_pressed = True
        self.setFlat(False)
        self.update_window()

    def button_release(self):
        self.button_pressed = False
        self.setFlat(True)
        self.update_window()

    def update_window(self):
        if self.button_pressed:
            self.setStyleSheet(
                "color: "
                + self.toolbox.mwindow.mwindow_ui.colorscheme().highlight_text
                + "; background-color: "
                + self.toolbox.mwindow.mwindow_ui.colorscheme().highlight
            )
            self.setIcon(QIcon(":/icons/target.png"))
        else:
            self.setStyleSheet(
                "color: "
                + self.toolbox.mwindow.mwindow_ui.colorscheme().highlight
                + "; background-color: "
                + self.toolbox.mwindow.mwindow_ui.colorscheme().second_background
            )
            if config.DARKMODE:
                self.setIcon(QIcon(":/icons/target-darkmode.png"))
            else:
                self.setIcon(QIcon(":/icons/target.png"))

    def remove(self):
        self.toolbox.position_buttons.remove(self)


class Toolbox(QWidget):
    """a dialog to which collapsible sections can be added;
    reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
    """

    def __init__(self, mwindow):
        super().__init__()
        self.sectionExpandButton = []
        self.mwindow = mwindow
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.tree.setIndentation(0)
        self.setGeometry(0, 0, 250, 500)
        self.arrowButtons = []
        self.position_buttons = []

        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tree.verticalScrollBar().setSingleStep(30)

        self.sections = []
        self.define_sections()
        self.add_sections()

    def add_sections(self):
        """adds a collapsible sections for every
        (title, widget) tuple in self.sections
        """
        for title, widget in self.sections:
            button1 = self.add_button(title)
            section1 = self.add_widget(button1, widget)
            button1.addChild(section1)

    def selection_change(self):
        self.lb.setText(self.save_menu.currentText())

    def add_button(self, title):
        """creates a QTreeWidgetItem containing a button
        to expand or collapse its section
        """
        item = QTreeWidgetItem()
        self.tree.addTopLevelItem(item)
        self.sectionExpandButton.append(SectionExpandButton(item, text=title, mwindow=self.mwindow))
        self.tree.setItemWidget(item, 0, self.sectionExpandButton[-1])
        return item

    def add_widget(self, button, widget):
        """creates a QWidgetItem containing the widget,
        as child of the button-QWidgetItem
        """
        section = QTreeWidgetItem(button)
        section.setDisabled(True)
        self.tree.setItemWidget(section, 0, widget)
        return section

    def update_window(self):
        for i in self.sectionExpandButton:
            i.update_window()
        for i in self.position_buttons:
            i.update_window()
        for i in self.arrowButtons:
            i.setStyleSheet(
                "QToolButton {border: none; color: "
                + self.mwindow.mwindow_ui.colorscheme().color
                + ";}"
            )

        p = QtGui.QPalette()
        p.setColor(
            QtGui.QPalette.ColorRole.Window,
            QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().second_background),
        )
        p.setColor(
            QtGui.QPalette.ColorRole.Base,
            QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().second_background),
        )
        p.setColor(
            QtGui.QPalette.ColorRole.Button,
            QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().background),
        )
        p.setColor(
            QtGui.QPalette.ColorRole.ButtonText,
            QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().color),
        )
        p.setColor(
            QtGui.QPalette.ColorRole.Text, QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().color)
        )
        p.setColor(
            QtGui.QPalette.ColorRole.WindowText,
            QtGui.QColor(self.mwindow.mwindow_ui.colorscheme().color),
        )
        self.setPalette(p)
