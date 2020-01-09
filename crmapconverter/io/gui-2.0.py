import os
import signal
import sys

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
        self.grid(column=self.column, row=self.row)


class Interface(Frame):
    """Class driving the interface of main window"""

    # osm2cr
    def osm2cr(self):
        return 1
        #start_gui()

    # OpenDrive2Lanelet
    def opendrive2Lanelet(self):
        """Open the conversion tool for OpenDRIVE in a new window."""
        return 2
        #G.opendrive_gui()

    def __init__(self, fenetre, **kwargs):
        Frame.__init__(self, fenetre, bg="#003359", **kwargs)
        self.pack(fill=BOTH)

        # head
        head_src_pil = Image.open("gui_src/head.png")
        head_src = ImageTk.PhotoImage(head_src_pil)
        head = Label(self, image=head_src, background='#003359')
        head.image = head_src
        head.grid(row=0)

        # welcoming text
        welcoming_text_src_pil = Image.open("gui_src/welcoming_text.png")
        welcoming_text_src = ImageTk.PhotoImage(welcoming_text_src_pil)
        welcoming_text = Label(self, image=welcoming_text_src, background='#003359')
        welcoming_text.image = welcoming_text_src
        welcoming_text.grid(row=1, pady=15)

        # Button_display
        active_color = '#003359'

        # First line - Canvas 1
        button_canvas_1 = Canvas(self)
        button_canvas_1.grid(row=2)

        b1_src_pil = Image.open("gui_src/Groupe 1.png")
        b1_src = ImageTk.PhotoImage(b1_src_pil)
        b1 = Design(button_canvas_1, 2, 0, b1_src)

        b2_src_pil = Image.open("gui_src/Groupe 2.png")
        b2_src = ImageTk.PhotoImage(b2_src_pil)
        b2 = Design(button_canvas_1, 2, 1, b2_src)

        b3_src_pil = Image.open("gui_src/Groupe 3.png")
        b3_src = ImageTk.PhotoImage(b3_src_pil)
        b3 = Design(button_canvas_1, 2, 2, b3_src)
        b3.grid(row=2, column=2)

        button_canvas_2 = Canvas(self, background='#003359', highlightbackground = '#003359')
        button_canvas_2.grid(row=3, pady=30)

        b4_src_pil = Image.open("gui_src/Groupe 4.png")
        b4_src = ImageTk.PhotoImage(b4_src_pil)
        b4 = Design(button_canvas_2, 3, 0, b4_src, padx= 40)

        b5_src_pil = Image.open("gui_src/Groupe 5.png")
        b5_src = ImageTk.PhotoImage(b5_src_pil)
        b5 = Design(button_canvas_2, 3, 1, b5_src, padx=40)


# INITIALISATION
welcome = Tk()
welcome.title("Common Road Tools")
try:
    welcome.iconbitmap("gui_src/icon.ico")
except TclError:
    ico = PhotoImage(file="gui_src/icon.png")
    welcome.tk.call('wm', 'iconphoto', welcome._w, ico)
welcome.geometry('640x600')
welcome['bg'] = '#003359'
welcome.resizable(False, False)
# headup


interface = Interface(welcome)
interface.mainloop()

