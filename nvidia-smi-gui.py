#!/usr/bin/python3

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QWidget
import threading
import time

import sys
import os
import io
import pty
import os

from subprocess import Popen, PIPE, STDOUT 

# nvidia-smi --query-gpu=index,count,name,uuid,memory.used,memory.total,temperature.gpu,power.draw --format=csv,noheader,nounits -lms 500
# nvidia-smi --query-compute-apps=gpu_uuid,pid,name,used_memory --format=csv,noheader,nounits -lms 500


is_running = False


def res(res_name):
    _script_path, _script_name = os.path.split(__file__)
    _resource_folder = os.path.join(_script_path, "resources")
    return os.path.join(_resource_folder, res_name)


class GPUInfoPanel(QWidget):
    
    def __init__(self, window_name="", *args, **kwargs):
        super(GPUInfoPanel, self).__init__(*args, **kwargs)

        self.setObjectName("GPU_PNL")
        self.setWindowTitle(window_name)
        self.setFixedSize(500, 146)

        self.padding_top = 10
        self.padding_left = 10
        self.padding_right = 10
        self.padding_bottom = 10

        self.margin = 10

        self.lbl_gpumodel = QtGui.QLabel("Graphics Device", self)
        self.lbl_gpuid = QtGui.QLabel("#0", self)
        self.lbl_pcibusid = QtGui.QLabel("bus: 00000000:00:00.0", self)
        
        self.lbl_temp = QtGui.QLabel("37deg", self)
        self.lbl_fan = QtGui.QLabel("20%", self)
        self.lbl_utilization = QtGui.QLabel("78%", self)
        self.lbl_clock = QtGui.QLabel("679MHz", self)
        
        self.lbl_mem_used = QtGui.QLabel("3000M", self)
        self.sep_mem = QtGui.QFrame(self)
        self.lbl_mem_total = QtGui.QLabel("8110M", self)
        
        self.lbl_power_draw = QtGui.QLabel("37W", self)
        self.sep_power = QtGui.QFrame(self)
        self.lbl_power_limit = QtGui.QLabel("180W", self)
        
        self.progress_mem = QtGui.QProgressBar(self)
        self.progress_power = QtGui.QProgressBar(self)
        self.lbl_mem_percentage = QtGui.QLabel("46%", self)
        self.lbl_power_percentage = QtGui.QLabel("27%", self)
        
        self.icon_temp = QtGui.QPushButton("", self)
        self.icon_fan = QtGui.QPushButton("", self)
        self.icon_utilization = QtGui.QPushButton("", self)
        self.icon_clock = QtGui.QPushButton("", self)
        self.icon_mem = QtGui.QPushButton("", self)
        self.icon_power = QtGui.QPushButton("", self)

        self.sep_panel = QtGui.QWidget(self)

        self.connect(self, QtCore.SIGNAL("SIGNAL_UPDATE"), self.update_info)
        self.init_ui()
        
    def init_ui(self):

        ## Self geometry
        self.setFixedSize(500, 146)
        self.setStyleSheet(
            "QWidget#GPU_PNL {"
            "   background-color: white;"
            "}")

        # btn_connect geometry
        ## lbl_gpumodel geometry
        self.lbl_gpumodel.setObjectName("lbl_gpumodel")
        self.lbl_gpumodel.setGeometry(self.padding_left, self.padding_top, 200, 40)
        self.lbl_gpumodel.setStyleSheet(
            "QLabel#lbl_gpumodel {"
            "   font-size: 26px; "
            "   qproperty-alignment: 'AlignVCenter | AlignLeft';"
            "}")

        ## lbl_gpuid geometry
        self.lbl_gpuid.setObjectName("lbl_gpuid")
        self.lbl_gpuid.setGeometry(
            self.lbl_gpumodel.x(),
            self.lbl_gpumodel.y() + self.lbl_gpumodel.height(),
            40, 10
        )
        self.lbl_gpuid.setStyleSheet(
            "QLabel#lbl_gpuid {"
            "   font-size: 12px;"
            "   qproperty-alignment: 'AlignVCenter | AlignLeft';"
            "}"
        )

        ## lbl_pcibusid
        self.lbl_pcibusid.setObjectName("lbl_pcibusid")
        self.lbl_pcibusid.setGeometry(
            self.lbl_gpuid.x() + self.lbl_gpuid.width(), self.lbl_gpumodel.y() + self.lbl_gpumodel.height(),
            self.lbl_gpumodel.width() - 40, 10
        )
        self.lbl_pcibusid.setStyleSheet(
            "QLabel#lbl_pcibusid {"
            "   font-size: 12px;"
            "   qproperty-alignment: 'AlignVCenter | AlignLeft';"
            "}"
        )

        ## Fan indicator related widgets:
        # lbl_fan geometry
        self.lbl_fan.setObjectName("lbl_fan")
        self.lbl_fan.setGeometry(
            self.width() - self.padding_right - 80, self.padding_top,
            70, 24
        )
        # icon_fan geometry
        self.icon_fan.setObjectName("icon_fan")
        self.icon_fan.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon_fan.setGeometry(
            self.lbl_fan.x() - self.margin - 24, self.lbl_fan.y(),
            24, 24
        )
        self.icon_fan.setStyleSheet(
            "QPushButton#icon_fan{"
            "   border-width: 1px;"
            "   border-color: #aaa;"
            "   border-style: none;"
            "   background-color: none;"
            "}")

        ## Clock indicator related widgets:
        # lbl_clock geometry
        self.lbl_clock.setObjectName("lbl_clock")
        self.lbl_clock.setGeometry(
            self.lbl_fan.x(), self.lbl_fan.y() + self.lbl_fan.height() + self.margin,
            self.lbl_fan.width(), self.lbl_fan.height()
        )
        # icon_clock geometry
        self.icon_clock.setObjectName("icon_clock")
        self.icon_clock.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon_clock.setGeometry(
            self.lbl_clock.x() - self.margin - 24, self.lbl_clock.y(),
            self.icon_fan.width(), self.icon_fan.height()
        )
        self.icon_clock.setStyleSheet(
            "QPushButton#icon_clock{"
            "   border-width: 1px;"
            "   border-color: #aaa;"
            "   border-style: solid;"
            "   background-color: white;"
            "}")

        ## Temperature indicator related widgets (snap left to Fan indicator)

        # lbl_temp geometry
        self.lbl_temp.setObjectName("lbl_temp")
        self.lbl_temp.setGeometry(
            self.icon_fan.x() - self.margin - self.lbl_fan.width(), self.lbl_fan.y(),
            self.lbl_fan.width(), self.lbl_fan.height()
        )

        # icon_temp geometry
        self.icon_temp.setObjectName("icon_temp")
        self.icon_temp.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon_temp.setGeometry(
            self.lbl_temp.x() - self.margin - self.icon_fan.width(), self.lbl_temp.y(),
            self.icon_fan.width(), self.icon_fan.height()
            )
        self.icon_temp.setStyleSheet(
            "QPushButton#icon_temp{"
            "   border-width: 1px;"
            "   border-color: #aaa;"
            "   border-style: none;"
            "   background-color: none;"
            "}")

        ## Utilization indicator related widgets (snap left to Clock indicator)
        # lbl_utilization geometry
        self.lbl_utilization.setObjectName("lbl_utilization")
        self.lbl_utilization.setGeometry(
            self.icon_clock.x() - self.margin - self.lbl_clock.width(), self.lbl_clock.y(),
            self.lbl_fan.width(), self.lbl_fan.height()
        )

        # icon_utilization geometry
        self.icon_utilization.setObjectName("icon_utilization")
        self.icon_utilization.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon_utilization.setGeometry(
            self.lbl_utilization.x() - self.margin - self.icon_fan.width(), self.lbl_utilization.y(),
            self.icon_fan.width(), self.icon_fan.height()
            )
        self.icon_utilization.setStyleSheet(
            "QPushButton#icon_utilization{"
            "   border-width: 1px;"
            "   border-color: #aaa;"
            "   border-style: none;"
            "   background-color: none;"
            "}")

        ## Memory Indicator bar:
        # mem indicator icon geometry
        self.icon_mem.setObjectName("icon_mem")
        self.icon_mem.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon_mem.setGeometry(
            self.padding_left, self.icon_utilization.y() + self.icon_utilization.height() + self.margin,
            24, 24
        )
        self.icon_mem.setStyleSheet(
            "QPushButton#icon_mem{"
            "   border-width: 1px;"
            "   border-color: #aaa;"
            "   border-style: none;"
            "   background-color: none;"
            "}")

        # mem used label geometry
        self.lbl_mem_used.setObjectName("lbl_mem_used")
        self.lbl_mem_used.setGeometry(
            self.icon_mem.x() + self.icon_mem.width() + self.margin,
            self.icon_mem.y(),
            50,
            self.icon_mem.height() // 2,
        )
        self.lbl_mem_used.setStyleSheet(
            "QLabel#lbl_mem_used{"
            "   font-size:10px;"
            "   qproperty-alignment: 'AlignVCenter | AlignCenter';"
            "}"
        )

        # mem seperator
        self.sep_mem.setObjectName("sep_mem")
        self.sep_mem.setGeometry(
            self.lbl_mem_used.x(), self.lbl_mem_used.y() + self.lbl_mem_used.height() - 1,
            self.lbl_mem_used.width(), 1
        )
        self.sep_mem.setFrameShape(QtGui.QFrame.HLine)

        # mem total label geometry
        self.lbl_mem_total.setObjectName("lbl_mem_total")
        self.lbl_mem_total.setGeometry(
            self.lbl_mem_used.x(),
            self.lbl_mem_used.y() + self.lbl_mem_used.height(),
            self.lbl_mem_used.width(),
            self.icon_mem.height() // 2,
        )
        self.lbl_mem_total.setStyleSheet(
            "QLabel#lbl_mem_total{"
            "   font-size:10px;"
            "   qproperty-alignment: 'AlignVCenter | AlignCenter';"
            "}"
        )

        # mem percentage:
        self.lbl_mem_percentage.setObjectName("lbl_mem_percentage")
        self.lbl_mem_percentage.setGeometry(
            self.width() - self.padding_right - 30,
            self.icon_mem.y(),
            30, self.icon_mem.height()
        )
        self.lbl_mem_percentage.setStyleSheet(
            "QLabel#lbl_mem_percentage{"
            "   qproperty-alignment: 'AlignVCenter | AlignRight';"
            "}"
        )

        # mem usage bar
        self.progress_mem.setObjectName("progress_mem")
        self.progress_mem.setTextVisible(False)
        self.progress_mem.setGeometry(
            self.lbl_mem_used.x() + self.lbl_mem_used.width() + self.margin,
            self.lbl_mem_used.y(),
            self.width() - self.lbl_mem_used.x() - self.lbl_mem_used.width() - self.margin - self.lbl_mem_percentage.width() - self.margin - self.padding_left,
            self.icon_mem.height()
        )
        self.progress_mem.setStyleSheet(
            "QProgressBar#progress_mem {"
            "   background-color: white;"
            "}"
        )

        ## Power Indicator bar:
        # power indicator icon geometry
        self.icon_power.setObjectName("icon_power")
        self.icon_power.setFocusPolicy(QtCore.Qt.NoFocus)
        self.icon_power.setGeometry(
            self.icon_mem.x(), self.icon_mem.y() + self.icon_mem.height() + self.margin,
            self.icon_mem.width(), self.icon_mem.height()
        )
        self.icon_power.setStyleSheet(
            "QPushButton#icon_power{"
            "   border-width: 1px;"
            "   border-color: #aaa;"
            "   border-style: none;"
            "   background-color: none;"
            "}")

        # power draw label geometry
        self.lbl_power_draw.setObjectName("lbl_power_draw")
        self.lbl_power_draw.setGeometry(
            self.icon_power.x() + self.icon_power.width() + self.margin,
            self.icon_power.y(),
            self.lbl_mem_used.width(),
            self.icon_power.height() // 2,
        )
        self.lbl_power_draw.setStyleSheet(
            "QLabel#lbl_power_draw{"
            "   font-size:10px;"
            "   qproperty-alignment: 'AlignVCenter | AlignCenter';"
            "}"
        )

        # power seperator
        self.sep_power.setObjectName("sep_power")
        self.sep_power.setGeometry(
            self.lbl_power_draw.x(), self.lbl_power_draw.y() + self.lbl_power_draw.height() - 1,
            self.lbl_power_draw.width(), 1
        )
        self.sep_power.setFrameShape(QtGui.QFrame.HLine)

        # power limit label geometry
        self.lbl_power_limit.setObjectName("lbl_power_limit")
        self.lbl_power_limit.setGeometry(
            self.lbl_power_draw.x(),
            self.lbl_power_draw.y() + self.lbl_power_draw.height(),
            self.lbl_power_draw.width(),
            self.icon_power.height() // 2,
        )
        self.lbl_power_limit.setStyleSheet(
            "QLabel#lbl_power_limit{"
            "   font-size:10px;"
            "   qproperty-alignment: 'AlignVCenter | AlignCenter';"
            "}"
        )

        # power percentage:
        self.lbl_power_percentage.setObjectName("lbl_power_percentage")
        self.lbl_power_percentage.setGeometry(
            self.width() - self.padding_right - self.lbl_mem_percentage.width(),
            self.icon_power.y(),
            self.lbl_mem_percentage.width(), self.icon_power.height()
        )
        self.lbl_power_percentage.setStyleSheet(
            "QLabel#lbl_power_percentage{"
            "   qproperty-alignment: 'AlignVCenter | AlignRight';"
            "}"
        )
        # power usage bar
        self.progress_power.setObjectName("progress_power")
        self.progress_power.setTextVisible(False)
        self.progress_power.setGeometry(
            self.lbl_power_draw.x() + self.lbl_power_draw.width() + self.margin,
            self.lbl_power_draw.y(),
            self.width() - self.lbl_power_draw.x() - self.lbl_power_draw.width() - self.margin - self.lbl_power_percentage.width() - self.margin - self.padding_left,
            self.icon_power.height()
        )
        self.progress_power.setStyleSheet(
            "QProgressBar#progress_power {"
            "   background-color: white;"
            "}"
        )

        ## Panel Seperator
        self.sep_panel.setObjectName("sep_panel")
        self.sep_panel.setGeometry(
            self.padding_left * 2, self.height() - 1,
            self.width() - 2 * self.padding_left - 2 * self.padding_right, 1
        )
        self.sep_panel.setStyleSheet(
            "QWidget#sep_panel{"
            "   background-color: #aaa;"
            "}"
        )

        ## Load images for each icon.
        self.icon_utilization.setIcon(QtGui.QIcon(res("gear.svg")))
        self.icon_utilization.setIconSize(self.icon_utilization.size())

        self.icon_mem.setIcon(QtGui.QIcon(res("ram.svg")))
        self.icon_mem.setIconSize(self.icon_mem.size())

        self.icon_fan.setIcon(QtGui.QIcon(res("fan.svg")))
        self.icon_fan.setIconSize(self.icon_fan.size())

        self.icon_temp.setIcon(QtGui.QIcon(res("thermometer.svg")))
        self.icon_temp.setIconSize(self.icon_temp.size())

        self.icon_clock.setIcon(QtGui.QIcon(res("wave.svg")))
        self.icon_clock.setIconSize(self.icon_clock.size())

        self.icon_power.setIcon(QtGui.QIcon(res("gauge.svg")))
        self.icon_power.setIconSize(self.icon_power.size())
        pass

    def move_to_center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def update_info(self, smi_data):

        ## Parse SMI_DATA and update interface.
        # headers = [
        #     "index",
        #     "count",
        #     "pci.bus_id",
        #     "name",
        #     "uuid",
        #     "memory.used",
        #     "memory.total",
        #     "temperature.gpu",
        #     "power.draw",
        #     "enforced.power.limit",
        #     "clocks.current.memory"
        # ]
        if "index" in smi_data:
            self.lbl_gpuid.setText("#" + smi_data["index"])

        if "pci.bus_id" in smi_data:
            self.lbl_pcibusid.setText("pci: " + smi_data["pci.bus_id"])

        if "name" in smi_data:
            self.lbl_gpumodel.setText(smi_data["name"])

        if "utilization.gpu" in smi_data:
            self.lbl_utilization.setText(smi_data["utilization.gpu"] + "%")

        if "clocks.current.memory" in smi_data:
            self.lbl_clock.setText(smi_data["clocks.current.memory"] + "MHz")

        if "memory.used" in smi_data:
            self.lbl_mem_used.setText(smi_data["memory.used"] + "M")

        if "memory.total" in smi_data:
            self.lbl_mem_total.setText(smi_data["memory.total"] + "M")

        if "memory.used" in smi_data and "memory.total" in smi_data:
            mem_used = float(smi_data["memory.used"])
            mem_total = float(smi_data["memory.total"])
            percentage = int(mem_used * 100 / mem_total)
            self.lbl_mem_percentage.setText(str(percentage) + "%")
            self.progress_mem.setValue(percentage)

        if "temperature.gpu" in smi_data:
            self.lbl_temp.setText(smi_data["temperature.gpu"] + "\u2103")
        else:
            self.lbl_temp.setText("N/A")

        if "fan.speed" in smi_data:
            if smi_data["fan.speed"].startswith("["):
                self.lbl_fan.setText("Passive Cooling")
            else:
                self.lbl_fan.setText(smi_data["fan.speed"] + "%")
        else:
            self.lbl_fan.setText("N/A")

        if "power.draw" in smi_data:
            self.lbl_power_draw.setText(smi_data["power.draw"] + "W")

        if "enforced.power.limit" in smi_data:
            self.lbl_power_limit.setText(smi_data["enforced.power.limit"] + "W")

        if "power.draw" in smi_data and "enforced.power.limit" in smi_data:
            draw = float(smi_data["power.draw"])
            limit = float(smi_data["enforced.power.limit"])
            percentage = int(draw * 100 / limit)
            self.lbl_power_percentage.setText(str(percentage) + "%")
            self.progress_power.setValue(percentage)

    def update_async(self, smi_data):
        self.emit(QtCore.SIGNAL("SIGNAL_UPDATE"), smi_data)


