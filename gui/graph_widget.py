###################################################################
#                                                                 #
#                     PLOTTING A LIVE GRAPH                       #
#                  ----------------------------                   #
#            EMBED A MATPLOTLIB ANIMATION INSIDE YOUR             #
#            OWN GUI!                                             #
#                                                                 #
###################################################################


import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib import pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import time
import threading
import matplotlib
from datetime import datetime
import pandas as pd

matplotlib.use("Qt5Agg")


class CustomFigCanvas(FigureCanvas, TimedAnimation):
    def __init__(self,
                 label="falling",
                 color=None):

        self.addedData = {}
        self.label = label
        self.color = color

        # The data
        self.xlim = 100
        self.n = np.linspace(0, self.xlim - 1, self.xlim)
        self.y = {label: (self.n * 0.0)}

        # total data of graph
        graph_data = pd.DataFrame(self.y).reset_index()

        # The window
        self.fig = Figure(figsize=(10, 7), facecolor="#323232", dpi=100)
        self.fig.subplots_adjust(left=0, bottom=0, right=1,
                                 top=1, wspace=0, hspace=0)
        self.ax1 = self.fig.add_subplot(111)
        # self.ax1 = plt.axes([0.0, 0.0, 1.0, 1.0])

        # plot multiple lines
        axes = graph_data.plot(x="index", y=[label],
                               ax=self.ax1, lw=3, c=color)

        # remove legend
        axes.get_legend().remove()
        # self.ax1.legend(loc="upper left", facecolor="#323232",
        #                 labelcolor='linecolor', frameon=False)

        self.lines = axes.lines

        # self.ax1 settings
        self.ax1.grid(True)
        self.ax1.xaxis.label.set_color('white')
        self.ax1.yaxis.label.set_color('white')
        self.ax1.set_xticklabels([])
        # self.ax1.set_yticklabels([])
        # self.ax1.set_yticks([])

        self.ax1.tick_params(axis='x', colors='white')
        self.ax1.set(frame_on=False)

        self.ax1.set_xlim(0, self.xlim - 1)
        self.ax1.set_ylim(0, 1.0)

        FigureCanvas.__init__(self, self.fig)
        TimedAnimation.__init__(self, self.fig, interval=50, blit=True)

    def new_frame_seq(self):
        return iter(range(self.n.size))

    def _init_draw(self):
        for l in self.lines:
            l.set_data([], [])

    def addData(self, res):
        # TODO. multiple values not scalar
        self.addedData.update(res)

    def _step(self, *args):
        # Extends the _step() method for the TimedAnimation class.
        try:
            TimedAnimation._step(self, *args)
        except Exception as e:
            self.abc += 1
            print(str(self.abc))
            TimedAnimation._stop(self)
            pass

    def _draw_frame(self, framedata):

        anim_artists = []
        is_new = len(self.addedData.keys()) > 0

        yvals = self.y[self.label]
        if is_new:
            yvals = np.roll(yvals, -1)
            yvals[-1] = self.addedData[self.label]
            # update self.y[self.label]
            self.y[self.label] = yvals

        # if valid new data is given
        graph_data = pd.DataFrame(self.y).values
        margin = 2
        for ix, line in enumerate(self.lines):
            yvals = graph_data[:, ix]
            # print(yvals)
            line.set_data(
                self.n[0:self.n.size - margin], yvals[0:self.n.size - margin])
            anim_artists.append(line)

        self._drawn_artists = anim_artists

        # re-initialize data
        self.addedData = {}


# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class Communicate(QtCore.QObject):
    data_signal = QtCore.pyqtSignal(object)


def dataSendLoop(addData_callbackFunc):
    # Setup the signal-slot mechanism.
    mySrc = Communicate()
    mySrc.data_signal.connect(addData_callbackFunc)

    # Simulate some data
    n = np.linspace(0, 499, 500)
    y = 50 + 25 * (np.sin(n / 8.3)) + 10 * \
        (np.sin(n / 7.5)) - 5 * (np.sin(n / 1.5))
    i = 0

    while(True):
        if(i > 499):
            i = 0
        time.sleep(0.1)
        mySrc.data_signal.emit(y[i])  # <- Here you emit a signal!
        i += 1


def start_graph_worker(target, callbacks):
    # Add the callbackfunc to ..
    graph_worker = threading.Thread(
        name='graph_worker', target=target, daemon=True, args=callbacks)
    graph_worker.start()

    return graph_worker
