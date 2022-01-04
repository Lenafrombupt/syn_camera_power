

import sys

from random import randint

from ongpym.experiments.powermeter_basic import powermeter_basic_interface
from ongpym.experiments.electrode_resistance import \
    electrode_resistance_interface
from ongpym.experiments.resonator_transmission import \
    transmission_interface
from ongpym.experiments.modulation_time_domain import \
    modulation_time_domain_interface
from ongpym.experiments.swept_transmission import \
    swept_transmission_interface
from ongpym.experiments.voltage_sequence_time_domain import \
    voltage_sequence_time_domain_interface

from PyQt5.QtWidgets import \
    QApplication, QPushButton, QLabel, QGridLayout, QWidget, QVBoxLayout
from PyQt5.QtGui import QFont


class AnotherWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Another Window % d" % randint(0, 100))
        layout.addWidget(self.label)
        self.setLayout(layout)


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.w = None  # No external window yet.
        self.layout = QGridLayout()

        self.title = QLabel('ONG PyMeasure Suite')
        self.setWindowTitle('ONG PyMeasure Suite')
        titleFont = QFont()
        titleFont.setBold(True)
        titleFont.setPointSize(14)
        self.title.setFont(titleFont)

        self.button1 = QPushButton('Power Meter Logger\n(Keysight N7744C)')
        self.button1.clicked.connect(self.pm_logger)
        self.button2 = QPushButton(
            'Resistance Measurement\n(Keysight E36106A)')
        self.button2.clicked.connect(self.res_meas)
        self.button3 = QPushButton(
            'Transmission Measurement\n(Toptica CTL + Tektronix MDO3052)')
        self.button3.clicked.connect(self.trans_meas)
        self.button4 = QPushButton(
            'Modulation in Time Domain\n(GWInstek AFG-2125 + \
            Tektronix MDO3052)')
        self.button4.clicked.connect(self.mod_time_domain)
        self.button5 = QPushButton(
            'Swept Transmission Measurement\n(Keysight N7776C + \
            Keysight N7744C)')
        self.button5.clicked.connect(self.swept_trans)
        self.button6 = QPushButton(
            'Voltage Sequence in Time Domain\n(Keysight E36106A + \
            Tektronix MDO3052)')
        self.button6.clicked.connect(self.v_seq_time_domain)

        self.layout.addWidget(self.title, 0, 1)
        self.layout.addWidget(self.button1, 1, 0)
        self.layout.addWidget(self.button2, 1, 1)
        self.layout.addWidget(self.button3, 1, 2)
        self.layout.addWidget(self.button4, 2, 0)
        self.layout.addWidget(self.button5, 2, 1)
        self.layout.addWidget(self.button6, 2, 2)

        self.layout.setVerticalSpacing(100)
        self.layout.setHorizontalSpacing(50)
        self.setLayout(self.layout)
        # self.resize(400,600)

    def pm_logger(self, checked):
        self.w = powermeter_basic_interface()
        self.w.show()

    def res_meas(self, checked):
        self.w = electrode_resistance_interface()
        self.w.show()

    def trans_meas(self, checked):
        self.w = transmission_interface()
        self.w.show()

    def mod_time_domain(self, checked):
        self.w = modulation_time_domain_interface()
        self.w.show()

    def swept_trans(self, checked):
        self.w = swept_transmission_interface()
        self.w.show()

    def v_seq_time_domain(self, checked):
        self.w = voltage_sequence_time_domain_interface()
        self.w.show()


app = QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec())
