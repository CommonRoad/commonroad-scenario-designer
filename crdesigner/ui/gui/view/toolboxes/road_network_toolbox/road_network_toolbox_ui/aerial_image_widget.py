from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtGui import QDoubleValidator, QFont
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from crdesigner.ui.gui.utilities.waitingspinnerwidget import QtWaitingSpinner


class AerialImageWidget:
    """
    Inherits the Aerial Image widget setup
    """

    def __init__(self, toolbox):
        self.toolbox = toolbox

    def create_aerial_image_widget(self):
        """
        create the Add aerial image widget
        """
        widget_aerial = QFrame(self.toolbox.tree)
        layout_aerial_image = QVBoxLayout(widget_aerial)
        label_general = QLabel("Aerial map Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        # GroupBox
        self.toolbox.aerial_image_groupbox = QGroupBox()
        self.toolbox.layout_aerial_image_groupbox = QFormLayout()
        self.toolbox.aerial_image_groupbox.setLayout(self.toolbox.layout_aerial_image_groupbox)
        self.toolbox.layout_aerial_image_groupbox.addRow(label_general)

        # Add button
        self.toolbox.button_add_aerial_image = QPushButton("Add")
        # Remove button
        self.toolbox.button_remove_aerial_image = QPushButton("Remove")

        connecting_radio_button_group_aerial = QButtonGroup()
        self.toolbox.bing_selection = QRadioButton("Bing maps")
        self.toolbox.bing_selection.setChecked(True)
        connecting_radio_button_group_aerial.addButton(self.toolbox.bing_selection)

        self.toolbox.ldbv_selection = QRadioButton("LDBV maps")
        connecting_radio_button_group_aerial.addButton(self.toolbox.ldbv_selection)

        self.toolbox.aerial_selection = QGridLayout()
        self.toolbox.aerial_selection.addWidget(self.toolbox.bing_selection, 1, 0)
        self.toolbox.aerial_selection.addWidget(self.toolbox.ldbv_selection, 1, 1)

        self.toolbox.layout_aerial_image_groupbox.addRow(self.toolbox.aerial_selection)

        validator_latitude = QDoubleValidator(-90.0, 90.0, 1000)
        validator_latitude.setLocale(QLocale("en_US"))
        validator_longitude = QDoubleValidator(-180.0, 180.0, 1000)
        validator_longitude.setLocale(QLocale("en_US"))

        # lat1
        self.toolbox.northern_bound = QLineEdit()
        self.toolbox.northern_bound.setValidator(validator_latitude)
        self.toolbox.northern_bound.setMaxLength(8)
        self.toolbox.northern_bound.setAlignment(Qt.AlignmentFlag.AlignRight)
        # lon1
        self.toolbox.western_bound = QLineEdit()
        self.toolbox.western_bound.setValidator(validator_longitude)
        self.toolbox.western_bound.setMaxLength(8)
        self.toolbox.western_bound.setAlignment(Qt.AlignmentFlag.AlignRight)
        # lat2
        self.toolbox.southern_bound = QLineEdit()
        self.toolbox.southern_bound.setValidator(validator_latitude)
        self.toolbox.southern_bound.setMaxLength(8)
        self.toolbox.southern_bound.setAlignment(Qt.AlignmentFlag.AlignRight)
        # lon2
        self.toolbox.eastern_bound = QLineEdit()
        self.toolbox.eastern_bound.setValidator(validator_longitude)
        self.toolbox.eastern_bound.setMaxLength(8)
        self.toolbox.eastern_bound.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.layout_aerial_image_groupbox.insertRow(
            3, "Northern Bound [°]", self.toolbox.northern_bound
        )
        self.toolbox.layout_aerial_image_groupbox.insertRow(
            4, "Western Bound [°]", self.toolbox.western_bound
        )
        self.toolbox.layout_aerial_image_groupbox.insertRow(
            5, "Southern Bound [°]", self.toolbox.southern_bound
        )
        self.toolbox.layout_aerial_image_groupbox.insertRow(
            6, "Eastern Bound [°]", self.toolbox.eastern_bound
        )

        # probably move the next 4 lines to init_aerial_widget or something
        self.toolbox.northern_bound.setText("48.263864")
        self.toolbox.western_bound.setText("11.655410")
        self.toolbox.southern_bound.setText("48.261424")
        self.toolbox.eastern_bound.setText("11.660930")

        self.toolbox.current_position = QPushButton("Select current Position")
        self.toolbox.layout_aerial_image_groupbox.addRow(self.toolbox.current_position)

        self.toolbox.Spinner = QtWaitingSpinner(self.toolbox, centerOnParent=True)
        self.toolbox.Spinner.setInnerRadius(7)
        self.toolbox.Spinner.setNumberOfLines(10)
        self.toolbox.Spinner.setLineLength(7)
        self.toolbox.Spinner.setLineWidth(2)

        self.toolbox.layout_aerial_image_groupbox.addRow(self.toolbox.button_add_aerial_image)
        self.toolbox.layout_aerial_image_groupbox.addRow(self.toolbox.button_remove_aerial_image)

        layout_aerial_image.addWidget(self.toolbox.aerial_image_groupbox)

        widget_title = "Add Aerial Image"
        return widget_title, widget_aerial
