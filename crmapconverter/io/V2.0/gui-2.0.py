import os
import signal
import sys
import time

from PyQt5 import QtGui, QtCore, QtWidgets

try:
    from PyQt5.QtWidgets import QFileDialog, QWidget, QApplication, QMainWindow
    # crmapconverter/osm2cr/converter_modulesgui_modulesgui_embedding.py
    from crmapconverter.osm2cr.converter_modules.gui_modules.gui_embedding import StartMenu, MainApp
except:
    print("You need manually to install your Qt distribution")
try:
    import crmapconverter.io.gui as G
    from commonroad.common.file_writer import CommonRoadFileWriter
    from commonroad.common.file_reader import CommonRoadFileReader

    from crmapconverter.osm.osm2lanelet import OSM2LConverter
    from crmapconverter.osm.parser import OSMParser
    from crmapconverter.osm.lanelet2osm import L2OSMConverter

    from crmapconverter.opendriveparser.parser import parse_opendrive
    from crmapconverter.opendriveconversion.network import Network
    from crmapconverter.io.viewer import MainWindow as ViewerWidget
    import crmapconverter.io.viewer as CRViewerQT
except:
    print("You need to install manually commonroad")

from tkinter import *

from PIL import Image
from PIL import ImageTk


try:
    from crmapconverter.osm2cr.main import start_gui
except ModuleNotFoundError as module_err:
    print(module_err)
    print("It seems like you did not install the dependencies for osm2cr.")
except:
    print("You need to install manually commonroad")

#GLOBAL VARIABLES
high = 902
width = 960

#GLOBAL FUNCTIONS
def image_encoding(path):
    """Loads an image in the right format to inster it in the Tkinter File System"""

    return ImageTk.PhotoImage(Image.open(path))

def osm2cr():
    """Converter OSM2CR intial function (V1.0)"""
    start_gui()

def openDRIVE2Lanelet():
    """Converter OpenDRIVE2Lanelet intial function (V1.0)"""
    G.opendrive_gui()

def default():
    print("coming soon")


class My_Button(Button):
    """Class defining the design of the buttons used in the interface defined below"""

    def __init__(self, parent, row, column, command, icon=None, padx=5, pady=0, **kwargs):
        self.row = row
        self.column = column
        self.command = command
        self.icon = image_encoding("gui_src/" + icon)
        self.padx = padx
        self.pady = pady
        Button.__init__(self, parent, **kwargs)
        self.configure(image=self.icon)
        self.configure(borderwidth=0)
        self.configure(activebackground='#003359')
        self.configure(background='#003359')
        self.configure(cursor='hand2')
        self.configure(command=self.command)
        self.configure(highlightbackground='#003359')
        self.configure(anchor=W)
        self.grid(
            column=self.column,
            row=self.row,
            sticky=W + N,
            padx=self.padx,
            pady=self.pady)

    def set_icon(self, icon):
        self.icon = image_encoding("gui_src/" + icon)
        self.configure(image=self.icon)


class My_Canvas(Canvas):
    """Class defining the design of the canvas used in the interface defined below"""

    def __init__(self, parent, row, pady=0, sticky=None, **kwargs):
        self.row = row
        self.pady = pady
        self.sticky = sticky
        Canvas.__init__(self, parent, **kwargs)
        self.configure(background = '#003359')
        self.configure(highlightbackground = '#003359')
        self.grid(
            row= self.row,
            pady = self.pady,
            sticky= self.sticky)


class My_Title(Label):
    """Class defining the design of the window titles used in the interface defined below"""

    def __init__(self, parent, image, row=1, column=2, pady=0, padx=0, sticky=None, **kwargs):
        self.row = row
        self.column = column
        self.pady = pady
        self.padx = padx
        self.sticky = sticky
        self.image = image_encoding("gui_src/" + image)
        Label.__init__(self, parent, image = self.image, **kwargs)
        self.configure(background = '#003359')
        self.configure(highlightbackground = '#003359')
        self.grid(
            row= self.row,
            column= self.column,
            pady= self.pady,
            padx = self.padx,
            sticky= self.sticky)


class Home(Frame):
    """Class driving the interface of welcoming window"""

    def __init__(self, window, **kwargs):
        Frame.__init__(self, window, bg="#003359", **kwargs)
        self.grid()

        # welcoming text
        self.welcoming_text = My_Title(self,
                                  image="welcoming_text.png",
                                  column=0,
                                  pady=15)

        def osm2cr_new():
            """Function to access the new GUI of OSM2CR Converter"""
            self.destroy()
            OSM2CRActivity1(window).mainloop()

        def openDRIVE2cr_new():
            """Function to access the new GUI of OpenDRIVE2Converter"""
            self.destroy()
            OD2CRActivity1(window).mainloop()

        def CRViewer():
            """Function to access the new GUI of Common Road Visualizer"""
            self.destroy()
            CRViewerActivity1(window).mainloop()


        # First line - Canvas 1
        self.button_canvas_1 = My_Canvas(self, 2)
        self.b1 = My_Button(self.button_canvas_1, 2, 0, osm2cr_new,
                            "Groupe 1.png")
        self.b2 = My_Button(self.button_canvas_1, 2, 1, default,
                            "Groupe 2.png" )
        self.b3 = My_Button(self.button_canvas_1, 2, 2, openDRIVE2cr_new,
                            "Groupe 3.png")

        self.button_canvas_2 = My_Canvas(self, 3, pady=30)
        self.b4 = My_Button(self.button_canvas_2, 3, 0, default,
                            "Groupe 4.png")
        self.b5 = My_Button(self.button_canvas_2, 3, 1, default,
                            "Groupe 5.png")
        self.b6 = My_Button(self.button_canvas_2, 3, 2, CRViewer,
                            "Groupe 6.png")


