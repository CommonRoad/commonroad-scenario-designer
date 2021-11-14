### This is the temporary file for the implementation of the new architecture. ###

Here all information is written, which is then transfered to the README.md.

# Package structure #

/gui
Contains all files for the GUI - is structure by the appearing of the GUI. Every part of the gui has a wrapper class which is in a package.
[insert image here from packages and parts of the GUI]
gui.py -> the main entrance to the application.
   /files
   Contains the files used or edited or downloaded during usage of the GUI.
   /mwindow
   Is the main window, contains the model and the view for the controller.
   mwindow.py contains the "what" of the main window
   mwindow_view.py contains the "how" of the layout generation
   mwindow_controller.py contains the "how" of the actions

/meta
[all information for setup, explanation etc...]

/api
[package with some core functionalities of the system]

/cli
The command line interface, uses the api.

### Contribution Guideline ###

The whole package is structured by the appearance in the GUI. Any functionality of an appereance is in the service_layer/ of the regarding level.

### Coding conventions ###

#### Comments ####
Docstring python convention.

###  ###