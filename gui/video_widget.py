# 출처 - https://github.com/ddd4117/GUI/blob/master/src/camera_test.py
# 수정 - webnautes

import threading
from graph_widget import Communicate, CustomFigCanvas

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import cv2
import sys
sys.path.append("./grpc_test")
from grpc_test.torchserve_grpc_client import get_inference_stub, infer_image
import json
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
import time


class ShowVideo(QtCore.QObject):

    height = 480
    width = 640

    VideoSignal = QtCore.pyqtSignal(QtGui.QImage)

    def __init__(self, parent=None):
        super(ShowVideo, self).__init__(parent)

    def dataSendLoop(self, addData_callbackFunc):
        # Setup the signal-slot mechanism.
        mySrc = Communicate()
        mySrc.data_signal.connect(addData_callbackFunc)

        while(True):
            time.sleep(0.1)
            if self.riskVal is not None:
                # <- Here you emit a signal!
                mySrc.data_signal.emit(self.riskVal)
            if self.flag:
                break

    @QtCore.pyqtSlot()
    def startVideo(self):
        global image

        self.flag = 0
        self.riskVal = None
        camera = cv2.VideoCapture(0)

        ix = 0

        while camera.isOpened():
            ret, image = camera.read()
            image = cv2.resize(image, (self.width, self.height))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            prediction = infer_image(get_inference_stub(),
                                     "STCNet_8f_CesleaFDD6", image, ix)
            if prediction != "0" and ix % 1 == 0:
                riskVal = json.loads(prediction)["falling"]
                self.riskVal = riskVal

            qt_input_image = QtGui.QImage(
                image.data,
                self.width,
                self.height,
                image.strides[0],
                QtGui.QImage.Format_RGB888,
            )
            self.VideoSignal.emit(qt_input_image)
            if self.flag:
                break

            ix += 1
            loop = QtCore.QEventLoop()
            QtCore.QTimer.singleShot(25, loop.quit)  # 25 ms
            loop.exec_()

        loop.quit()
        camera.release()

    @QtCore.pyqtSlot()
    def stopVideo(self):
        self.flag = 1


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


class VideoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # setup thread
        self.video_worker = ShowVideo()
        self.worker_thread = QtCore.QThread(self)
        self.worker_thread.start()
        self.video_worker.moveToThread(self.worker_thread)

        # setup viewers
        self.image_viewer = ImageViewer(self)
        self.image_viewer.setFixedSize(640, 480)

        # connect signals
        self.video_worker.VideoSignal.connect(
            self.image_viewer.setImage)
        self.resultCanvas = CustomFigCanvas()

        self.start_btn = QtWidgets.QPushButton("Start", self)
        self.stop_btn = QtWidgets.QPushButton("Stop", self)

        self.start_btn.clicked.connect(self.video_worker.startVideo)
        self.stop_btn.clicked.connect(self.video_worker.stopVideo)
        self.start_btn.setIcon(self.start_btn.style().standardIcon(
            QtWidgets.QStyle.SP_MediaPlay))
        self.stop_btn.setIcon(self.stop_btn.style().standardIcon(
            QtWidgets.QStyle.SP_MediaStop))

        self.vertical_layout = QtWidgets.QVBoxLayout(self)
        self.horizontal_layout = QtWidgets.QHBoxLayout(self)
        self.horizontal_layout.addWidget(self.start_btn)
        self.horizontal_layout.addWidget(self.stop_btn)

        self.vertical_layout.addWidget(self.image_viewer)
        self.vertical_layout.addWidget(self.resultCanvas)
        self.vertical_layout.addLayout(self.horizontal_layout)

        self.vertical_layout.setAlignment(QtCore.Qt.AlignHCenter)

        # Add the callbackfunc to ..
        myDataLoop = threading.Thread(
            name='myDataLoop', target=self.video_worker.dataSendLoop, daemon=True, args=(self.addData_callbackFunc,))
        myDataLoop.start()

        # initial click after widgets are mounted
        self.start_btn.click()

    @QtCore.pyqtSlot(float)
    def addData_callbackFunc(self, value):
        # print("Add data: " + str(value))
        self.resultCanvas.addData(value)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    widget.setFixedSize(640 + 500, 480 + 500)

    vw = VideoWidget()
    widget.addWidget(vw)
    widget.show()
    sys.exit(app.exec_())
