# 출처 - https://github.com/ddd4117/GUI/blob/master/src/camera_test.py
# 수정 - webnautes

import PyQt5
import cv2
import sys
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from functools import partial


class ShowVideo(QtCore.QObject):

    height = 480
    width = 640

    VideoSignal = QtCore.pyqtSignal(QtGui.QImage)

    def __init__(self, parent=None):
        super(ShowVideo, self).__init__(parent)

    @QtCore.pyqtSlot()
    def startVideo(self, qlabel_widget):
        global image

        self.flag = 0
        camera = cv2.VideoCapture(0)

        # set status text msg
        qlabel_widget.setText("Start recording")

        while camera.isOpened():
            ret, image = camera.read()
            image = cv2.resize(image, (self.width, self.height))
            color_swapped_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            qt_image1 = QtGui.QImage(
                color_swapped_image.data,
                self.width,
                self.height,
                color_swapped_image.strides[0],
                QtGui.QImage.Format_RGB888,
            )
            self.VideoSignal.emit(qt_image1)
            if self.flag:
                break

            loop = QtCore.QEventLoop()
            QtCore.QTimer.singleShot(25, loop.quit)  # 25 ms
            loop.exec_()

        camera.release()

    @QtCore.pyqtSlot()
    def stopVideo(self, qlabel_widget):
        self.flag = 1
        qlabel_widget.setText("Stop recording")


class ImageViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self.image = QtGui.QImage()
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.image)
        self.image = QtGui.QImage()

    def initUI(self):
        self.setWindowTitle("Test")

    @QtCore.pyqtSlot(QtGui.QImage)
    def setImage(self, image):
        if image.isNull():
            print("Viewer Dropped frame!")

        self.image = image
        if image.size() != self.size():
            self.setFixedSize(self.size())
        self.update()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    thread = QtCore.QThread()
    thread.start()
    vid = ShowVideo()
    vid.moveToThread(thread)

    image_viewer = ImageViewer()
    image_viewer.setFixedSize(640, 480)
    vid.VideoSignal.connect(image_viewer.setImage)

    status_widget = QtWidgets.QLabel()

    start_btn = QtWidgets.QPushButton("Start")
    stop_btn = QtWidgets.QPushButton("Stop")

    start_btn.clicked.connect(partial(vid.startVideo, status_widget))
    stop_btn.clicked.connect(partial(vid.stopVideo, status_widget))
    start_btn.setIcon(start_btn.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
    stop_btn.setIcon(stop_btn.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))

    status_widget.setText("Pending")

    vertical_layout = QtWidgets.QVBoxLayout()
    horizontal_layout = QtWidgets.QHBoxLayout()
    horizontal_layout.addWidget(start_btn)
    horizontal_layout.addWidget(stop_btn)

    vertical_layout.addWidget(image_viewer)
    vertical_layout.addLayout(horizontal_layout)
    vertical_layout.addWidget(status_widget)

    vertical_layout.setAlignment(QtCore.Qt.AlignHCenter)

    # TODO. this widget will be used at main dashboard dialog or window
    # hide <-> show
    layout_widget = QtWidgets.QWidget()
    layout_widget.setLayout(vertical_layout)

    main_window = QtWidgets.QMainWindow()
    # main_window.setStyleSheet("background-color:white;")
    main_window.setFixedSize(640 + 100, 480 + 100)
    main_window.setCentralWidget(layout_widget)
    main_window.setWindowTitle("Video Capture Widget")
    main_window.show()
    sys.exit(app.exec_())