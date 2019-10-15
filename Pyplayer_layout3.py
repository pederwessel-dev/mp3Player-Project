from PyQt5.QtCore import QDir, Qt, QUrl, QCoreApplication,QSize,QFileInfo
from PyQt5.QtCore import pyqtSignal as Signal,pyqtSlot as Slot, QThread, QAbstractListModel
import datetime,time
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from PyQt5.QtGui import QPalette,QColor

from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
        QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget, QStyleFactory,QDialog, QLineEdit)

from PyQt5.QtWidgets import QMainWindow,QWidget, QPushButton, QAction, QMessageBox,QTableWidgetItem, QGridLayout, QDialogButtonBox
from PyQt5.QtGui import QIcon
import sys
import mp3playerGUILayout3
from mutagen.mp3 import MP3


class PlaylistModel(QAbstractListModel):
    def __init__(self, playlist, *args, **kwargs):
        super(PlaylistModel, self).__init__(*args, **kwargs)
        self.playlist = playlist

    def data(self, index, role):
        if role == Qt.DisplayRole:
            media = self.playlist.media(index.row())
            return media.canonicalUrl().fileName()

    def rowCount(self, index):
        return self.playlist.mediaCount()

class MainUIClass(QMainWindow,mp3playerGUILayout3.Ui_MainWindow):

    def __init__(self,parent=None):
        super(MainUIClass,self).__init__(parent)
        self.setupUi(self)
        self.fixLayout()
        self.mediaPlayer = QMediaPlayer()
        self.mediaPlayer.error.connect(self.erroralert)

        self.playlist = QMediaPlaylist()
        self.mediaPlayer.setPlaylist(self.playlist)

        #Connecting button clicks and functions
        self.OpenButton.clicked.connect(self.addtoqueue)
        self.PlayButton.clicked.connect(self.play)
        self.StopButton.clicked.connect(self.mediaPlayer.stop)
        self.muteButton.clicked.connect(self.mute)
        self.ForwardButton.clicked.connect(self.playlist.next)
        self.BackwardButton.clicked.connect(self.playlist.previous)

        self.addToQueue.clicked.connect(self.addtoqueue)
        self.repeatButton.clicked.connect(self.repeat)
        self.shuffleButton.clicked.connect(self.shuffle)

        #Adding valuechange functionality
        self.Timeline.setRange(0, 100)
        self.Timeline.sliderReleased.connect(self.set_position)

        self.mediaPlayer.setVolume(50)
        self.volume_on = True
        self.Volumedial.setValue(50)
        self.Volumedial.valueChanged.connect(self.set_volume)

        self.displayfilename_thread = DisplayThread()
        self.displayfilename_thread.start()
        self.displayfilename_thread.labeltext.connect(self.displayfilename_func)

        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.playlist.currentMediaChanged.connect(self.filenameChange)
        self.tableWidget.cellDoubleClicked.connect(self.getcurrentrow)
        #self.mediaPlayer.mutedChanged.connect(self.muteChange)

        self.items = 0

        self.repeated = True
        self.shuffled = True

        #p = self.palette()
        #p.setColor(self.backgroundRole(), Qt.lightGray)
        #self.setPalette(p)
        #self.dumpObjectInfo()

    @Slot()
    def addtoqueue(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select song")# QDir.homePath())
        if filename != '':
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.addtoview(filename)

    def addtoview(self,filename):
        self.tableWidget.insertRow(self.items)
        table_filename = QTableWidgetItem(filename.split("/")[-1])
        inputdialog = InputDialog()
        inputdialog.exec_()
        if len(inputdialog.accept_func()[0])>0 or len(inputdialog.accept_func()[1])>0:
            table_artist = QTableWidgetItem(inputdialog.accept_func()[0])
            table_artist.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            table_song = QTableWidgetItem(inputdialog.accept_func()[1])
            table_song.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        else:
            table_artist = QTableWidgetItem("..artist..")
            table_artist.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            table_song = QTableWidgetItem("..song..")
            table_song.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        self.tableWidget.setItem(self.items,0,table_artist)
        self.tableWidget.setItem(self.items,1,table_song)
        for i in range(self.playlist.mediaCount()):
            print(self.playlist.media(i).canonicalUrl().fileName())
        self.PlayButton.setEnabled(True)
        self.items+=1

    @Slot()
    def play(self):
        if self.playlist.mediaCount() == 0:
            alert = selectfileAlert()
            alert.exec_()
        elif self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

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

    @Slot()
    def repeat(self):
        if self.repeated:
            self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
            self.repeatButton.setFlat(True)
            self.repeated = False
            self.statusbar.showMessage("Repeat function is on")
        else:
            self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemOnce)
            self.repeatButton.setFlat(False)
            self.repeated = True
            self.statusbar.showMessage("Repeat function is off")
    @Slot()
    def shuffle(self):
        if self.shuffled:
            self.playlist.setPlaybackMode(QMediaPlaylist.Random)
            self.shuffleButton.setFlat(True)
            self.shuffled = False
            self.displayfilename_thread.exit()
            self.statusbar.clearMessage()
            self.statusbar.showMessage("Shuffle function is on",100000)
            self.statusbar.clearMessage()
            self.displayfilename_thread.start()
        else:
            self.playlist.setPlaybackMode(QMediaPlaylist.Sequential)
            self.shuffleButton.setFlat(False)
            self.shuffled = True
            self.displayfilename_thread.exit()
            self.statusbar.clearMessage()
            self.statusbar.showMessage("Shuffle function is off",100000)
            self.statusbar.clearMessage()
            self.displayfilename_thread.start()

    @Slot('qint64', name="positionChanged")
    def positionChanged(self, position):
        self.Timeline.setValue(position)
        self.displaytime_func(position)

    @Slot()
    def set_position(self):
        self.mediaPlayer.setPosition(self.Timeline.value())#self.mediaPlayer.setPosition(position)

    @Slot('qint64', name = 'durationChanged')
    def durationChanged(self, duration):
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

    def fixLayout(self):
        _translate = QCoreApplication.translate
        self.PlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.BackwardButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.ForwardButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
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
        self.tableWidget.setHorizontalHeaderLabels(["Artist","Song"])

    def erroralert(self):
        print(self.mediaPlayer.error())
        #print("type of args: " + type(args), "  args: ",args)
    def getcurrentrow(self,row,col):
        self.playlist.setCurrentIndex(row+1)
        self.mediaPlayer.play()