class MainWindow(QtGui.QWidget):
    def __init__(self, *args, window_name):
        super(MainWindow, self).__init__(*args)
        self.window_name = window_name
        self.panel_list = []

        self.connect(self, QtCore.SIGNAL("SIGNAL_ADDNEW"), self.add_new_panel)
        self.cond_pnl = threading.Condition()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.window_name)
        self.setFixedSize(500, 146)

        self.setObjectName("MainWindow")
        self.setStyleSheet(
            "QWidget#MainWindow {"
            "   background-color: white;"
            "}"
        )

        self.setWindowIcon(QtGui.QIcon(res("graphic-card.svg")))

    def add_new_panel(self):
        # print("[", threading.current_thread().name, "]", "acquiring cond...")
        self.cond_pnl.acquire()

        # print("[", threading.current_thread().name, "]", "creating panel")
        pnl = GPUInfoPanel(parent=self)
        pnl.show()
        panel_height = sum([p.height() for p in self.panel_list])
        self.panel_list.append(pnl)
        pnl.move(0, panel_height)
        self.setFixedSize(self.panel_list[0].width(), panel_height + pnl.height())

        self.move_to_center()

        # print("[", threading.current_thread().name, "]", "notifing ...")
        self.cond_pnl.notify_all()
        self.cond_pnl.release()
        # print("[", threading.current_thread().name, "]", "released.")

    def add_new_panel_async(self):
        # print("[", threading.current_thread().name, "]", "acquiring cond...")
        self.cond_pnl.acquire()

        # print("[", threading.current_thread().name, "]", "lock acquired, sending signal...")
        self.emit(QtCore.SIGNAL("SIGNAL_ADDNEW"))

        # print("[", threading.current_thread().name, "]", "waiting on condition")
        self.cond_pnl.wait()

        # print("[", threading.current_thread().name, "]", "wait ended.")

        return self.panel_list[-1]

    def move_to_center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    pass


