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
import matplotlib.pyplot as plt

from pymeasure.display.Qt import QtGui
from pymeasure.display.windows import ManagedWindow

from pymeasure.experiment import Procedure, Results
from pymeasure.experiment import (FloatParameter, BooleanParameter,
                                  ListParameter)
from pymeasure.experiment.parameters import Parameter
from pymeasure.log import console_log

from pymeasure.experiment.results import unique_filename

from ongpym.instruments.keysight.n7744c import N7744C
from ongpym.instruments.keysight.n7776c import N7776C
from ..config import ADDRESS_N7744C, ADDRESS_N7776C, PATH_TRASH


sys.modules['cloudpickle'] = None
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class swept_transmission_experiment(Procedure):
    # Parameter definition
    # Automatic gain and range setting
    tau_avg = FloatParameter('Averaging Time', default=1e-6,
                             minimum=1e-6, maximum=1, units='s')

    power_range = ListParameter('Power Range',
                                choices=[-30, -20, -10, 0, 10],
                                units='dBm', default=-30)
    power_unit = ListParameter('Power Unit', choices=['dBm', 'W'],
                               default='dBm')

    auto_range = BooleanParameter('Auto Range', default=False)
    auto_gain = BooleanParameter('Auto Gain', default=False)
    sweep_step = FloatParameter('Trigger Stepsize', default=1, units='pm')
    sweep_speed = ListParameter('Sweep Speed',
                                choices=[0.5, 1, 2, 5, 10, 20, 40, 50,
                                         80, 100, 150, 160, 200],
                                default=0.5, units='nm/s')
    wl_start = FloatParameter('Start Wavelength', default=1559,
                              units='nm', minimum=1450, maximum=1640)
    wl_stop = FloatParameter('End Wavelength', default=1560,
                             units='nm', minimum=1450, maximum=1640)

    laser_power = FloatParameter('Laser Power', default=10, units='dBm')

    channel = ListParameter('Channel', choices=['CH1', 'CH2', 'CH3', 'CH4'],
                            default='CH1')

    directory = Parameter('', default='empty')
    plotting = BooleanParameter('Save Plot', default=False)
    saving = BooleanParameter('Save Data', default=False)
    filename = Parameter('Filename', default='SweptTransmission')

    DATA_COLUMNS = ['Wavelength [nm]', 'Power']

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

        self.chcurr.power_range = self.power_range

        # Trigger
        self.chcurr.trigger_input_setting = 'SME'

        log.info('Basic Setup of '+str(self.channel)+' completed.')
        self.emit('progress', 10)

        # Laser Setup
        self.laser = N7776C(ADDRESS_N7776C)
        self.laser.reset()

        self.laser.output = 1
        j = 0
        while not self.laser.output == 1:
            if j > 10:
                log.info('Laser Output Not Enabled. Abort.')
            sleep(1)
            j += 1
            if self.should_stop():
                break

        self.laser.trigger_out = 'stf'
        self.laser.trigger_in = 'ign'

        self.laser.wl_start = self.wl_start
        self.laser.wl_stop = self.wl_stop
        self.laser.sweep_step = self.sweep_step*1e-3
        self.laser.sweep_speed = self.sweep_speed
        self.laser.sweep_mode = 'cont'

        self.laser.wl_logging = 1

        self.laser.output_power_unit = 0
        self.laser.output_power = self.laser_power

        log.info('Setup of N7776C Laser Source completed.')

        # Logging setup
        self.chcurr.setup_logging(N=min(int(self.laser.sweep_points), 1000000),
                                  tau_avg=self.tau_avg)

        log.info('Setup Logging for swept transmission measurement. \
                 Ready to sweep.')
        self.emit('progress', 20)

    def execute(self):
        log.info('Execute')
        # Start Logging
        self.chcurr.start_logging()
        log.info('Logging Started.')

        self.laser.sweep = 1

        while self.laser.sweep == 1:
            log.info('Sweep in progress.')
            if self.should_stop():
                break
            sleep(1)

        pm_data = self.chcurr.get_result()
        wl_data = self.laser.get_wl_data()
        self.emit('progress', 70)
        # Emit data to result
        for i in range(len(pm_data)):
            data = {'Wavelength [nm]': wl_data[i],
                    self.DATA_COLUMNS[1]: pm_data[i]}
            self.emit('results', data)
            if self.should_stop():
                break
        log.info('Results successfully obtained.')
        self.emit('progress', 90)

        if self.plotting:
            log.info('Plotting in progress.')
            fig, ax = plt.subplots()
            ax.plot(wl_data, pm_data)
            ax.set_xlabel(self.DATA_COLUMNS[0])
            ax.set_ylabel(self.DATA_COLUMNS[1])
            fig.savefig(self.directory+'/'+self.filename+'_PLOT.png')

        self.emit('progress', 100)

    def shutdown(self):
        self.laser.output = 0
        self.pm.close()
        self.laser.close()
        log.info('Shutting Down.')


class swept_transmission_interface(ManagedWindow):
    def __init__(self):
        super(swept_transmission_interface, self).__init__(
            procedure_class=swept_transmission_experiment,
            inputs=['tau_avg', 'power_range', 'auto_gain', 'auto_range',
                    'power_unit', 'channel', 'wl_start', 'wl_stop',
                    'sweep_step', 'sweep_speed', 'laser_power', 'plotting',
                    'saving', 'filename'],
            displays=['tau_avg', 'sweep_speed', 'sweep_step', 'filename',
                      'wl_start', 'wl_stop'],
            x_axis='Wavelength [nm]',
            y_axis='Power',
            directory_input=True,
            sequencer=True)

        self.setWindowTitle('Swept Wavelength Measurement with \
                            N7776C and N7744C')

    def queue(self, *, procedure=None):
        directory = self.directory
        if procedure is None:
            procedure = self.make_procedure()

        if not procedure.saving:
            directory = PATH_TRASH+"\\.trash"
        elif directory == '':
            directory = PATH_TRASH

        procedure.directory = directory
        filename = procedure.filename.replace('.csv', '')
        procedure.filename = filename

        while (procedure.filename+'.csv') in os.listdir(directory):
            log.info('File already exists. Giving unique filename.')
            procedure.filename = \
                unique_filename(directory,
                                prefix=filename.replace('.csv', '')+'_')
            filename = procedure.filename

        dirfilename = os.path.join(directory, filename)

        results = Results(procedure, dirfilename.replace('.csv', '')+'.csv')
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)


if __name__ == "__main__":
    console_log(log)
    app = QtGui.QApplication(sys.argv)
    window = swept_transmission_interface()
    window.show()
    sys.exit(app.exec_())
