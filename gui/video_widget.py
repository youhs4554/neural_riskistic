from functools import partial
import threading
from graph_widget import Communicate, CustomFigCanvas, start_graph_worker

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
import matplotlib.pyplot as plt

def inspect_camera():
    cam = cv2.VideoCapture(0)
    ret, _ = cam.read()
    return ret


def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
        RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)


class UpdatableLabelWidget(QtWidgets.QLabel):
    state_signal = QtCore.pyqtSignal(str)

    def __init__(self, result_canvas=None, parent=None, width=150, height=30):
        super(UpdatableLabelWidget, self).__init__(parent)
        self.result_canvas = result_canvas
        self.init_UI(width, height)

    def init_UI(self, width, height):
        self.setText("N/A")
        self.setFixedWidth(width)                            # +++
        self.setMinimumHeight(height)                          # +++
        self.adjustSize()
        self.setStyleSheet(f"color: white; font-size: 15pt")

    @QtCore.pyqtSlot(object)
    def update_text(self, value):
        # print("Add data: " + str(value))
        label = self.result_canvas.label
        rgb_code = tuple(int(255 * c) for c in self.result_canvas.color[:-1])
        message = "{}: {:4.2f}".format(
            label.capitalize(), value[label])
        self.setText(message)
        self.setStyleSheet(f"color: rgb{rgb_code}; font-size: 15pt")

    @QtCore.pyqtSlot(object)
    def update_fallRisk(self, value):
        # print("Add data: " + str(value))
        label = "falling"
        message = "Risk of falling: {:4.2f}".format(
            value[label])
        self.setText(message)
        # TODO if risk of falls goes up, change text color to red
        if value[label] > 0.8:
            color = "red"
        else:
            color = "white"
        self.setStyleSheet(f"color: {color}; font-size: 15pt")


class ShowVideo(QtCore.QObject):

    height = 480
    width = 640

    VideoSignal = QtCore.pyqtSignal(QtGui.QImage)
    mySrc = Communicate()

    def __init__(self, parent=None):
        super(ShowVideo, self).__init__(parent)

    def dataSendLoop(self, *callbacks):
        for cb in callbacks:
            # Setup the signal-slot mechanism.
            self.mySrc.data_signal.connect(cb)

        while(True):
            time.sleep(0.1)
            if self.results is not None:
                # <- Here you emit a signal!
                self.mySrc.data_signal.emit(self.results)
            if self.flag:
                break

    @QtCore.pyqtSlot()
    def startVideo(self, target, callbacks):
        # start graph_widget thread
        self.gworker = start_graph_worker(target=target,
                                          callbacks=callbacks)

        global image

        self.flag = 0
        self.results = None
        camera = cv2.VideoCapture(0)

        ix = 0

        while camera.isOpened():
            ret, image = camera.read()
            image = cv2.resize(image, (self.width, self.height))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            prediction = infer_image(get_inference_stub(),
                                     "STCNet_8f_CesleaFDD6", image, ix)
            if prediction != "0" and ix % 1 == 0:
                self.results = json.loads(prediction)

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
        self.gworker.join()


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

        self.resultCanvasWidgets = []
        self.labels = ["falling", "walking", "standing",
                       "background", "sleeping", "sitting"]

        cmap = get_cmap(len(self.labels) + 1)
        for i, lab in enumerate(self.labels):
            _canvas = CustomFigCanvas(lab, color=cmap(i))
            self.resultCanvasWidgets.append(_canvas)

        self.start_btn = QtWidgets.QPushButton("Start", self)
        self.stop_btn = QtWidgets.QPushButton("Stop", self)
        
        self.start_btn.setStyleSheet("background-color: lightgray")
        self.stop_btn.setStyleSheet("background-color: lightgray")

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        # video player widget
        self.widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        lbl_title = QtWidgets.QLabel("Camera Input")
        lbl_title.setStyleSheet(
            f"color: white; font-size: 32pt; font-weight: bold")
        lbl_title.adjustSize()
        lbl_title.setAlignment(QtCore.Qt.AlignCenter)
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        # label for risk of falls(=rof)
        lbl_rof = UpdatableLabelWidget(width=250, height=100)
        lbl_rof.setAlignment(QtCore.Qt.AlignCenter)

        qLabelUpdateCallbacks = []
        qLabelUpdateCallbacks.append(lbl_rof.update_fallRisk)

        self.widget.setLayout(layout)
        layout.addWidget(lbl_title)
        layout.addWidget(self.image_viewer)
        layout.addLayout(btn_layout)
        layout.addWidget(lbl_rof)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout().addWidget(self.widget)

        # graph widgets
        self.widget = QtWidgets.QWidget()
        # layout = QtWidgets.QVBoxLayout()
        layout = QtWidgets.QGridLayout()
        self.widget.setLayout(layout)
        for row, _canvas in enumerate(self.resultCanvasWidgets):
            layout.addWidget(_canvas, row, 0)
            qLabel = UpdatableLabelWidget(_canvas)
            qLabelUpdateCallbacks.append(qLabel.update_text)
            layout.addWidget(qLabel, row, 1)

        layout.setAlignment(QtCore.Qt.AlignHCenter)
        self.layout().addWidget(self.widget)

        self.layout().setAlignment(QtCore.Qt.AlignHCenter)

        if not inspect_camera():
            msg = QtWidgets.QMessageBox()
            msg.setStyleSheet("QLabel{width: 400px; font-size: 24px}")
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Camera Error")
            msg.setInformativeText('Camera is not found!')
            msg.setWindowTitle("Camera Error")
            msg.exec_()
            sys.exit(0)


        self.start_btn.clicked.connect(
            partial(self.video_worker.startVideo, self.video_worker.dataSendLoop, (self.addData_callbackFunc, *qLabelUpdateCallbacks)))
        self.stop_btn.clicked.connect(self.video_worker.stopVideo)
        self.start_btn.setIcon(self.start_btn.style().standardIcon(
            QtWidgets.QStyle.SP_MediaPlay))
        self.stop_btn.setIcon(self.stop_btn.style().standardIcon(
            QtWidgets.QStyle.SP_MediaStop))

        # initial click after widgets are mounted
        self.start_btn.click()

    @QtCore.pyqtSlot(object)
    def addData_callbackFunc(self, value):
        # print("Add data: " + str(value))
        for _canvas in self.resultCanvasWidgets:
            _canvas.addData(value)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    widget.setFixedSize(1920 - 100, 1080 - 100)

    vw = VideoWidget()
    widget.addWidget(vw)
    widget.show()
    sys.exit(app.exec_())
