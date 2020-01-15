import os
import signal
import sys
import time

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
except:
    print("You need to install manually commonroad")

from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import *
from PIL import Image
from PIL import ImageTk


try:
    from crmapconverter.osm2cr.main import start_gui
except ModuleNotFoundError as module_err:
    print(module_err)
    print("It seems like you did not install the dependencies for osm2cr.")
except:
    print("You need to install manually commonroad")

# osm2cr
def osm2cr():
    start_gui()

# OpenDrive2Lanelet
def opendrive2Lanelet():
    """Open the conversion tool for OpenDRIVE in a new window."""
    G.opendrive_gui()

def default():
    print("coming soon")

class Design(Button):
    """Class defining the design of the buttons used in the interface defined below"""

    def __init__(self, parent, row, column, icon, command=print("ok"), **kwargs):
        self.row = row
        self.column = column
        self.icon = icon
        self.command = command
        Button.__init__(self, parent, **kwargs)
        self.configure(image=icon)
        self.configure(borderwidth=0)
        self.configure(activebackground='#003359')
        self.configure(background='#003359')
        self.configure(cursor='hand2')
        self.configure(command=command)
        self.configure(highlightbackground='#003359')
        self.grid(column=self.column, row=self.row)


class Interface(Frame):
    """Class driving the interface of main window"""

    def __init__(self, window, **kwargs):
        Frame.__init__(self, window, bg="#003359", **kwargs)
        self.grid()

        # welcoming text
        welcoming_text_src_pil = Image.open("V2.0/gui_src/welcoming_text.png")
        welcoming_text_src = ImageTk.PhotoImage(welcoming_text_src_pil)
        welcoming_text = Label(self, image=welcoming_text_src, background='#003359')
        welcoming_text.image = welcoming_text_src
        welcoming_text.grid(row=1, pady=15)

        def hey():
            self.destroy()

        def rebuild():
            self.destroy()
            Interface2(window).mainloop()


        # First line - Canvas 1
        button_canvas_1 = Canvas(self, background='#003359', highlightbackground='#003359')
        button_canvas_1.grid(row=2)

        b1_src_pil = Image.open("V2.0/gui_src/Groupe 1.png")
        b1_src = ImageTk.PhotoImage(b1_src_pil)
        b1 = Design(button_canvas_1, 2, 0, b1_src, command=osm2cr)

        b2_src_pil = Image.open("V2.0/gui_src/Groupe 2.png")
        b2_src = ImageTk.PhotoImage(b2_src_pil)
        b2 = Design(button_canvas_1, 2, 1, b2_src, command=default)

        b3_src_pil = Image.open("V2.0/gui_src/Groupe 3.png")
        b3_src = ImageTk.PhotoImage(b3_src_pil)
        b3 = Design(button_canvas_1, 2, 2, b3_src, command=opendrive2Lanelet)

        button_canvas_2 = Canvas(self, background='#003359', highlightbackground = '#003359')
        button_canvas_2.grid(row=3, pady=30)

        b4_src_pil = Image.open("V2.0/gui_src/Groupe 4.png")
        b4_src = ImageTk.PhotoImage(b4_src_pil)
        b4 = Design(button_canvas_2, 3, 0, b4_src, padx= 40, command=rebuild)

        b5_src_pil = Image.open("V2.0/gui_src/Groupe 5.png")
        b5_src = ImageTk.PhotoImage(b5_src_pil)
        b5 = Design(button_canvas_2, 3, 1, b5_src, padx=40, command=hey)


class InterfaceToolTemplate(Frame):
    """Classe driving the interface of main window inside tools"""

    def __init__(self, window, **kwargs):
        Frame.__init__(self, window, bg="#003359", **kwargs)
        self.grid()

        def home():
            self.destroy()
            Interface(window).mainloop()

        # button toujours là
        a_pil = Image.open("V2.0/gui_src/icon.png")
        a_src = ImageTk.PhotoImage(a_pil)
        a = Design(self, 1, 0, a_src, home)


class Interface2(InterfaceToolTemplate):
    """Class driving the interface of main window"""

    def __init__(self, fenetre, **kwargs):
        InterfaceToolTemplate.__init__(self, fenetre, **kwargs)

        # welcoming text
        welcoming_text_src_pil = Image.open("V2.0/gui_src/welcoming_text.png")
        welcoming_text_src = ImageTk.PhotoImage(welcoming_text_src_pil)
        welcoming_text = Label(self, image=welcoming_text_src, background='#003359')
        welcoming_text.image = welcoming_text_src
        welcoming_text.grid(row=1, pady=15)

        def hey():
            self.destroy()


        # First line - Canvas 1
        button_canvas_1 = Canvas(self, background='#003359', highlightbackground='#003359')
        button_canvas_1.grid(row=2)

        b1_src_pil = Image.open("V2.0/gui_src/Groupe 1.png")
        b1_src = ImageTk.PhotoImage(b1_src_pil)
        b1 = Design(button_canvas_1, 2, 0, b1_src, command=osm2cr)

        b2_src_pil = Image.open("V2.0/gui_src/Groupe 2.png")
        b2_src = ImageTk.PhotoImage(b2_src_pil)
        b2 = Design(button_canvas_1, 2, 1, b2_src, command=default)


# INITIALISATION

def initialise():
    window = Tk()
    window.title("Common Road Tools")
    try:
        window.iconbitmap("V2.0/gui_src/icon.ico")
    except TclError:
        ico = PhotoImage(file="V2.0/gui_src/icon.png")
        window.tk.call('wm', 'iconphoto', window._w, ico)
    window.geometry('640x600')
    window['bg'] = '#003359'
    window.resizable(False, False)

    # head
    head_src_pil = Image.open("V2.0/gui_src/head.png")
    head_src = ImageTk.PhotoImage(head_src_pil)
    head = Label(window, image=head_src, background='#003359')
    head.image = head_src
    head.grid(row=0)

    return window


welcome = initialise()

Interface2(welcome).mainloop()





