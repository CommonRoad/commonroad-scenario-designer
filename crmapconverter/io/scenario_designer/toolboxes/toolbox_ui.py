from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


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


class CheckableComboBox(QComboBox):
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QStandardItemModel(self))

    def handle_item_pressed(self, index):

        # getting which item is pressed
        item = self.model().itemFromIndex(index)

        # make it check if unchecked and vice-versa
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

        self.check_items()

    def item_checked(self, index):
        # getting item at index
        item = self.model().item(index, 0)

        # return true if checked else false
        return item.checkState() == Qt.Checked

    def get_checked_items(self):
        # blank list
        checked_items = []

        # traversing the items
        for i in range(self.count()):

            # if item is checked add it to the list
            if self.item_checked(i):
                checked_items.append(self.itemText(i))

        return checked_items

    def set_checked_items(self, checked_items):
        for index in range(self.count()):
            item = self.model().item(index, 0)
            if item.text() in checked_items:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

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


class Toolbox(QWidget):
    """a dialog to which collapsible sections can be added;
    reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
        """

    def __init__(self):
        super().__init__()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.tree.setIndentation(0)
        self.setGeometry(0, 0, 250, 500)
        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

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