class InterfaceToolTemplate(Frame):
    """Classe driving the interface of main window inside tools"""

    def __init__(self, window, **kwargs):
        Frame.__init__(self, window, bg="#003359", **kwargs)
        self.grid()

        def go_home():
            self.destroy()
            Home(window).mainloop()

        def go_help():
            try:
                help_window= initialise()
                OSM2CRFrame(help_window).mainloop()
            except TclError:
                print("Error code 15")

        # Buttons Head
        self.Can = My_Canvas(self, 1, sticky=W)

        self.home = My_Button(self.Can, 1, 0, go_home, "/button_home.png")
        self.back = My_Button(self.Can, 1, 1, go_home,
                         "button_back.png",
                         padx=10)
        self.help = My_Button(self.Can, 1, 3, go_help, "button_help.png", padx=30, pady=5)


class OSM2CRFrame(InterfaceToolTemplate):
    """Class driving the frame of OSM2CR Converter"""

    def __init__(self, window, **kwargs):
        InterfaceToolTemplate.__init__(self, window, **kwargs)
        #Head Text
        self.welcoming_text = My_Title(self.Can, "OSM2CR_head.png",
                                 column=2, pady=10, padx=40)


class OSM2CRActivity1(OSM2CRFrame):
    """Class driving the interface of the first Activity of OSM2CR"""

    def __init__(self, window, **kwargs):
        OSM2CRFrame.__init__(self, window, **kwargs)

        #Question
        self.question = My_Title(self, "OSM2CR_question.png", 2, 0, pady=50)

        #Answers
        answers = My_Canvas(self, 3)
        answers_padx = 40
        self.open = My_Button(answers, 0, 0, osm2cr,
                         "button_open.png",
                         padx=answers_padx)
        self.download = My_Button(answers, 0, 1, osm2cr,
                             "button_download.png",
                             padx=answers_padx)


class OD2CRFrame(InterfaceToolTemplate):
    """Class driving the frame of OSM2CR Converter"""

    def __init__(self, window, **kwargs):
        InterfaceToolTemplate.__init__(self, window, **kwargs)
        #Head Text
        self.welcoming_text = My_Title(self.Can, "OD2CR_head.png",
                                 column=2, pady=10, padx=40)


class OD2CRActivity1(OD2CRFrame):
    """Class driving the interface of the first Activity of OSM2CR"""

    def __init__(self, window, **kwargs):
        OD2CRFrame.__init__(self, window, **kwargs)

        #Open OpenDRIVE Map
        self.open_canvas = My_Canvas(self, 2, pady=50)
        self.question = My_Title(self.open_canvas, "OD2CR_question.png", 0, 0)
        self.open = My_Button(self.open_canvas, 0, 1, default,
                         "button_open.png",
                         padx=20)

        class FileOpener(QWidget):

            def __init__(self, parent=None, path=None):
                self.path = None
                super().__init__(parent)

            def open_file_dialog(self):
                print(self.path)
                """"""

                self.path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select OpenDRIVE Map",
                    "",
                    "",
                    options=QFileDialog.Options(),
                )
                print(self.path)

        opener = FileOpener()

        def open_OD():
            opener.open_file_dialog()
            #appi= QtWidgets.QApplication(sys.argv)
            #ex = FileOpener()
            #ex.open_file_dialog()
            #self.open.set_icon("button_done.png")


        self.open.configure(command=open_OD)


class CRViewer(InterfaceToolTemplate):
    """Class driving the frame of OSM2CR Converter"""

    def __init__(self, window, **kwargs):
        InterfaceToolTemplate.__init__(self, window, **kwargs)
        #Head Text
        self.welcoming_text = My_Title(self.Can, "OSM2CR_head.png",
                                 column=2, pady=10, padx=40)


class CRViewerActivity1(OD2CRFrame):
    """Class driving the interface of the first Activity of OSM2CR"""

    def __init__(self, window, **kwargs):
        OD2CRFrame.__init__(self, window, **kwargs)

        class ViewerQt(QWidget):
            """Class used to provied the existant viewer in Qt"""

            def __init__(self):
                super().__init__()

            def commonroad_visualization_menu(self):
                """Open the simple color-supported visualization of a CommonRoad file."""
                viewer = QMainWindow(self)
                commonroad_viewer_widget = ViewerWidget(self)
                viewer.setCentralWidget(commonroad_viewer_widget)
                viewer.show()

        def CRviewer_run():
            app = QtWidgets.QApplication(sys.argv)
            ui = ViewerQt()
            ui.commonroad_visualization_menu()
            app.exec_()

        CRviewer_run()




# INITIALISATION

def initialise():
    window = Tk()
    window.title("Common Road Tools")
    try:
        window.iconbitmap("gui_src/icon.ico")
    except TclError:
        try:
            ico = PhotoImage(file="gui_src/icon.png")
            window.tk.call('wm', 'iconphoto', window._w, ico)
        except:
            print("Impossible to set icon")
    window.geometry(str(width)+'x'+str(high))
    window['bg'] = '#003359'
    window.resizable(False, False)

    # head
    head_src = image_encoding("gui_src/head.png")
    head = Label(window, image=head_src, background='#003359')
    head.image = head_src
    head.grid(row=0)

    return window


app = QApplication(sys.argv)
welcome = initialise()

Home(welcome).mainloop()


#For next time : Traffic signs (light, stop, yeld, priority)
#Visualise a commonroad Map Button on the