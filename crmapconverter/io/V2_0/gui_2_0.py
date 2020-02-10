"""This module controls all the views from the GUI"""

__author__ = "Rayane Zaibet"


import os
import signal
import sys
import time

#Graphic libraries
from PyQt5 import QtGui, QtCore, QtWidgets
try:
    from PyQt5.QtWidgets import QFileDialog, QWidget, QApplication, QMainWindow
except:
    print("You need manually to install your Qt distribution")
from tkinter import *

#Model libraries
try:
    from commonroad.common.file_writer import CommonRoadFileWriter
    from commonroad.common.file_reader import CommonRoadFileReader
except:
    print("You need first to install commonroad")

try:
    from crmapconverter.io.V2_0.gui_2_0_controller import *
    from crmapconverter.io.V2_0.gui_2_0_documentation import *
    import crmapconverter.io.gui as G
    from crmapconverter.osm2cr.converter_modules.gui_modules.gui_embedding import StartMenu, MainApp
    from crmapconverter.osm.osm2lanelet import OSM2LConverter
    from crmapconverter.osm.parser import OSMParser
    from crmapconverter.osm.lanelet2osm import L2OSMConverter
    from crmapconverter.opendriveparser.parser import parse_opendrive
    from crmapconverter.opendriveconversion.network import Network
    from crmapconverter.io.viewer import MainWindow as ViewerWidget
    import crmapconverter.io.viewer as CRViewerQT
except:
    print("You need first to install crmapconverter")


try:
    from crmapconverter.osm2cr.main import start_gui as gui_osm2cr
except ModuleNotFoundError as module_err:
    print(module_err)
    print("It seems like you did not install the dependencies for osm2cr.")
except:
    print("You need first to install crmapconverter to get osm2cr converter")

#GLOBAL VARIABLES
"""Those variables set the dimensions of the main window"""
high = 902
width = 960

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
            column= self.column,
            row= self.row,
            sticky= W + N,
            padx= self.padx,
            pady= self.pady)

    def set_icon(self, icon):
        """Function used to modify while running the GUI the icon of a
        button, for example to set it when it's disabled or clicked"""
        self.icon = image_encoding("gui_src/" + icon)
        self.configure(image=self.icon)


class My_Canvas(Canvas):
    """Class defining the design of the canvas used in the interface defined below"""

    def __init__(self, parent, row, pady=0, sticky=None, **kwargs):
        self.row = row
        self.pady = pady
        self.sticky = sticky
        Canvas.__init__(self, parent,**kwargs)
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


class My_Text(Canvas):
    """Class defining the design of the text displays used in the interface defined below"""

    def __init__(self, parent, row, text="", pady=0,
                 font_color = "white", type_text=None, **kwargs):
        self.row = row
        self.text = text
        self.pady = pady
        self.font_color = font_color
        Canvas.__init__(self, parent, **kwargs)
        self.configure(background = '#003359')
        self.configure(highlightbackground='#003359')
        self.grid(
            row= self.row,
            pady= self.pady,
            sticky= W+E
        )
        self.height= 50
        self.curve= 50
        self.length= 800

        if type_text=="path":
            """Special format used to display a path"""
            self.create_rectangle(self.curve/2, 0, self.length+self.curve/2, self.height, fill="White", outline="White")
            self.create_oval(self.length, 0, self.length+self.curve, self.height, fill="White", outline="White")
            self.create_text(self.curve/2,
                         self.height/3,
                         anchor=NW,
                         font=('KacstDecorative', -20, 'italic'),
                         text=text)
        else:
            """default text format"""
            self.my_text = Text(self,
                                font=('KacstDecorative', -20),
                                bg='#003359',
                                fg='White',
                                padx=20,
                                pady=10,
                                spacing1=30,
                                spacing2=10,
                                wrap=WORD)

            self.my_text.grid(row=0)

def osm2cr():
    """Converter OSM2CR intial function (V1.0)"""
    global welcome
    welcome.destroy()
    welcome = None
    gui_osm2cr()
    welcome = initialise()
    OSM2CRActivity1(welcome).mainloop()

