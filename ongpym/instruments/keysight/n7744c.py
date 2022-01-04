from pymeasure.instruments import Instrument
import numpy as np


class Channel():
    """
    Implementation of a Keysight N7744C Channel
    """
    def __init__(self, instrument, number):
        self.instrument = instrument
        self.number = number

    def values(self, command, **kwargs):
        """ Reads a set of values from the instrument through the adapter,
        passing on any key-word arguments.
        """
        cmd_subsystem = command.split(':')[1]
        cmd_end = command[command.find(':', 1):]
        return self.instrument.values(':%s%g%s' %
                                      (cmd_subsystem, self.number, cmd_end),
                                      **kwargs)

    def ask(self, command):
        # Get the part of the command up to the first :
        cmd_subsystem = command.split(':')[1]
        cmd_end = command[command.find(':', 1):]
        self.instrument.ask(':%s%g%s' % (cmd_subsystem, self.number, cmd_end))

    def write(self, command):
        cmd_subsystem = command.split(':')[1]
        if str(self.number) in cmd_subsystem:
            cmd_subsystem = cmd_subsystem[:-1]
        cmd_end = command[command.find(':', 1):]
        self.instrument.write(':%s%g%s' %
                              (cmd_subsystem, self.number, cmd_end))

    def zero(self):
        self.write(':SENS:CORR:COLL:ZERO')
        zero_cmd_status = 0  # self.values(':SENS:CORR:COLL:ZERO?')
        return zero_cmd_status == 0

    # SENSE SUBSYSTEM
    power_unit = Instrument.control(':SENS:POW:UNIT?', ':SENS:POW:UNIT %g',
                                    """Sensor power unit of selected channel \
                                    or of ALL channels.""")

    wavelength = Instrument.control(':SENS:POW:WAV?', ':SENS:POW:WAV %f',
                                    """ Sensor Wavelength for the Channel \
                                    in meters.""")

    power_range = Instrument.control(':SENS:POW:RANG?', ':SENS:POW:RANG %f',
                                     """ Power range for the channel. \
                                     The range is a float value in dBm.""")

    auto_range = Instrument.control(':SENS:POW:RANG:AUTO?',
                                    ':SENS:POW:RANG:AUTO %g',
                                    """ Enables or disables automatic power \
                                    ranging for the channel.""")

    auto_gain = Instrument.control(':SENS:POW:GAIN:AUTO?',
                                   ':SENS:POW:GAIN:AUTO %g',
                                   """ Enables or disables automatic gain for \
                                   the channel.""")

    averaging_time = Instrument.control(':SENS:POW:ATIM?', ':SENS:POW:ATIM %f',
                                        """ Averaging time in seconds, i.e. the \
                                        time the signal is averaged for each \
                                        measurement point.""")

    loop_number = Instrument.control(':SENS:FUNC:LOOP?', ':SENS:FUNC:LOOP %g',
                                     """ Number of Logging Loops. """)

    _logging_parameters = Instrument.control(':SENS:FUNC:PAR:LOGG?',
                                             ':SENS:FUNC:PAR:LOGG %s',
                                             """ (PRIVATE) Number of \
                                             datapoints and averaging time \
                                             for logging data acquisition.""")

    _function_state = Instrument.control(':SENS:FUNC:STAT?',
                                         ':SENS:FUNC:STAT %s',
                                         """ (PRIVATE) Enables/Disables  the \
                                         logging, MinMax, or stability data \
                                         acquisition function mode.""")

    def setup_logging(self, N=None, tau_avg=None):
        old_parameters = self._logging_parameters
        if not N:
            N = old_parameters[0]
        if not tau_avg:
            tau_avg = old_parameters[1]

        self._logging_parameters = str(N) + ',' + str(tau_avg)

    def start_logging(self):
        self._function_state = 'LOGG,STAR'

    def stop_logging(self):
        self._function_state = 'LOGG,STOP'

    def get_result(self):
        command = ':SENS:FUNC:RES?'
        cmd_subsystem = command.split(':')[1]
        cmd_end = command[command.find(':', 1):]
        cmd_total = ':%s%g%s' % (cmd_subsystem, self.number, cmd_end)
        return np.array(self.instrument.adapter.
                        connection.query_binary_values(cmd_total,
                                                       datatype=u'f'))

    def in_progress(self):
        if not self._function_state[1] == 'COMPLETE':
            return True
        else:
            return False

    # INITIATE SUBSYSTEM
    continuous_mode = Instrument.control(':init:cont?', 'init:cont %g',
                                         """Continuous software triggering \
                                         state (on/off)""")

    # TRIGGER SUBSYSTEM
    trigger_delay = Instrument.control(':TRIG:DEL?', ':TRIG:DEL %g',
                                       """ Factor for trigger delay. Effective \
                                       trigger delay time is factor/32 MHz.""")

    trigger_edge = Instrument.control(':TRIG:INP:EDGE?', ':TRIG:INP:EDGE %g',
                                      """ Trigger edge detection \
                                      (0: Rising, 1: Falling)""")

    trigger_input_setting = Instrument.control(':TRIG:INP?', ':TRIG:INP %s',
                                               """ Incoming Trigger \
                                               Response.""")

    trigger_offset = Instrument.control(':TRIG:OFFS?', ':TRIG:OFFS %g',
                                        """ Number of incoming triggers \
                                        received before data logging \
                                        begins.""")


class N7744C(Instrument):
    def __init__(self, address, **kwargs):
        super(N7744C, self).__init__(
            address, "N774C High Dynamic Range Power Meter", **kwargs)

        self.ch1 = Channel(self, 1)
        self.ch2 = Channel(self, 2)
        self.ch3 = Channel(self, 3)
        self.ch4 = Channel(self, 4)

    def reset(self):
        self.write('*RST')

    def zero_all(self):
        self.write(':SENS:CORR:COLL:ZERO:ALL')
        zero_cmd_status = 0  # self.values(':SENS:CORR:COLL:ZERO:ALL?')
        return zero_cmd_status == 0

    wavelength = Instrument.control(':SENS:POW:WAV:ALL?',
                                    ':SENS:POW:WAV:ALL %f',
                                    """ Sensor Wavelength for all Channels \
                                    in meters.""")

    power_unit = Instrument.control('SENS:POW:UNIT:ALL:CSV?',
                                    'SENS:POW:UNIT:ALL %g',
                                    """ Power Unit for all channels.""")

    def close(self):
        self.adapter.connection.close()