def get_iostream(commandline):

    stdout_master, stdout_slave = pty.openpty()
    stderr_master, stderr_slave = pty.openpty()
    
    proc = Popen(commandline, stdin=PIPE, stdout=stdout_slave, stderr=stderr_slave, close_fds=True)
    
    pstdout = os.fdopen(stdout_master)
    pstderr = os.fdopen(stderr_master)
     
    return proc, pstdout, pstderr


def proc_smireader(fields, main_window, smi_stdout, proc):
    global is_running
    is_running = True
    
    while is_running:

        smi_line = smi_stdout.readline().strip()
        smi_data = {k: v for k, v in zip(fields, smi_line.split(", "))}

        idx = int(smi_data["index"])
        if idx >= len(main_window.panel_list):
            pnl = main_window.add_new_panel_async()
            pnl.update_async(smi_data)
        else:
            main_window.panel_list[idx].update_async(smi_data)

        # print("[", threading.current_thread().name, "]", "SMI-DATA:", smi_line)
    
    proc.kill()


def main():
    global is_running
    
    fields = [
        "index",
        "count",
        "pci.bus_id",
        "name",
        "uuid",
        "memory.used",
        "memory.total",
        "temperature.gpu",
        "power.draw",
        "enforced.power.limit",
        "clocks.current.memory",
        "fan.speed",
        "utilization.gpu"
        ""
    ]

    cmd_gpu_stat = ["nvidia-smi", "--query-gpu=" + ",".join(fields), "--format=csv,noheader,nounits", "-lms", "200"]
    proc_gpu_stat, gpu_stat, _ = get_iostream(cmd_gpu_stat)

    app = QApplication([""])
    mw = MainWindow(window_name="GPU Status")

    th = threading.Thread(target=proc_smireader, name="SMI-StdoutReader", args=(fields, mw, gpu_stat, proc_gpu_stat), daemon=True)
    th.start()
    mw.show()

    while True:
        app.processEvents()
        if not mw.isVisible():
            # app exit.
            break
        time.sleep(0.01)

    is_running = False
    th.join()


if __name__ == "__main__":
    main()