def go_help(help_text="test"):
    """Function which displays a help pop-up in each converter to help the user"""
    try:
        help_window = Tk()
        help_window.title("Help")
        help_window.resizable(False, False)
        text= My_Text(help_window, 0, text=help_text)
        text.my_text.delete(1.0, END)
        text.my_text.insert(INSERT,help_text)
        help_window.mainloop()
    except TclError:
        print("Error code 15")

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

        def osm2cr():
            """Function to access the new GUI of OSM2CR Converter"""
            self.destroy()
            OSM2CRActivity1(window).mainloop()

        def opendrive2cr():
            """Function to access the new GUI of OpenDRIVE2Converter"""
            self.destroy()
            OD2CRActivity1(window).mainloop()

        def crviewer():
            """Function to access the new GUI of Common Road Visualizer"""
            self.destroy()
            CRViewerActivity1(window).mainloop()


        # First line - Canvas 1
        self.button_canvas_1 = My_Canvas(self, 2)
        self.b1 = My_Button(self.button_canvas_1, 2, 0, osm2cr,
                            "Groupe 1.png")
        self.b2 = My_Button(self.button_canvas_1, 2, 1, default,
                            "Groupe 2.png" )
        self.b3 = My_Button(self.button_canvas_1, 2, 2, opendrive2cr,
                            "Groupe 3.png")

        self.button_canvas_2 = My_Canvas(self, 3, pady=30)
        self.b4 = My_Button(self.button_canvas_2, 3, 0, default,
                            "Groupe 4.png")
        self.b5 = My_Button(self.button_canvas_2, 3, 1, default,
                            "Groupe 5.png")
        self.b6 = My_Button(self.button_canvas_2, 3, 2, crviewer,
                            "Groupe 6.png")


class InterfaceToolTemplate(Frame):
    """Classe driving the interface of main window inside tools"""

    def __init__(self, window, **kwargs):
        Frame.__init__(self, window, bg="#003359", **kwargs)
        self.grid()

        def go_home():
            """Function to get on the home window"""
            self.destroy()
            Home(window).mainloop()

        # Buttons Head
        self.Can = My_Canvas(self, 1, sticky=W+E)

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

        # Documentation
        def go_help_local():
            """Function uploading locally the help pop-up with the right documentation"""
            go_help(OSM2CR_help_text)

        self.help.configure(command=go_help_local)


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
        # Documentation
        def go_help_local():
            """Function uploading locally the help pop-up with the right documentation"""
            go_help(OD2CR_help_text)
        self.help.configure(command=go_help_local)


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

        #Read and Export OpenDRIVE Map
        self.output_canvas = My_Canvas(self, 3)
        self.export = My_Button(self.output_canvas, 0, 1, default,
                              "Groupe 14.png",
                              padx=20)

        class FileOpener(QWidget):
            """Class providin a FileOpener pop-up in PyQt5"""

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

        self.path = ""

        def open_OD2():
            """Function driving the opening of an OpenDRIVE map in the converter"""
            app = QApplication(sys.argv)
            A = G.OpenDriveConvertWindow("")
            app.disconnect()
            self.path = A.openOpenDriveFileDialog()
            app.exit()
            A.destroy()
            self.open_canvas.destroy()
            self.export.set_icon("Groupe 7.png")
            self.export.configure(command=export_OD)
            My_Text(self, 2, self.path, pady=50, type_text="path")

        def export_OD():
            """Function performing the conversion and opeing a save file pop-up
            to save the CommonRoad map created"""
            app = QApplication(sys.argv)
            C = G.OpenDriveConvertWindow("")
            C.load_opendriveFile(self.path)
            C.exportAsCommonRoad()
            app.exit()
            C.destroy()
            global welcome
            welcome.destroy()
            welcome = None
            welcome = initialise()
            Home(welcome).mainloop()

        self.open.configure(command=open_OD2)


class CRViewerFrame(InterfaceToolTemplate):
    """Class driving the frame of CR Viewer"""

    def __init__(self, window, **kwargs):
        InterfaceToolTemplate.__init__(self, window, **kwargs)
        #Head Text
        self.welcoming_text = My_Title(self.Can, "OSM2CR_head.png",
                                 column=2, pady=10, padx=40)


class CRViewerActivity1(OD2CRFrame):
    """Class driving the interface of the first Activity of CRViewer"""

    def __init__(self, window, **kwargs):
        OD2CRFrame.__init__(self, window, **kwargs)
        global welcome
        welcome.destroy()
        welcome = None
        CRviewer_run()
        welcome = initialise()
        Home(welcome).mainloop()
        welcome = welcome



# INITIALISATION
def initialise():
    """Function initialising the GUI to the Home Window"""
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