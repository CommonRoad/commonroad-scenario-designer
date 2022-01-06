import unittest
import pytest
import time

from crdesigner.ui.gui.mwindow.mwindow import MWindow
import sys
from PyQt5.QtWidgets import *


def test_app(qtbot):
    window = MWindow()
    qtbot.addWidget(window)
    # window.showMaximized()
    window.top_bar_wrapper.toolbar_wrapper.action_new.trigger()
    window.close()
    print("Ready")
    #qtbot.mouseClick(window.top_bar_wrapper.toolbar_wrapper.action_new)

