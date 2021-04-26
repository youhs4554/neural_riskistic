import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QLineEdit, QWidget
from PyQt5.uic import loadUi
import pyrebase

firebaseConfig = {
    "apiKey": "AIzaSyDdwuA19Lmdm6vHWNDel7cJM28Ff39os88",
    "authDomain": "auth-risk-f89e3.firebaseapp.com",
    "databaseURL": "",
    "projectId": "auth-risk-f89e3",
    "storageBucket": "auth-risk-f89e3.appspot.com",
    "messagingSenderId": "831873646665",
    "appId": "1:831873646665:web:c95e0f894a93f799747f98",
    "measurementId": "G-D7YEY21SDQ"
}

firebase = pyrebase.initialize_app(firebaseConfig)

auth = firebase.auth()


class MainWidget(QtWidgets.QStackedWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        mainwindow = Login()
        self.setFixedSize(480, 640)
        self.addWidget(mainwindow)
        self.center()
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
            # open dashboard window
            self.openDashboard()
        except:
            self.invalid.setVisible(True)

    def gotocreate(self):
        createacc = CreateAcc()
        widget.addWidget(createacc)
        widget.setCurrentIndex(widget.currentIndex()+1)

    def openDashboard(self):
        # hide parent widget
        self.parent().hide()
        # open dash board dialog
        dashboard = DashBoard()
        dashboard.exec_()


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
                widget.setCurrentIndex(widget.currentIndex()+1)
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
        widget.setCurrentIndex(widget.currentIndex()+1)


class ComponentsHandler():
    # component group1(video player)
    __components = {
        "1": ["start_btn", "stop_btn", "pause_btn", "video_plane"],
        "2": ["riskhistory", "gaithistory"]
    }

    @staticmethod
    def init_components(ui):
        n_mode = len(ComponentsHandler.__components.keys())
        for mode in range(1, n_mode+1):
            for compo in ComponentsHandler.get_components(mode):
                getattr(ui, compo).setVisible(False)

    @staticmethod
    def get_components(mode):
        return ComponentsHandler().__components[str(mode)]

    @staticmethod
    def show_components(ui, mode):
        # re-init componets
        ComponentsHandler.init_components(ui)

        for compo in ComponentsHandler.get_components(mode):
            getattr(ui, compo).setVisible(True)


class DashBoard(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("ui_files/dashboard.ui", self)
        self.setWindowTitle("Neural Riskistic Dashboard")
        self.setFixedSize(1920, 1080)

        # init components
        ComponentsHandler.init_components(self)

        self.clickme1.clicked.connect(self.show_comp1)
        self.clickme2.clicked.connect(self.show_comp2)

        # dummy dashboard example image
        self.dashExample.setStyleSheet(
            "image:url(./images/dashboard_example.png)")

    def show_comp1(self):
        print("clicked-btn1!!!")
        ComponentsHandler.show_components(self, mode=1)

    def show_comp2(self):
        print("clicked-btn2!!!")
        ComponentsHandler.show_components(self, mode=2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWidget()
    app.exec_()