class selectfileAlert(QMessageBox):
    def __init__(self,parent=None):
        super(selectfileAlert,self).__init__(parent)
        self.setIcon(self.Information)
        self.setText("Please select a file")
        self.setInformativeText("No song is queued.")

class InputDialog(QDialog):
    def __init__(self,parent=None):
        super(InputDialog,self).__init__(parent)
        artist = QLabel("Artist: ")
        self.artistEdit = QLineEdit()
        song = QLabel("Song: ")
        informativeText = QLabel("<font size = 4> <b>Choose artist and song name to display</b></font>")
        self.songEdit = QLineEdit()
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Apply |QDialogButtonBox.Cancel)

        grid = QGridLayout()
        grid.addWidget(informativeText,0,0,1,4)
        grid.addWidget(artist, 1, 0)
        grid.addWidget(self.artistEdit,1,1,1,3)
        grid.addWidget(song,2,0)
        grid.addWidget(self.songEdit,2,1,1,3)
        grid.addWidget(self.buttonBox,4,1,1,2)
        self.setLayout(grid)
        self.resize(400, 200)
        self.setWindowTitle("Display song information")

        self.buttonBox.clicked.connect(self.accept_func)
        self.buttonBox.rejected.connect(self.reject)

    def accept_func(self):
        self.accept()
        return self.artistEdit.text(),self.songEdit.text()

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


def setstyle(app):

    palette = QPalette() # Get a copy of the standard palette.
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    # Additional CSS styling for tooltip elements.
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

if __name__ == "__main__":
    a = QApplication(sys.argv)
    app = MainUIClass()
    app.setStyle(QStyleFactory.create("Fusion"))
    #setstyle(app)
    app.show()
    a.exec_()
