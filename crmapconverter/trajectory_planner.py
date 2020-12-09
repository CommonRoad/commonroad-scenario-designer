from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys

'''Custom QLabel class'''


class myImgLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(myImgLabel, self).__init__(parent)
        f = QFont("ZYSong18030", 10)  # Set the font, font size
        self.setFont(f)  # After the event is not defined, the two sentences are deleted or commented out.

    '''Reload the mouse click event (click) '''

def mousePressEvent(self, event: QMouseEvent):
    if event.button() == Qt.LeftButton:
        self.close()


"""def mousePressEvent(self, event):
    if event.buttons() == QtCore.Qt.LeftButton:  # left button pressed
        self.setText("Click the left mouse button for the event: define it yourself")
        print("Hello")  # response test statement
    elif event.buttons() == QtCore.Qt.RightButton:  # right click
        self.setText("Click the right mouse button for the event: define it yourself")
        print("right click")  # response test statement
    elif event.buttons() == QtCore.Qt.MidButton:  # Press
        self.setText("Click the middle mouse button for the event: define it yourself")
        print("click the middle mouse button")  # response test statement
    elif event.buttons() == QtCore.Qt.LeftButton | QtCore.Qt.RightButton:  # Left and right buttons simultaneously pressed
        self.setText("Also click the left and right mouse button event: define it yourself")
        print("Click the left and right mouse button")  # response test statement
    elif event.buttons() == QtCore.Qt.LeftButton | QtCore.Qt.MidButton:  # Left middle button simultaneously pressed
        self.setText("Also click the middle left mouse button event: define it yourself")
        print("Click the left middle button")  # response test statement
    elif event.buttons() == QtCore.Qt.MidButton | QtCore.Qt.RightButton:  #
        self.setText("Also click the middle right mouse button event: define it yourself")
        print("click the middle right button")  # response test statement
    elif event.buttons() == QtCore.Qt.LeftButton | QtCore.Qt.MidButton \
         | QtCore.Qt.RightButton:  # Left and right button simultaneously pressed
        self.setText("Also click the left mouse button right event: define it yourself")
        print("Click the left and right mouse button")  # response test statement

    '''Overload the wheel scrolling event '''"""


def wheelEvent(self, event):
    # if event.delta() > 0: # Roller up, PyQt4
    # This function has been deprecated, use pixelDelta() or angleDelta() instead.
    angle = event.angleDelta() / 8  # Returns the QPoint object, the value of the wheel, in 1/8 degrees


    angleX = angle.x()  # The distance rolled horizontally (not used here)
    angleY = angle.y()  # The distance that is rolled vertically
    if angleY > 0:
        self.setText("Scroll up event: define itself")
        print("mouse wheel scrolling")  # response test statement
    else:
        self.setText("Scroll down event: define itself")
        print("mouse wheel down")  # response test statement

'''Overload the mouse double click event '''


def mouseDoubieCiickEvent(self, event):
    # if event.buttons () == QtCore.Qt.LeftButton: # Left button pressed
    # self.setText ("Double-click the left mouse button function: define it yourself")
    self.setText("mouse double click event: define itself")


'''Reload the mouse button release event '''


def mouseReleaseEvent(self, event):
    self.setText("mouse release event: define itself")
    print("mouse release")  # response test statement


'''Reload the mouse movement event '''


def mouseMoveEvent(self, event):
    self.setText("Mouse Move Event: Defining Yourself")
    print("mouse movement")  # response test statement


# '''Reload the mouse to enter the control event '''
#    def enterEvent(self, event):
#
#
# '''Reload the mouse to leave the control event '''
#    def leaveEvent(self, event):
#


'''Define the main window'''


class MyWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.imgLabel = myImgLabel()  # declare imgLabel
        self.image = QImage()  # declare new img
        if self.image.load("image/cc2.png"):  # If the image is loaded, then
            self.imgLabel.setPixmap(QPixmap.fromImage(self.image))  # Display image

        self.gridLayout = QtWidgets.QGridLayout(self)  # Layout settings
        self.gridLayout.addWidget(self.imgLabel, 0, 0, 1, 1)  # comment out these two sentences, no image will be displayed


'''Main function'''
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myshow = MyWindow()
    myshow.show()
    sys.exit(app.exec_())