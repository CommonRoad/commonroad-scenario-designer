from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

"""
This file is a general collection of smaller functions which are used in the mwindow
or by two or more components from the service_layer.
"""


def create_action(mwindow, text, icon=None, checkable=False, slot=None, tip=None, shortcut=None):
    """
    Generic function used to create actions for the settings or the menu bar.
    """
    action = QAction(text, mwindow)
    if icon is not None:
        action.setIcon(QIcon(icon))
    if checkable:
        # toggle, True means on/off state, False means simply executed
        action.setCheckable(True)
        if slot is not None:
            action.toggled.connect(slot)
    else:
        if slot is not None:
            action.triggered.connect(slot)
    if tip is not None:
        action.setToolTip(tip)  # toolbar_wrapper tip
        action.setStatusTip(tip)  # statusbar tip
    if shortcut is not None:
        action.setShortcut(shortcut)  # shortcut
    return action
