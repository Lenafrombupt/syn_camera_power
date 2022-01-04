try:
    import ongpym
    del ongpym
except ImportError:
    from pathlib import Path
    file = Path(__file__). resolve()
    package_root_directory = str(file)[:str(file).find('ONGPyMeasureSuite')] \
        + 'ONGPyMeasureSuite'
    exec(open(str(package_root_directory)+'/initialize.py').read())

import os
import sys
import logging


from time import sleep
import numpy as np
import matplotlib.pyplot as plt


from pymeasure.display.Qt import QtGui
from pymeasure.display.windows import ManagedWindow

from pymeasure.experiment import Procedure, Results
from pymeasure.experiment import (IntegerParameter, FloatParameter,
                                  BooleanParameter, ListParameter)
from pymeasure.experiment.parameters import Parameter

from ongpym.instruments.keysight.n7744c import N7744C
from ..config import ADDRESS_N7744C, PATH_TRASH

sys.modules['cloudpickle'] = None
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class powermeter_basic_experiment(Procedure):
    # Parameter definition
    # Automatic gain and range setting
    auto_gain = BooleanParameter('Auto Gain', default=True)
    auto_range = BooleanParameter('Auto Range', default=False)

    tau_avg = FloatParameter('Averaging Time', default=1e-6,
                             minimum=1e-6, maximum=1, units='s')
    number = IntegerParameter('Number of Points', minimum=10,
                              maximum=1e6, default=1e5)

    power_range = ListParameter('Power Range',
                                choices=[-30, -20, -10, 0, 10],
                                units='dBm', default=-30)
    power_unit = ListParameter('Power Unit', choices=['dBm', 'W'],
                               default='dBm')

    channel = ListParameter('Channel', choices=['CH1', 'CH2', 'CH3', 'CH4'],
                            default='CH1')

    trigger = BooleanParameter('Trigger', default=False)

    directory = Parameter('', default='empty')
    saving = BooleanParameter('Save Data', default=False)
    filename = Parameter('Filename', default='TimeTrace')

    plotting = BooleanParameter('Plot Results', default=False)

    DATA_COLUMNS = ['Time [s]', 'Power']

    def startup(self):
        log.info('Startup')
        self.emit('progress', 10)
        self.pm = N7744C(ADDRESS_N7744C)
        log.info('N7744C Power Meter connected.')

        self.pm.reset()

        # Define the channel which was chosen
        self.chcurr = self.pm.ch1
        if self.channel == 'CH2':
            self.chcurr = self.pm.ch2
        elif self.channel == 'CH3':
            self.chcurr = self.pm.ch3
        elif self.channel == 'CH4':
            self.chcurr = self.pm.ch4

        # Setup the powermeter to these Settings
        self.chcurr.auto_gain = self.auto_gain
        self.chcurr.auto_range = self.auto_range
        if self.power_unit == 'dBm':
            self.pm.power_unit = 0

        else:
            self.pm.power_unit = 1

        if not self.auto_range:
            self.chcurr.power_range = self.power_range

        # Trigger
        if self.trigger:
            self.chcurr.trigger_input_setting = 'CME'
        else:
            self.chcurr.trigger_input_setting = 'IGN'

        log.info('Basic Setup of '+str(self.channel)+' completed.')

        # Logging setup
        self.chcurr.setup_logging(N=self.number, tau_avg=self.tau_avg)

        log.info('Setup Logging for '+str(self.number*self.tau_avg)
                 + 'seconds.')
        self.emit('progress', 10)

    def execute(self):
        log.info('Execute')
        # Start Logging
        self.chcurr.start_logging()
        log.info('Logging Started.')
        if not self.trigger:
            self.chcurr.write(':TRIG 1')

        while self.chcurr.in_progress():
            log.info('Logging in progress.')
            if self.should_stop():
                break
            sleep(1)

        pm_data = self.chcurr.get_result()
        tt = np.linspace(0, (self.number-1)*self.tau_avg, pm_data.shape[0])
        self.emit('progress', 70)

        # Emit data to result
        for i in range(len(pm_data)):
            data = {'Time [s]': tt[i], self.DATA_COLUMNS[1]: pm_data[i]}
            self.emit('results', data)
            if self.should_stop():
                break
        log.info('Results successfully obtained.')
        self.emit('progress', 90)

        if self.plotting:
            log.info('Plotting in progress.')
            fig, ax = plt.subplots()
            ax.plot(tt, pm_data)
            ax.set_xlabel(self.DATA_COLUMNS[0])
            ax.set_ylabel(self.DATA_COLUMNS[1])
            fig.savefig(self.directory+'/'+self.filename+'_PLOT.png')

        self.emit('progress', 100)

    def shutdown(self):
        self.pm.close()
        log.info('Shutting Down.')


class powermeter_basic_interface(ManagedWindow):

    def __init__(self):
        super(powermeter_basic_interface, self).__init__(
            procedure_class=powermeter_basic_experiment,
            inputs=['auto_gain', 'auto_range', 'tau_avg', 'number',
                    'power_range', 'power_unit', 'channel', 'trigger',
                    'plotting', 'saving', 'filename'],
            displays=['tau_avg', 'number'],
            x_axis='Time [s]',
            y_axis='Power',
            directory_input=True,
            sequencer=False)

        self.setWindowTitle('N7744C Power Meter Logger')

    def queue(self, *, procedure=None):
        directory = self.directory
        if procedure is None:
            procedure = self.make_procedure()

        if not procedure.saving:
            directory = PATH_TRASH + "\\.trash"
        elif directory == '':
            directory = PATH_TRASH

        procedure.directory = directory
        filename = procedure.filename

        while procedure.filename in os.listdir(directory):
            procedure.filename = procedure.filename+'_1'
            filename = procedure.filename

        dirfilename = os.path.join(directory, filename)
        print(dirfilename)
        results = Results(procedure, dirfilename)
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = powermeter_basic_interface()
    window.show()
    sys.exit(app.exec_())
