from typing import List, Union

from commonroad.common.util import Interval
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
)

from crdesigner.common.config.config_base import Attribute
from crdesigner.ui.gui.utilities.size_policy import (
    create_size_policy_for_settings_elements,
)


def _extract_interval(interval: str) -> Interval:
    try:
        split = interval.split(",")
        return Interval(float(split[0].strip()), float(split[1].strip()))
    except Exception:
        return Interval(0, 0)


def _extract_list(str_list: str) -> List:
    ret = []
    try:
        ret = [int(e.strip()) for e in str_list.split(",")]
    except Exception:
        pass

    try:
        ret = [float(e.strip()) for e in str_list.split(",")]
    except Exception:
        pass

    try:
        ret = [e.strip() for e in str_list.split(",")]
    except Exception:
        pass

    return ret


class SettingsTabUI:
    """
    Class for creating the settings tabs based of the Attributes and their layout.
    """

    def __init__(
        self,
        layout: List[List[Union[Attribute, str]]],
        settings_ui,
        factor: float,
        widthf: int,
        widthm: int,
        height: int,
        font_size: int,
    ):
        """Initialize the settings tab."""
        self.factor = factor
        self.widthf = int(widthf * factor)
        self.widthm = int(widthm * factor)
        self.height = int(height)
        self.font_size = font_size

        self.scrollArea = QtWidgets.QScrollArea(settings_ui.tabWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaLayout = QtWidgets.QGridLayout(self.scrollArea)

        # single content widget for adding to the scrollArea
        # otherwise scrolling is disabled
        self.contentWrapper = QtWidgets.QWidget()
        self.contentWrapper.setObjectName("ContentWrapper")
        self.HBoxLayout = QtWidgets.QHBoxLayout(self.contentWrapper)
        self.HBoxLayout.setObjectName("gridLayout")
        self.HBoxLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.HBoxLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        # creating columns
        self.content = []
        self.formLayout = []
        for i in range(len(layout)):
            self.content.append(QtWidgets.QWidget(self.contentWrapper))
            self.content[i].setObjectName("scrollAreaWidgetContents_" + str(i))
            self.formLayout.append(QtWidgets.QFormLayout(self.content[i]))
            self.formLayout[i].setObjectName("form_" + str(i))
            self.content[i].setMinimumSize(int(860 * factor), 820)
            self.content[i].setLayout(self.formLayout[i])
            self.HBoxLayout.addWidget(self.content[i])

        for column, attributes in enumerate(layout):
            for attribute in attributes:
                if isinstance(attribute, str):
                    self._add_label(attribute, column, attributes.index(attribute) != 0)
                else:
                    if attribute.value_type is bool:
                        self._add_checkbox(attribute, column)
                    elif attribute.value_type is int:
                        self._add_int_spinbox(attribute, column)
                    elif attribute.value_type is float:
                        self._add_float_spinbox(attribute, column)
                    elif attribute.value_type is str:
                        if attribute.options is not None:
                            self._add_str_dropdown(attribute, column)
                        else:
                            self._add_str_textbox(attribute, column)
                    elif attribute.value_type is dict:
                        self._add_sub_window(attribute, column)
                    elif attribute.value_type is Interval:
                        self._add_interval_str(attribute, column)
                    elif attribute.value_type is list:
                        self._add_list_str(attribute, column)

        self.scrollArea.setWidget(self.contentWrapper)

    def _add_label(self, name: str, column: int, spacer: bool = True):
        if spacer:
            self.formLayout[column].addRow(QtWidgets.QLabel(self.content[column]))

        label = QtWidgets.QLabel(self.content[column])
        label.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Weight.Bold))
        label.setObjectName("label_" + name)
        label.setText(name)
        self.formLayout[column].addRow(label)

    def _add_checkbox(self, attribute: Attribute, column: int):
        # Create the layout
        hbox, label = self._create_hbox_label(attribute, column)

        # Create the checkbox
        checkbox = QtWidgets.QCheckBox(self.content[column])
        checkbox.setObjectName(f"chk_{attribute.display_name}")
        checkbox.setMinimumSize(self.widthm, self.height)
        checkbox.setChecked(attribute.value)

        # Connect the checkbox to the attribute
        checkbox.stateChanged.connect(
            lambda value: attribute.set_value(value == QtCore.Qt.CheckState.Checked.value)
        )
        attribute.subscribe(lambda value: checkbox.setChecked(value))

        # Add label and checkbox to the layout
        self._insert_in_hbox(attribute, column, hbox, label, checkbox)

    def _add_int_spinbox(self, attribute: Attribute, column: int):
        self._add_spinbox(attribute, column, QtWidgets.QSpinBox(self.content[column]))

    def _add_float_spinbox(self, attribute: Attribute, column: int):
        self._add_spinbox(attribute, column, QtWidgets.QDoubleSpinBox(self.content[column]))

    def _add_spinbox(self, attribute: Attribute, column: int, spinbox):
        # Create the layout
        hbox, label = self._create_hbox_label(attribute, column)

        # Fill the spinbox for the value
        spinbox.setSuffix("")
        spinbox.setPrefix("")
        if attribute.options is not None and type(attribute.options) is tuple:
            spinbox.setMinimum(attribute.options[0])
            spinbox.setMaximum(attribute.options[1])
        spinbox.setProperty("value", attribute.value)
        spinbox.setObjectName(f"sb_{attribute.display_name}")
        spinbox.setMinimumSize(self.widthm, self.height)

        # Connect the spinbox to the attribute
        spinbox.valueChanged.connect(lambda value: attribute.set_value(value))
        attribute.subscribe(lambda value: spinbox.setValue(value))

        # Add label and spinbox to the layout
        self._insert_in_hbox(attribute, column, hbox, label, spinbox)

    def _add_str_dropdown(self, attribute: Attribute, column: int):
        # Create the layout
        hbox, label = self._create_hbox_label(attribute, column)

        # Create the dropdown for the value
        dropdown = QtWidgets.QComboBox(self.content[column])
        dropdown.setObjectName(f"dd_{attribute.display_name}")
        for option in attribute.options:
            dropdown.addItem(option)
        dropdown.setCurrentIndex(attribute.options.index(attribute.value))
        dropdown.setMinimumSize(self.widthm, self.height)
        dropdown.setSizePolicy(create_size_policy_for_settings_elements())

        # Connect the dropdown to the attribute
        dropdown.currentIndexChanged.connect(
            lambda value: attribute.set_value(attribute.options[value])
        )
        attribute.subscribe(
            lambda value: dropdown.setCurrentIndex(attribute.options.index(attribute.value))
        )

        # Add label and dropdown to the layout
        self._insert_in_hbox(attribute, column, hbox, label, dropdown)

    def _add_interval_str(self, attribute: Attribute[Interval], column: int):
        # Create the layout
        hbox, label = self._create_hbox_label(attribute, column)

        # Create the textbox for the value
        textbox = QtWidgets.QLineEdit(self.content[column])
        textbox.setObjectName(f"tb_{attribute.display_name}")
        textbox.setText(str(attribute.value.start) + "," + str(attribute.value.end))
        textbox.setMinimumSize(self.widthm, self.height)
        textbox.setSizePolicy(create_size_policy_for_settings_elements())

        # Connect the textbox to the attribute
        textbox.textChanged.connect(lambda value: attribute.set_value(_extract_interval(value)))
        attribute.subscribe(lambda value: textbox.setText(str(value.start) + "," + str(value.end)))

        # Add label and textbox to the layout
        self._insert_in_hbox(attribute, column, hbox, label, textbox)

    def _add_list_str(self, attribute: Attribute[list], column: int):
        # Create the layout
        hbox, label = self._create_hbox_label(attribute, column)

        # Create the textbox for the value
        textbox = QTextEdit(self.content[column])
        textbox.setObjectName(f"tb_{attribute.display_name}")
        textbox.setText(", ".join([str(e) for e in attribute.value]))
        textbox.setSizePolicy(create_size_policy_for_settings_elements())

        # Limit the textbox to two lines
        textbox.setFixedHeight(self.font_size * 2 * 5 + 20)

        # Set the width of the QTextEdit to match QLineEdit
        textbox.setMinimumWidth(self.widthm)  # adjust the value as per your requirement

        # Connect the textbox to the attribute
        textbox.textChanged.connect(
            lambda: attribute.set_value(_extract_list(textbox.toPlainText()))
        )
        attribute.subscribe(lambda value: textbox.setText(",".join([str(e) for e in value])))

        # Add label and textbox to the layout
        self._insert_in_hbox(attribute, column, hbox, label, textbox)

    def _add_str_textbox(self, attribute: Attribute, column: int):
        # Create the layout
        hbox, label = self._create_hbox_label(attribute, column)

        # Create the textbox for the value
        textbox = QtWidgets.QLineEdit(self.content[column])
        textbox.setObjectName(f"tb_{attribute.display_name}")
        textbox.setText(attribute.value)
        textbox.setMinimumSize(self.widthm, self.height)
        textbox.setSizePolicy(create_size_policy_for_settings_elements())

        # Connect the textbox to the attribute
        textbox.textChanged.connect(lambda value: attribute.set_value(value))
        attribute.subscribe(lambda value: textbox.setText(value))

        # Add label and textbox to the layout
        self._insert_in_hbox(attribute, column, hbox, label, textbox)

    def _create_hbox_label(self, attribute: Attribute, column: int):
        # Create the layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.setObjectName(f"hbox_{attribute.display_name}")

        # Create the label
        label = QtWidgets.QLabel(self.content[column])
        label.setObjectName(f"label_{attribute.display_name}")
        label.setMinimumSize(self.widthf, self.height)
        label.setText(attribute.display_name)
        label.setToolTip(attribute.description)

        return hbox, label

    def _insert_in_hbox(
        self,
        attribute: Attribute,
        column: int,
        hbox: QtWidgets.QHBoxLayout,
        label: QtWidgets.QLabel,
        widget: QtWidgets.QWidget,
    ):
        # Add label and textbox to the layout
        hbox.addWidget(label)
        hbox.addWidget(widget)

        # Add optional unit or empty label
        unit = QtWidgets.QLabel(self.content[column])
        unit.setObjectName(f"label_{attribute.display_name}_unit")
        if attribute.unit is not None:
            unit.setText(attribute.unit)
        else:
            unit.setText("d/m")
        hbox.addWidget(unit)

        # Add the layout to the form
        self.formLayout[column].addRow(hbox)

    def _add_sub_window(self, attribute, column):
        # Create the layout
        hbox, label = self._create_hbox_label(attribute, column)
        dialog = self._create_dialog(attribute)

        # Create button
        button = QtWidgets.QPushButton(self.content[column])
        button.setObjectName(f"btn_{attribute.display_name}")
        button.setText(attribute.display_name)
        button.setMinimumSize(self.widthf, self.height)
        button.setSizePolicy(create_size_policy_for_settings_elements())

        # Connect the button to dialog
        button.clicked.connect(lambda: dialog.exec())

        # Add label and button to the layout
        self._insert_in_hbox(attribute, column, hbox, label, button)

    def _create_dialog(self, attribute: Attribute[dict]) -> QDialog:
        # Create the dialog
        dialog = QDialog()
        dialog.setObjectName(f"dlg_{attribute.display_name}")
        dialog.resize(400, 200)

        # Define a stylesheet with the desired font size and apply it to the settings window
        stylesheet = "QWidget { font-size: %dpt; }" % self.font_size
        dialog.setStyleSheet(stylesheet)

        # Create the layout
        layout = QFormLayout(dialog)
        dialog.setLayout(layout)

        # Add the attributes to the dialog
        for name, value in attribute.value.items():
            label = QLabel(dialog)
            label.setObjectName(f"label_{name}")
            label.setText(name if isinstance(name, str) else name.name)

            if isinstance(value, bool):
                input_widget = QCheckBox(dialog)
                input_widget.setChecked(value)
                input_widget.stateChanged.connect(
                    lambda _state, _name=name: attribute.value.update(
                        {_name: _state == QtCore.Qt.CheckState.Checked.value}
                    )
                )
                attribute.subscribe(
                    lambda _value, _name=name, _iw=input_widget: _iw.setChecked(_value[_name])
                )

            elif isinstance(value, int):
                input_widget = QSpinBox(dialog)
                input_widget.setValue(value)
                input_widget.valueChanged.connect(
                    lambda _value, _name=name: attribute.value.update({_name: _value})
                )
                attribute.subscribe(
                    lambda _value, _name=name, _iw=input_widget: _iw.setValue(_value[_name])
                )

            elif isinstance(value, float):
                input_widget = QDoubleSpinBox(dialog)
                input_widget.setValue(value)
                input_widget.valueChanged.connect(
                    lambda _value, _name=name: attribute.value.update({_name: _value})
                )
                attribute.subscribe(
                    lambda _value, _name=name, _iw=input_widget: _iw.setValue(_value[_name])
                )

            elif isinstance(value, str):
                input_widget = QLineEdit(dialog)
                input_widget.setText(value)
                input_widget.textChanged.connect(
                    lambda _value, _name=name: attribute.value.update({_name: _value})
                )
                attribute.subscribe(
                    lambda _value, _name=name, _iw=input_widget: _iw.setText(_value[_name])
                )

            else:
                continue

            layout.addRow(label, input_widget)

        # Create button box
        button_box = QtWidgets.QDialogButtonBox(QtCore.Qt.Orientation.Horizontal)
        button_box.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        button_box.setObjectName("button_box")

        # Connect button box to dialog
        button_box.accepted.connect(dialog.hide)
        button_box.rejected.connect(lambda: (dialog.hide(), attribute.reset()))

        # Add button box to layout
        layout.addRow(button_box)

        return dialog
