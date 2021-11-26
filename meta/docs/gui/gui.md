# Documentation for the folder gui

The gui is programmed in a descriptive architecture. 

![](architecture_gui_parts.png)

Every rectangle in the picture above represents on package. Each package can contain more packages.

**0. mwindow.py**: not mentioned in the picture, is the representation of the whole window. uses the mwindow_service_layer package to hide the functionality for the sake of readability.

**1. top_bar**: holds the menu_bar_wrapper and the toolbar_wrapper because both share file functionality.

**2. toolboxes**: contains the toolboxes. the toolboxes are the actual implementations of e.g. how the lanelets or the obstacles are edited.

**3. animated_viewer_wrapper**: contains all functionality for the display of the scenarios and also the interaction with it.

**5. console:**: for printing out.