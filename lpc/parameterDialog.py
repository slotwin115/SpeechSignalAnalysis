import sys
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                             QGroupBox, QLabel, QSpinBox, QVBoxLayout)

class Dialog(QDialog):
    def __init__(self):
        super(Dialog, self).__init__()

        modeArray = ("default", "psd", "magnitude", "angle", "phase")
        scaleArray = ("default", "linear", "dB")
        self.createFormGroupBox(modeArray, scaleArray)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Set parameters")


    def createFormGroupBox(self, modeArray, scaleArray):
        self.formGroupBox = QGroupBox("Parameters:")
        self.layout = QFormLayout()
        self.fftsp = QSpinBox()
        self.fftsp.setMinimum(4)
        self.fftsp.setMaximum(sys.maxsize)
        self.fftsp.setValue(1024)
        self.layout.addRow(QLabel("NFFT:"), self.fftsp)

        self.oversp = QSpinBox()
        self.oversp.setMinimum(1)
        self.oversp.setMaximum(sys.maxsize)
        self.oversp.setValue(900)
        self.layout.addRow(QLabel("noverlap:"), self.oversp)

        self.modeCb = QComboBox()
        self.modeCb.addItems(modeArray)
        self.layout.addRow(QLabel("mode:"), self.modeCb)

        self.scaleCb = QComboBox()
        self.scaleCb.addItems(scaleArray)
        self.layout.addRow(QLabel("scale:"), self.scaleCb)

        self.formGroupBox.setLayout(self.layout)

    @staticmethod
    def decompose():
        dialog = Dialog()
        result = dialog.exec_()
        nfft = dialog.fftsp.value()
        noverlap = dialog.oversp.value()
        mode = dialog.modeCb.currentText()
        scale = dialog.scaleCb.currentText()

        return (nfft, noverlap, mode, scale ,result == QDialog.Accepted)

