import sys
import PyQt5.QtWidgets as p
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter
import wave
import pyaudio
import audiolazy as audio
import parameterDialog, warningDialog, parameterLpcDialog

class Window(p.QWidget):
    def __init__(self, parent = None):
        super(Window, self).__init__(parent)

        self.fileName = ""
        self.NFFT = 1024
        self.noverlap = 900
        self.mode = "default"
        self.scale = "default"

        self.setWindowTitle("Spectrogram")
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.canvas.resize_event()

        self.fileNameLabel = p.QLabel(self.fileName)
        self.fileNameLabel.setFixedHeight(17)

        self.plotButton = p.QPushButton("Plot")
        self.plotButton.setToolTip("Choose file to plot")
        self.plotButton.clicked.connect(self.plot)

        self.recordButton = p.QPushButton("Record")
        self.recordButton.setToolTip("Say something to your mic. (file name is arbitrarly 'recordedFile.wav')")
        self.recordButton.clicked.connect(self.record)

        self.replotButton = p.QPushButton("Reset original view")
        self.replotButton.setToolTip("Return plot to its original resolution")
        self.replotButton.clicked.connect(self.replot)

        self.playButton = p.QPushButton("Play")
        self.playButton.setToolTip("Play currently ploted file")
        self.playButton.clicked.connect(self.play)

        self.performLpcButton = p.QPushButton("Perform Lpc")
        self.performLpcButton.setToolTip("Compute lpc coefficients and compare aplitudes and frequencies with original signal")
        self.performLpcButton.setDisabled(True)
        self.performLpcButton.clicked.connect(self.lpc)

        self.playChunk = p.QPushButton("Play chunk")
        self.playChunk.setToolTip("Play choosen chunk")
        self.playChunk.setDisabled(True)
        self.playChunk.clicked.connect(self.playSample)

        self.playChunkLpc = p.QPushButton("Play lpc")
        self.playChunkLpc.setToolTip("Play lpc chunk")
        self.playChunkLpc.setDisabled(True)
        self.playChunkLpc.clicked.connect(self.playSampleLpc)

        layout = p.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.fileNameLabel)
        layout.addWidget(self.plotButton)
        layout.addWidget(self.performLpcButton)
        layout.addWidget(self.replotButton)
        layout.addWidget(self.recordButton)
        layout.addWidget(self.playButton)
        layout.addWidget(self.playChunk)
        layout.addWidget(self.playChunkLpc)
        self.setLayout(layout)

    def plot(self):
        nameFile = self.chooseFile()

        if nameFile:
            tmpNFFT, tmpNoverlap, tmpMode, tmpScale, ok = parameterDialog.Dialog().decompose()

            if ok & (tmpNFFT > tmpNoverlap):
                self.fileName = nameFile

                frequency, wavFile = wavfile.read(self.fileName, True)
                wavFileTime = len(wavFile) / frequency
                dt = wavFileTime / len(wavFile)
                t = np.arange(0.0, wavFileTime, dt)

                self.waveFileLength = len(wavFile)
                self.frequency = frequency

                self.NFFT = tmpNFFT
                self.noverlap = tmpNoverlap
                self.mode = tmpMode
                self.scale = tmpScale

                self.fileNameLabel.setText(self.fileName)
                self.figure.clear()
                plot1 = self.figure
                plot2 = plot1.add_subplot(211)
                plot2.set_ylabel("amplitude [dB]")
                plot2.plot(t, wavFile)
                plot3 = plot1.add_subplot(212, sharex = plot2)
                plot3.set_xlabel("time [mS]")
                plot3.set_ylabel("frequency [Hz]")
                Pxx, freqs, bins, im = plot3.specgram(wavFile, NFFT = self.NFFT, Fs = frequency, noverlap = self.noverlap, mode = self.mode, scale = self.scale)

                self.playChunk.setDisabled(True)
                self.playChunkLpc.setDisabled(True)
                self.performLpcButton.setEnabled(True)
                self.canvas.draw_idle()

            if ok & (tmpNFFT <= tmpNoverlap):
                self.showMSG("NFFT must be grater than noverlap !")

    def showMSG(self, message):
        msg = warningDialog.Warning(message)
        msg.exec()

    def replot(self):
        if self.fileName:
            frequency, wavFile = wavfile.read(self.fileName, True)
            wavFileTime = len(wavFile) / frequency
            dt = wavFileTime / len(wavFile)
            t = np.arange(0.0, wavFileTime, dt)

            self.waveFileLength = len(wavFile)
            self.frequency = frequency

            self.fileNameLabel.setText(self.fileName)
            self.figure.clear()
            plot1 = self.figure
            plot2 = plot1.add_subplot(211)
            plot2.set_ylabel("amplitude [dB]")
            plot2.plot(t, wavFile)
            plot3 = plot1.add_subplot(212, sharex = plot2)
            plot3.set_xlabel("time [s]")
            plot3.set_ylabel("frequency [Hz]")
            Pxx, freqs, bins, im = plot3.specgram(wavFile, NFFT = self.NFFT, Fs = frequency, noverlap = self.noverlap, mode = self.mode, scale = self.scale)
            self.canvas.draw_idle()

    def chooseFile(self):
        options = p.QFileDialog.Options()
        options |= p.QFileDialog.DontUseNativeDialog
        fileName, _ = p.QFileDialog.getOpenFileName(self, "Loadfile", "", "Wave Files (*.wav);;All Files (*)", options = options)

        return fileName

    def record(self):
        self.figure.clear()
        self.fileNameLabel.setText("Recording...")
        self.canvas.draw()

        outFileName = "recordedFile.wav"
        format = pyaudio.paInt16
        channels = 1
        rate = 22100
        chunk = 1024

        recordDur, ok = p.QInputDialog.getInt(self, "Record duration", "In seconds:", 7, 0, 30, 1)

        if ok:
            audio = pyaudio.PyAudio()

            stream = audio.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
            frames = []
            for i in range(0, int(rate / chunk * recordDur)):
                data = stream.read(chunk)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            audio.terminate()

            self.fileNameLabel.setText("")
            self.canvas.draw_idle()

            options = p.QFileDialog.Options()
            options |= p.QFileDialog.DontUseNativeDialog
            outFileName, _ = p.QFileDialog.getSaveFileName(self, "Save recorded file", outFileName, "Wav Files (*.wav)", options = options)

            if outFileName:
                if outFileName[(len(outFileName) - 1 - 3) : (len(outFileName))] == ".wav":
                    wavFile = wave.open(outFileName, "wb")
                    wavFile.setnchannels(channels)
                    wavFile.setsampwidth(audio.get_sample_size(format))
                    wavFile.setframerate(rate)
                    wavFile.writeframes(b''.join(frames))
                    wavFile.close()

                    a, b, c, d, ok = parameterDialog.Dialog().decompose()
                    if ok:
                        self.fileName = outFileName
                        self.NFFT = a
                        self.noverlap = b
                        self.mode = c
                        self.scale = d
                        self.replot()
                    else:
                        self.fileNameLabel.setText("")
                        self.canvas.draw_idle()
                else:
                    self.fileNameLabel.setText("")
                    self.canvas.draw_idle()
        else:
            self.fileNameLabel.setText("")
            self.canvas.draw_idle()

    def lpc(self):
        tmpNFFT, tmpNoverlap, tmpOrder, tmpMiliseconds, tmpStartPoint, tmpMode, tmpScale, ok = parameterLpcDialog.Dialog().decompose()

        start = int(round(tmpStartPoint / 1000 * self.frequency))
        end = start + int(round((self.frequency * tmpMiliseconds) / 1000))

        if ok & (tmpNFFT > tmpNoverlap) & (start < self.waveFileLength) & (end < self.waveFileLength):
            frequency, wavFile = wavfile.read(self.fileName, True)
            wavFileTime = len(wavFile) / frequency
            dt = wavFileTime / len(wavFile)
            t = np.arange(0.0, wavFileTime, dt)

            samplewaveFile = wavFile[start:end]
            samplet = t[start:end]

            order = tmpOrder
            wLPC = audio.lpc.autocor(samplewaveFile, order=order)
            tmp = np.negative(wLPC.numerator)
            tmp = np.append(0, tmp[2:len(tmp)])
            est_waveFile = lfilter(tmp, 1, samplewaveFile)

            for i in range(0, order - 1):
                est_waveFile[i] = 0


            tmpSample = []
            for i in range(0, len(samplewaveFile) - 1):
                tmpSample.append(samplewaveFile[i] & 0xff)

            audiopy = pyaudio.PyAudio()
            tmp1 = wave.open("tmp1.wav", "wb")
            tmp1.setnchannels(1)
            tmp1.setsampwidth(audiopy.get_sample_size(pyaudio.paInt16))
            tmp1.setframerate(frequency)
            tmp1.writeframes(b''.join(tmpSample))
            tmp1.close()

            #tmpSampleLpc = []
            #for i in range(0, len(est_waveFile) - 1):
            #    tmpSampleLpc.append(int(round(est_waveFile[i])) & 0xff)
            #
            #print(tmpSampleLpc)
            #tmp2 = wave.open("tmp2.wav", "wb")
            #print(1)
            #tmp2.setnchannels(1)
            #print(2)
            #tmp2.setsampwidth(audiopy.get_sample_size(pyaudio.paInt16))
            #print(3)
            #tmp2.setframerate(frequency)
            #print(4)
            #tmp2.writeframes(tmpSampleLpc)
            #print(5)
            #tmp2.close()
            #print(6)

            self.figure.clear()
            fig = self.figure

            plot1 = fig.add_subplot(221)
            plot1.set_title("Original signal")
            plot1.set_ylabel("amplitude [dB]")
            plot1.plot(np.subtract(samplet, samplet[0]), samplewaveFile)
            plot1.set_xlim(0, tmpMiliseconds / 1000)

            plot3 = fig.add_subplot(222, sharex = plot1)
            plot3.set_title("Lpc signal")
            plot3.plot(np.subtract(samplet, samplet[0]), est_waveFile)
            plot3.set_xlim(0, tmpMiliseconds / 1000)

            plot2 = fig.add_subplot(223, sharex = plot3)
            plot2.set_xlabel("time [s]")
            plot2.set_ylabel("frequency [Hz]")
            Pxx, freqs, bins, im = plot2.specgram(samplewaveFile, NFFT = tmpNFFT, Fs = frequency, noverlap = tmpNoverlap, mode = tmpMode, scale = tmpScale)
            plot2.set_xlim(0, tmpMiliseconds / 1000)

            plot4 = fig.add_subplot(224, sharex = plot2)
            plot4.set_xlabel("time [s]")
            Pxx, freqs, bins, im = plot4.specgram(est_waveFile, NFFT=tmpNFFT, Fs=frequency, noverlap=tmpNoverlap, mode=tmpMode, scale=tmpScale)
            plot4.set_xlim(0, tmpMiliseconds / 1000)

            self.playChunk.setEnabled(True)
            #self.playChunkLpc.setEnabled(True)
            self.canvas.draw_idle()

        if ok & (tmpNFFT <= tmpNoverlap):
            self.showMSG("NFFT must be grater than noverlap !")
        elif ok & (start >= self.waveFileLength):
            self.showMSG("Start point must be before end !")
        elif ok & (end >= self.waveFileLength):
            self.showMSG("Chunk must end before end of file !")

    def play(self):
        if self.fileName:
            f = wave.open(self.fileName, "rb")

            audio = pyaudio.PyAudio()
            chunk = 1024
            channels = f.getnchannels()
            rate = f.getframerate()
            format = audio.get_format_from_width(f.getsampwidth())

            stream = audio.open(format = format, channels = channels, rate = rate, output = True, frames_per_buffer = chunk)
            data = f.readframes(chunk)

            while data:
                stream.write(data)
                data = f.readframes(chunk)

            stream.stop_stream()
            stream.close()
            audio.terminate()

    def playSample(self):
        f = wave.open("tmp1.wav", "rb")

        audio = pyaudio.PyAudio()
        chunk = 1024
        channels = f.getnchannels()
        rate = f.getframerate()
        format = audio.get_format_from_width(f.getsampwidth())

        stream = audio.open(format = format, channels = channels, rate = rate, output = True, frames_per_buffer = chunk)
        data = f.readframes(chunk)

        while data:
            stream.write(data)
            data = f.readframes(chunk)

        stream.stop_stream()
        stream.close()
        audio.terminate()

    def playSampleLpc(self):
        f = wave.open("tmp2.wav", "rb")

        audio = pyaudio.PyAudio()
        chunk = 1024
        channels = f.getnchannels()
        rate = f.getframerate()
        format = audio.get_format_from_width(f.getsampwidth())

        stream = audio.open(format = format, channels = channels, rate = rate, output = True, frames_per_buffer = chunk)
        data = f.readframes(chunk)

        while data:
            stream.write(data)
            data = f.readframes(chunk)

        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == '__main__':
    app = p.QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())

