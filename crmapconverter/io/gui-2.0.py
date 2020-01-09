import os
import signal
import sys

import crmapconverter.io.gui as G

from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import *
from PIL import Image
from PIL import ImageTk

from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.file_reader import CommonRoadFileReader

from crmapconverter.osm.osm2lanelet import OSM2LConverter
from crmapconverter.osm.parser import OSMParser
from crmapconverter.osm.lanelet2osm import L2OSMConverter

from crmapconverter.opendriveparser.parser import parse_opendrive
from crmapconverter.opendriveconversion.network import Network
from crmapconverter.io.viewer import MainWindow as ViewerWidget

try:
    from crmapconverter.osm2cr.main import start_gui
except ModuleNotFoundError as module_err:
    print(module_err)
    print("It seems like you did not install the dependencies for osm2cr.")




class Interface(Frame):
    """Class driving the interface of main window"""

    # osm2cr
    def osm2cr(self):
        start_gui()

    # OpenDrive2Lanelet
    def opendrive2Lanelet(self):
        """Open the conversion tool for OpenDRIVE in a new window."""
        G.opendrive_gui()

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
        b1 = Button(button_canvas_1, command=self.osm2cr, image=b1_src, borderwidth=0, activebackground=active_color,
                    background='#003359', cursor='hand2')
        b1.image = b1_src
        b1.grid(row=2, column=0, sticky=W)

        b2_src_pil = Image.open("gui_src/Groupe 2.png")
        b2_src = ImageTk.PhotoImage(b2_src_pil)
        b2 = Button(button_canvas_1, image=b2_src, borderwidth=0, activebackground=active_color, background='#003359',
                    cursor='hand2')
        b2.image = b2_src
        b2.grid(row=2, column=1)

        b3_src_pil = Image.open("gui_src/Groupe 3.png")
        b3_src = ImageTk.PhotoImage(b3_src_pil)
        b3 = Button(button_canvas_1, command=self.opendrive2Lanelet, image=b3_src, borderwidth=0,
                    activebackground=active_color, background='#003359', cursor='hand2')
        b3.image = b3_src
        b3.grid(row=2, column=2, sticky=W)

        button_canvas_2 = Canvas(self)
        button_canvas_2.grid(row=3, pady=30)

        b4_src_pil = Image.open("gui_src/Groupe 4.png")
        b4_src = ImageTk.PhotoImage(b4_src_pil)
        b4 = Button(button_canvas_2, padx=10, image=b4_src, borderwidth=0, activebackground=active_color, background='#003359',
                    cursor='hand2')
        b4.image = b4_src
        b4.grid(row=3, column=0)

        b5_src_pil = Image.open("gui_src/Groupe 5.png")
        b5_src = ImageTk.PhotoImage(b5_src_pil)
        b5 = Button(button_canvas_2, image=b5_src, borderwidth=0, activebackground=active_color, background='#003359',
                    cursor='hand2')
        b5.image = b5_src
        b5.grid(row=3, column=1)


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
i = Interface(welcome)
interface.mainloop()
i.mainloop()
