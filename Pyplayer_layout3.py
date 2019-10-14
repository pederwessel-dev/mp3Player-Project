from PyQt5.QtCore import QDir, Qt, QUrl, QCoreApplication,QSize
from PyQt5.QtCore import pyqtSignal as Signal,pyqtSlot as Slot, QThread
import datetime,time
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist

from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
        QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget)

from PyQt5.QtWidgets import QMainWindow,QWidget, QPushButton, QAction, QMessageBox
from PyQt5.QtGui import QIcon
import sys
import mp3playerGUILayout3
from mutagen.mp3 import MP3

#openedfile_signal = Signal(str)
#loadedfile_signal = Signal(float)
#song_signal = Signal(str
#busy_signal = Signal(str)
#loopcontrol_signal = Signal(str)
#FIX EMIT FUNCTION for volume!

class MainUIClass(QMainWindow,mp3playerGUILayout3.Ui_MainWindow):

    def __init__(self,parent=None):
        super(MainUIClass,self).__init__(parent)
        self.setupUi(self)
        self.fixLayout()
        #Connecting button clicks and functions
        self.OpenButton.clicked.connect(self.OpenFile_clicked)
        self.PlayButton.clicked.connect(self.play)
        self.StopButton.clicked.connect(self.stop)
        self.muteButton.clicked.connect(self.mute)
        #self.Forward.pressed.connect(self.forward) #Implement QThread!!!!!
        #self.Backward.pressed.connect(self.backward)

        self.mediaPlayer = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        #Adding valuechange functionality
        self.Timeline.setRange(0, 0)
        self.Timeline.sliderReleased.connect(self.set_position)

        self.mediaPlayer.setVolume(50)
        self.volume_on = True
        self.Volumedial.setValue(50)
        self.Volumedial.valueChanged.connect(self.set_volume)

		#initiating the Threads
		#self.threadclass = ThreadClass()
		#self.loopcontrol_signal.connect(self.threadclass.loopcontrol_func)
		#self.threadclass.new_time.connect(self.displaytime)
		#self.threadclass.start()

        self.displayfilename_thread = DisplayThread()
        self.displayfilename_thread.start()
        self.displayfilename_thread.labeltext.connect(self.displayfilename_func)

        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.playlist.currentMediaChanged.connect(self.filenameChange)
        #self.mediaPlayer.mutedChanged.connect(self.muteChange)

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.lightGray)
        self.setPalette(p)
        self.dumpObjectInfo()

    @Slot()
    def OpenFile_clicked(self):
        print(self.mediaPlayer.mediaStatus())
        fileName, _ = QFileDialog.getOpenFileName(self, "Select song")# QDir.homePath())
        if fileName != '':
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            #self.mediaPlayer.setMedia(QMediaContent()
            self.mediaPlayer.setPlaylist(self.playlist)
            self.PlayButton.setEnabled(True)

    @Slot()
    def play(self):
        print(self.mediaPlayer.mediaStatus())
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        elif self.mediaPlayer.mediaStatus() == QMediaPlayer.NoMedia:
            self.selectfile_alert()
        else:
            self.mediaPlayer.play()

    @Slot()
    def stop(self):
        self.mediaPlayer.stop()
        print(self.mediaPlayer.mediaStatus())

    @Slot()
    def set_volume(self):
        volume = self.Volumedial.value()
        self.mediaPlayer.setVolume(volume)

    @Slot(QMediaPlayer.State)
    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.PlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            icon = self.style().standardIcon(QStyle.SP_DialogYesButton)
            self.PlayingIcon.setPixmap(icon.pixmap(QSize(15,15)))
        elif self.mediaPlayer.state() == QMediaPlayer.StoppedState:
            filename = "........Select song to enjoy the moment........"
            self.displayfilename_thread.filename = filename
            self.PlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            icon = self.style().standardIcon(QStyle.SP_DialogNoButton)
            self.PlayingIcon.setPixmap(icon.pixmap(QSize(15,15)))
        else:
            self.PlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            icon = self.style().standardIcon(QStyle.SP_DialogYesButton)
            self.PlayingIcon.setPixmap(icon.pixmap(QSize(15,15)))

    @Slot('qint64', name="positionChanged")
    def positionChanged(self, position):
        self.Timeline.setValue(position)
        self.displaytime_func(position)

    @Slot()
    def set_position(self):
        self.mediaPlayer.setPosition(self.Timeline.value())#self.mediaPlayer.setPosition(position)

    @Slot('qint64', name = 'durationChanged')
    def durationChanged(self, duration):
        print("duration",type(duration))
        self.Timeline.setRange(0, duration)

    def displaytime_func(self,position):
        sec = round(position/1000.)
        sec_dt = datetime.timedelta(seconds=sec)
        sec_leftdt = datetime.timedelta(seconds=round(self.mediaPlayer.duration()/1000.) - sec+1)
        sec_format  = datetime.datetime(2000,1,1) + sec_dt
        sec_formatdt = datetime.datetime(2000,1,1) + sec_leftdt
        self.Timepassed.setText(sec_format.strftime("%M min %S s"))
        self.Timeleft.setText(sec_formatdt.strftime("-%M min %S s"))

    @Slot('QString')
    def displayfilename_func(self,text):
        filetext = text.split(",")[0].replace("text: ","")
        if text.split(",")[1] == " loop: 1":
            self.statusbar.showMessage(filetext)
            #self.displayfilename.setText(filetext)
        if text.split(",")[1] == " loop: 2":
            self.statusbar.showMessage(filetext)

    @Slot(QMediaContent)
    def filenameChange(self,media):
        if media:
            self.displayfilename_thread.quit()
            filename = media.canonicalUrl().fileName()
            filename = "Now playing ..... " + filename
            self.displayfilename_thread.filename = filename
            self.displayfilename_thread.start()

    @Slot()
    def mute(self):
        if self.volume_on:
            self.muteButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
            self.mediaPlayer.setMuted(True)
            self.volume_on = False
        else:
            self.muteButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
            self.mediaPlayer.setMuted(False)
            self.volume_on = True

    def selectfile_alert(self):
        alert = QMessageBox()
        alert.setIcon(QMessageBox.Information)
        alert.setText("Please select a file")
        alert.setInformativeText("No song is queued.")
        alert.exec_()

    def fixLayout(self):
        _translate = QCoreApplication.translate
        self.PlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.BackwardButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.ForwardButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.StopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.muteButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        icon = self.style().standardIcon(QStyle.SP_DialogNoButton)
        self.PlayingIcon.setPixmap(icon.pixmap(QSize(15,15)))
        self.addToQueue.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.repeatButton.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.shuffleButton.setIcon(self.style().standardIcon(QStyle.SP_DialogOkButton))

        self.shuffleButton.setText(_translate("MainWindow",""))
        self.repeatButton.setText(_translate("MainWindow",""))
        self.PlayingIcon.setText(_translate("MainWindow", ""))
        self.PlayButton.setText(_translate("MainWindow", ""))
        self.BackwardButton.setText(_translate("MainWindow", ""))
        self.ForwardButton.setText(_translate("MainWindow", ""))
        self.StopButton.setText(_translate("MainWindow", ""))
        self.Timepassed.setText(_translate("MainWindow", "00 min 00 s"))
        self.muteButton.setText(_translate("MainWindow", ""))
        self.addToQueue.setText(_translate("MainWindow", ""))
        #self.displayfilename.setText(_translate("MainWindow", ""))
        #self.displayfilename2.setText(_translate("MainWindow", ""))
        self.Timeleft.setText(_translate("MainWindow", "-00 min 00 s"))

class DisplayThread(QThread):
    labeltext = Signal(str)

    def __init__(self,parent=None):
        super(DisplayThread,self).__init__(parent)
        self.filename = "........Select song to enjoy the moment........"

    def run(self):
        filelist = []
        filelist_rev = []
        loop_list = []
        filename = self.filename
        while True:
            for element in self.filename_list2(self.filename):
                self.labeltext.emit("text: {}, loop: 2".format(element))
                time.sleep(0.2)
            for element in self.filename_list(self.filename):
                self.labeltext.emit("text: {}, loop: 2".format(element))
                time.sleep(0.15)

    def filename_list(self,filename):
        string_list = []
        if len(filename.split("/")) > 1:
            filename = "Now playing......  " + filename.split("/")[-1]
        for i in range(len(filename)):
            string_list.append(filename[:i])
        return string_list

    def filename_list2(self,filename):
        string_list = []
        if len(filename.split("/")) > 1:
            filename = "Now playing......  " + filename.split("/")[-1]
        for i in range(len(filename)):
            string_list.append(filename[i:])
        return string_list

if __name__ == "__main__":
    a = QApplication(sys.argv)
    app = MainUIClass()
    app.show()
    a.exec_()
