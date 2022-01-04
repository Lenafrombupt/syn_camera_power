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

from pymeasure.display.windows import ManagedWindow

from pymeasure.experiment import Procedure, Results
from pymeasure.experiment import (FloatParameter, BooleanParameter,
                                  ListParameter)
from pymeasure.experiment.parameters import Parameter
from pymeasure.experiment.results import unique_filename

from ..instruments.tektronix.mdo3052 import MDO3052
from ..instruments.keysight.e36106a import E36106A

from ..config import ADDRESS_E36106A, ADDRESS_MDO3052, PATH_TRASH

sys.modules['cloudpickle'] = None
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

HORIZONTAL_SCALES = np.array([[1*i, 2*i, 4*i]
                             for i in [1e-6, 1e-5, 1e-4, 1e-3, 1e-2,
                                       1e-1, 1e0, 1e1, 1e2, 1e3]]).flatten()


class voltage_sequence_time_domain_experiment(Procedure):
    # Parameter definition
    voltage_sequence = Parameter('Voltage Sequence', default='0,1,0')
    dwell_time = FloatParameter(name='Dwell Time', minimum=0,
                                maximum=2000, default=2, units='s')

    response_channel = ListParameter(name='Response Channel',
                                     choices=['CH1', 'CH2'], default='CH1')
    signal_channel = ListParameter(name='Signal Channel',
                                   choices=['CH1', 'CH2', 'n/a'],
                                   default='CH2')

    vertical_resolution = FloatParameter(name='Vertical Resolution', minimum=1,
                                         maximum=1000, default=5,
                                         units='mV/div')
    vertical_offset = FloatParameter(name='Vertical Offset', default=0,
                                     minimum=-4, maximum=4, units='div')
    termination_response = ListParameter(name='Response Channel Termination',
                                         choices=['50 Ohm', '1 MOhm'],
                                         default='50 Ohm')
    termination_signal = ListParameter(name='Signal Channel Termination',
                                       choices=['50 Ohm', '1 MOhm'],
                                       default='1 MOhm')
    record_length = ListParameter(name='Record Length',
                                  choices=[1000, 10000, 100000, 1000000,
                                           5000000, 10000000],
                                  default=10000)
    acquisition_mode = ListParameter(name='Acquisition Mode',
                                     choices=['Sample', 'Peak Detect',
                                              'Hi Res', 'Envelope', 'Average'],
                                     default='Sample')

    directory = Parameter('', default='empty')
    saving = BooleanParameter('Save Data', default=False)
    filename = Parameter('Filename', default='TimeTrace')

    DATA_COLUMNS = ['Time [s]', 'Response [V]', 'Signal [V]']

    def startup(self):
        log.info('Startup.')
        self.src = E36106A(ADDRESS_E36106A)
        log.info('Connection to E36106A established.')
        self.osc = MDO3052(ADDRESS_MDO3052)
        log.info('Connection to MDO3052 established.')

        log.info('Reset Voltage Source')
        self.src.reset()
        log.info('Setup Oscilloscope')
        self.osc.reset()

        self.osc.write('sel:ch2 on')

        voltage_array = np.asarray(self.voltage_sequence.split(','),
                                   dtype=np.float64)
        T_min = len(voltage_array)*self.dwell_time
        h_scale_min = T_min/10.
        for i, _ in enumerate(HORIZONTAL_SCALES):
            if HORIZONTAL_SCALES[i] < h_scale_min:
                continue
            else:
                h_scale = HORIZONTAL_SCALES[i]
                break
        self.osc.horizontalscal = h_scale
        self.osc.acqidilaymode = 'OFF'
        self.osc.horizontalpos = 0

        if self.response_channel == self.signal_channel:
            self.signal_channel = 'n/a'
            pass

        self.ch_response = self.osc.ch1
        if self.response_channel == 'CH2':
            self.ch_response = self.osc.ch2.position

        if not (self.signal_channel == 'n/a'):
            self.ch_signal = self.osc.ch2
            if self.signal_channel == 'CH1':
                self.ch_signal = self.osc.ch1

            self.ch_signal.termination = 'FIF'
            if self.termination_signal == '1 MOhm':
                self.ch_signal.termination = 'MEG'
            self.ch_signal.scale = max(voltage_array)/4.
            self.ch_signal.position = 0
        else:
            self.ch_signal = None

        # Set Termination values
        self.ch_response.termination = 'FIF'
        self.ch_response.scale = self.vertical_resolution/1000
        self.ch_response.position = self.vertical_offset

        if self.termination_response == '1 MOhm':
            self.ch_response.termination = 'MEG'

        # Set high resolution for measurement
        if self.acquisition_mode == 'Sample':
            self.osc.acquirmod = 'SAM'
        elif self.acquisition_mode == 'Peak Detect':
            self.osc.acquirmod = 'PEAK'
        elif self.acquisition_mode == 'Hi Res':
            self.osc.acquirmod = 'HIR'
        elif self.acquisition_mode == 'Envelope':
            self.osc.acquirmod = 'ENV'
        elif self.acquisition_mode == 'Average':
            self.osc.acquirmod = 'AVE'

        if not self.signal_channel == 'n/a':
            self.osc.triggersource = self.signal_channel
        else:
            self.osc.triggersource = self.response_channel
        self.emit('progress', 10)
        self.osc.triggertyp = 'EDG'
        self.osc.triggermode = 'NORM'
        self.osc.triggerlevel2 = 1
        self.osc.acqu_state = 0
        self.osc.singelrun = 'SEQ'

        self.osc.acquirereclen = self.record_length

        log.info('Setup Completed')
        self.emit('progress', 20)

    def execute(self):
        log.info('Measurement in progress.')
        self.osc.acqu_state = 1
        self.src.enable()
        voltage_array = np.asarray(self.voltage_sequence.split(','),
                                   dtype=np.float64)
        while self.osc.triggerstate != 'REA':
            log.info('Wait for Trigger to be Ready.')
            sleep(2)

        self.osc.force_trig()
        for i, Vi in enumerate(voltage_array):
            self.src.voltage_range = Vi
            sleep(self.dwell_time)
        self.src.disable()

        while self.osc.acqu_state == 1.0:
            log.info('Recording State')
            if self.should_stop():
                break

        log.info('Measurement Completed.')
        log.info('Data Processing')
        record_length = self.osc.acquirereclen
        response = self.osc.getwaveform(stop=record_length,
                                        channel=self.response_channel)
        if not self.signal_channel == 'n/a':
            signal = self.osc.getwaveform(stop=record_length,
                                          channel=self.signal_channel)
        else:
            signal = np.zeros_like(response)

        # Rescaling to correct voltage levels
        s_scale, s_off, s_pos = self.osc.get_vscale(self.signal_channel)
        r_scale, r_off, r_pos = self.osc.get_vscale(self.response_channel)

        signal = (signal-s_pos)*s_scale-s_off
        response = (response-r_pos)*r_scale-r_off

        t0, tscale, record_length = self.osc.get_timescale()
        time = np.linspace(t0, t0+record_length*tscale, record_length)

        self.emit('progress', 80)
        log.info('Emitting Data')
        for i in range(len(time)):
            data = {'Time [s]': time[i],
                    'Response [V]': response[i],
                    'Signal [V]': signal[i]}
            self.emit('results', data)
            if self.should_stop():
                break
        log.info('Data Emitted')
        self.emit('progress', 90)

    def shutdown(self):
        log.info('Shutting Down')
        self.osc.adapter.connection.close()
        self.src.disconnect()

        log.info('Measurement Successful.')
        self.emit('progress', 100)


class voltage_sequence_time_domain_interface(ManagedWindow):
    def __init__(self):
        super(voltage_sequence_time_domain_interface, self).__init__(
            procedure_class=voltage_sequence_time_domain_experiment,
            inputs=['voltage_sequence', 'dwell_time', 'response_channel',
                    'signal_channel', 'vertical_resolution', 'vertical_offset',
                    'termination_response', 'termination_signal',
                    'record_length', 'acquisition_mode', 'saving', 'filename'],
            displays=['voltage_sequence', 'dwell_time'],
            x_axis='Time [s]',
            y_axis='Response [V]',
            directory_input=True,
            sequencer=True)

        self.setWindowTitle('Voltage Sequence Time Domain')

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
