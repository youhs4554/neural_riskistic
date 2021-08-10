import sys
from PyQt5.QtGui import QIcon
from video_widget import VideoWidget
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QAction, QDialog, QApplication, QLabel, QLineEdit, QMainWindow, QStackedWidget
from PyQt5.uic import loadUi
import pyrebase
from dotenv import dotenv_values
import time


def releaseCameraResource(func):
    def wrapper_fn(self):
        func(self)
        if getattr(self, "video_widget", None) is not None:
            self.video_widget.video_worker.flag = 1
            time.sleep(0.5)
            del self.video_widget

    return wrapper_fn


class MainWidget(QtWidgets.QStackedWidget):
    def __init__(self, dialog, size=(480, 640), enabled=True):
        super().__init__()
        self.init_ui(dialog, size, enabled)

    def init_ui(self, dialog, size, enabled):
        dialog_instance = dialog()
        self.setFixedSize(*size)
        self.addWidget(dialog_instance)
        self.center()
        if enabled:
            self.show()

    def center(self):
        # geometry of the main window
        qr = self.frameGeometry()

        # center point of screen
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()

        # move rectangle's center point to screen's center point
        qr.moveCenter(cp)

        # top left of rectangle becomes top left of window centering it
        self.move(qr.topLeft())


class Login(QDialog):
    def __init__(self):
        super(Login, self).__init__()
        loadUi("ui_files/login.ui", self)
        self.loginbutton.clicked.connect(self.loginfunction)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.createaccbutton.clicked.connect(self.gotocreate)
        self.invalid.setVisible(False)

    def loginfunction(self):
        email = self.email.text()
        password = self.password.text()
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            print("Login Success!")
            self.authenticated = True
            # open dashboard window
            self.openDashboard()
        except:
            self.invalid.setVisible(True)

    def gotocreate(self):
        createacc = CreateAcc()
        widget.addWidget(createacc)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDashboard(self):
        # hide parent widget
        self.parent().hide()
        # open main app
        win.show()

    def closeEvent(self, event):
        if not self.authenticated:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.loginfunction()
        elif not event.key() == QtCore.Qt.Key_Escape:
            super(Login, self).keyPressEvent(event)


class CreateAcc(QDialog):
    def __init__(self):
        super(CreateAcc, self).__init__()
        loadUi("ui_files/createacc.ui", self)
        self.signupbutton.clicked.connect(self.createaccfunction)
        self.canclebutton.clicked.connect(self.gotologin)
        self.password.setEchoMode(QLineEdit.Password)
        self.confirmpass.setEchoMode(QLineEdit.Password)
        self.invalid.setVisible(False)

    def createaccfunction(self):
        email = self.email.text()
        password = self.password.text()
        confirmpass = self.confirmpass.text()
        if (email and password and confirmpass) == '':
            return

        if password == confirmpass:
            password = self.password.text()

            try:
                # creat accout
                auth.create_user_with_email_and_password(email, password)
                # if successfully create account -> go to login window
                login = Login()
                widget.addWidget(login)
                widget.setCurrentIndex(widget.currentIndex() + 1)
            except:
                # else invalid message shows up
                self.invalid.setVisible(True)
                self.invalid.setText("existing email")

        else:
            self.invalid.setVisible(True)
            self.invalid.setText("password is not matched")

    def gotologin(self):
        login = Login()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)


class MainApp(QMainWindow):
    def __init__(self, enabled=True):
        super().__init__()
        self.date = QtCore.QDateTime.currentDateTime()
        self.initUI(enabled)

    def initUI(self, enabled):
        self.homeAction = QAction(QIcon('./images/home_icon.png'),
                                  'Go to dashboard home', self)
        self.homeAction.triggered.connect(self.show_Home)
        self.homeAction.setCheckable(True)

        self.startAction = QAction(
            QIcon('./images/activity_icon.png'), 'Run Activity Test', self)
        self.startAction.triggered.connect(self.start_ActivityTest)
        self.startAction.setCheckable(True)

        self.gaitAction = QAction(QIcon('./images/gait_icon.png'),
                                  'Run Gait Test', self)
        self.gaitAction.triggered.connect(self.start_GaitTest)
        self.gaitAction.setCheckable(True)

        self.exitAction = QAction(QIcon("./images/exit_icon.png"),
                                  'Exit client and return to login window!', self)
        self.exitAction.triggered.connect(self.exit_App)
        self.statusBar().showMessage(self.date.toString(QtCore.Qt.DefaultLocaleLongDate))

        self.toolbar = self.addToolBar("side-banner")
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)
        self.toolbar.addAction(self.homeAction)
        self.toolbar.addAction(self.startAction)
        self.toolbar.addAction(self.gaitAction)
        self.toolbar.addAction(self.exitAction)
        self.toolbar.setIconSize(QtCore.QSize(64, 64))

        self.toolbar.setStyleSheet(
            "QToolButton:hover {background-color:lightgray} QToolButton:checked { border : 10px solid yellow }")

        self.setWindowTitle('Neural Riskistic App')

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.dashExample = QLabel(self)
        self.dashExample.resize(640 + 250, 480 + 250)

        # dummy dashboard example image
        self.dashExample.setStyleSheet(
            "image:url(./images/dashboard_example.png)")

        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()

        # resize and centerize
        self.resize(screen.width(), screen.height())
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)

        # initial fallback
        self.show_Home()

        if enabled:
            self.show()

    def uncheck_toolbar(self):
        self.homeAction.setChecked(False)
        self.startAction.setChecked(False)
        self.gaitAction.setChecked(False)

    @releaseCameraResource
    def show_Home(self):
        print("show_Home!!!")

        self.uncheck_toolbar()
        self.homeAction.setChecked(True)

        self.central_widget.addWidget(self.dashExample)
        self.central_widget.setCurrentWidget(self.dashExample)

    def start_ActivityTest(self):
        print("start_ActivityTest!!!")

        if getattr(self, "video_widget", None) is not None:
            self.video_widget.video_worker.flag = 1
            time.sleep(1)
            del self.video_widget

        self.uncheck_toolbar()
        self.startAction.setChecked(True)

        self.video_widget = VideoWidget(self)
        self.central_widget.addWidget(self.video_widget)
        self.central_widget.setCurrentWidget(self.video_widget)

    def start_GaitTest(self):
        print("start_GaitTest!!!")
        if getattr(self, "video_widget", None) is not None:
            self.video_widget.video_worker.flag = 1
            time.sleep(1)
            del self.video_widget

        self.uncheck_toolbar()
        self.gaitAction.setChecked(True)

        # TODO. embed video widget for gait analysis
        self.video_widget = VideoWidget(self)
        self.central_widget.addWidget(self.video_widget)
        self.central_widget.setCurrentWidget(self.video_widget)

    @releaseCameraResource
    def exit_App(self):
        self.central_widget.addWidget(self.dashExample)
        self.central_widget.setCurrentWidget(self.dashExample)
        self.uncheck_toolbar()
        self.homeAction.setChecked(True)
        self.close()

        # return to login widget
        login = Login()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        widget.show()


if __name__ == "__main__":
    # firebase setup
    firebaseConfig = dotenv_values(".env")
    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()

    app = QApplication(sys.argv)
    widget = MainWidget(Login, size=(480, 640))
    win = MainApp(enabled=False)
    sys.exit(app.exec_())
