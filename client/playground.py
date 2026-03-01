
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import QSize, Qt
import sys

class MyWindow(QMainWindow):
    
    def __init__(self):

        super().__init__()          
        self.setWindowTitle("Random ahh messenger")
        self.setGeometry(100, 100, 500, 400)
        self.setFixedSize(QSize(500, 400))


    def SendButton(self):

        btn = QPushButton( "Send", self)
        btn.setGeometry(350, 325, 100, 50)
        btn.clicked.connect(self.on_button_click)

    def on_button_click(self):
        print("*message*")
    
    def Textbox(self):
        TextInput = QLineEdit()
        TextInput.setMaxLength(10)
        TextInput.setPlaceholderText("Enter your text")
        #TextInput.setReadOnly(True) # uncomment this to make it read-only
        TextInput.returnPressed.connect(self.return_pressed)
        TextInput.selectionChanged.connect(self.selection_changed)
        TextInput.textChanged.connect(self.text_changed)
        TextInput.textEdited.connect(self.text_edited)

        self.setCentralWidget(TextInput)

    def return_pressed(self):
        print("Return pressed")
    
    def selection_changed(self):
        print("Selection changed")

    def text_changed(self):
        print("Text changed")

    def text_edited(self):
        print("Text edited")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.Textbox()
    window.SendButton()
    window.show()
    sys.exit(app.exec_())
