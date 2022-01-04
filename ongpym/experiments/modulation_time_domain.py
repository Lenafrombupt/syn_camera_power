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
from pymeasure.experiment import (IntegerParameter,
                                  FloatParameter, BooleanParameter,
                                  ListParameter)
from pymeasure.experiment.parameters import Parameter
from ..instruments.gwinstek.afg2125 import AFG2125
from ..instruments.tektronix.mdo3052 import MDO3052

from ..config import ADDRESS_AFG2125, ADDRESS_MDO3052

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
sys.modules['cloudpickle'] = None

HORIZONTAL_SCALES = np.array([[1*i, 2*i, 4*i]
                             for i in [1e-6, 1e-5, 1e-4, 1e-3,
                             1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3]]).flatten()


class modulation_time_domain_experiment(Procedure):
    # Parameter definition

    frequency = FloatParameter(name='Frequency', minimum=0,
                               maximum=25e6, default=1e3, units='Hz')
    amplitude = FloatParameter(name='Amplitude', default=1,
                               minimum=0, units='Vpp')
    offset = FloatParameter(name='Offset', default=0, minimum=-10, maximum=10,
                            units='V')
    signal = ListParameter(name='Signal Type',
                           choices=['Triangular', 'Square'],
                           default='Triangular')

    response_channel = ListParameter(name='Response Channel',
                                     choices=['CH1', 'CH2'], default='CH1')
    signal_channel = ListParameter(name='Signal Channel',
                                   choices=['CH1', 'CH2', 'n/a'],
                                   default='CH2')

    n_periods = IntegerParameter(name='Number of Periods',
                                 minimum=1, maximum=30, default=5)
    vertical_resolution = FloatParameter(name='Vertical Resolution',
                                         minimum=1, maximum=1000, default=5,
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
                                              'Hi Res', 'Envelope',
                                              'Average'],
                                     default='Sample')

    directory = Parameter('', default='empty')
    saving = BooleanParameter('Save Data', default=False)
    filename = Parameter('Filename', default='TimeTrace')

    DATA_COLUMNS = ['Time [s]', 'Response [V]', 'Signal [V]']

    def startup(self):
        log.info('Startup.')
        self.fg = AFG2125(ADDRESS_AFG2125)
        log.info('Connection to AFG2125 established.')
        self.osc = MDO3052(ADDRESS_MDO3052)
        log.info('Connection to MDO3052 established.')

        log.info('Setup Oscilloscope')
        self.osc.reset()

        self.osc.write('sel:ch2 on')

        T_min = self.n_periods/self.frequency
        h_scale_min = T_min/10.
        for i, _ in enumerate(HORIZONTAL_SCALES):
            if HORIZONTAL_SCALES[i] < h_scale_min:
                continue
            else:
                h_scale = HORIZONTAL_SCALES[i]
                break
        self.osc.horizontalscal = h_scale

        if self.response_channel == self.signal_channel:
            # TODO: Error handling

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
            self.ch_signal.scale = self.amplitude/3.
            self.ch_signal.position = 0  # -self.offset/((self.amplitude/4.))
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
        self.osc.triggerlevel2 = 0.1  # self.offset
        self.osc.acqu_state = 0
        self.osc.singelrun = 'SEQ'
        self.osc.acquirereclen = self.record_length

        log.info('Setup Function Generator')
        self.fg.frequency = self.frequency
        self.fg.amplitude = self.amplitude
        self.fg.offset = self.offset
        self.fg.signal = 'RAMP'
        if self.signal == 'Square':
            self.fg.signal = 'SQU'

        self.fg.high_impedance = True  # self.termination_response == '1 MOhm'

        log.info('Setup Completed')
        self.emit('progress', 20)

    def execute(self):
        self.fg.output = True
        self.osc.acqu_state = 1
        sleep(2)
        while self.osc.acqu_state == 1.0:
            log.info('Recording State')
            if self.should_stop():
                break

        log.info('Measurement Completed.')
        self.fg.output = True

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
        self.fg.adapter.connection.close()

        log.info('Measurement Successful.')
        self.emit('progress', 100)


class modulation_time_domain_interface(ManagedWindow):
    def __init__(self):
        super(modulation_time_domain_interface, self).__init__(
            procedure_class=modulation_time_domain_experiment,
            inputs=['frequency', 'amplitude', 'offset', 'signal',
                    'response_channel', 'signal_channel', 'n_periods',
                    'vertical_resolution', 'vertical_offset', 'record_length',
                    'acquisition_mode', 'termination_response',
                    'termination_signal', 'saving', 'filename'],
            displays=['frequency', 'amplitude', 'offset'],
            x_axis='Time [s]',
            y_axis='Response [V]',
            directory_input=True,
            sequencer=True)

        self.setWindowTitle('Modulation Time Domain')

    def queue(self, *, procedure=None):
        directory = self.directory
        if procedure is None:
            procedure = self.make_procedure()

        if not procedure.saving:
            directory = \
                r"C:\Users\ONGD11_01\Documents\\ONGPyMeasure_trash\.trash"
        elif directory == '':
            directory = \
                r"C:\Users\ONGD11_01\Documents\ONGPyMeasure_trash"

        procedure.directory = directory
        filename = procedure.filename

        while (procedure.filename+'.csv') in os.listdir(directory):
            procedure.filename = procedure.filename+'_1'
            filename = procedure.filename

        dirfilename = os.path.join(directory, filename)

        results = Results(procedure, dirfilename+'.csv')
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)
