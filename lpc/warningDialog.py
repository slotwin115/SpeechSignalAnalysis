
from PyQt5.QtWidgets import QMessageBox

class Warning(QMessageBox):
    def __init__(self, message):
        super(Warning, self).__init__()

        self.setIcon(QMessageBox.Warning)
        self.setWindowTitle("Warning")
        self.setText(message)
        self.show()

