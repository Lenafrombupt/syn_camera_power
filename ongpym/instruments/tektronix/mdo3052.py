import logging

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_range, strict_discrete_set
import numpy as np

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


FORMATTER_LOOKUP = {  # number of bytes, then signedness
    "1": {"RI": "b", "RP": "B"},
    "2": {"RI": "h", "RP": "H"},
    "4": {"RI": "i", "RP": "I", "FP": "f"},
    "8": {"RI": "q", "RP": "Q", "FP": "d"},
}


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
        cmd_subsystem = command.split(':')[0]
        cmd_end = command[command.find(':', 1):]
        # print(':%s%g%s' % (cmd_subsystem,self.number, cmd_end))
        return self.instrument.values(':%s%g%s' %
                                      (cmd_subsystem, self.number, cmd_end),
                                      **kwargs)

    def ask(self, command):
        # Get the part of the command up to the first :
        cmd_subsystem = command.split(':')[0]
        cmd_end = command[command.find(':', 1):]
        self.instrument.ask(':%s%g%s' % (cmd_subsystem, self.number, cmd_end))

    def write(self, command):
        cmd_subsystem = command.split(':')[0]
        if str(self.number) in cmd_subsystem:
            cmd_subsystem = cmd_subsystem[:-1]
        cmd_end = command[command.find(':', 1):]
        self.instrument.write(':%s%g%s' %
                              (cmd_subsystem, self.number, cmd_end))

    scale = Instrument.control('CH:SCA?', 'CH:SCA %f',
                               """This command specifies the vertical scale of \
                               the channel in V""",
                               validator=strict_range, values=[1e-3, 10])

    position = Instrument.control('CH:POS?', 'CH:POS %f',
                                  """ This command specifies the channel's \
                                  vertical position.""")

    termination = Instrument.control('CH:TER?', 'CH:TER %s',
                                     """This command specifies channel 1 input \
                                     termination to 1M or 50 by: FIF,MEG,? """,
                                     validator=strict_discrete_set,
                                     values=['FIF', 'MEG'])


class MDO3052(Instrument):
    def __init__(self, adapter, **kwargs):
        super(MDO3052, self).__init__(
            adapter, "Oscilloscope", **kwargs
        )
        self.ch1 = Channel(self, 1)
        self.ch2 = Channel(self, 2)

    # TODO: THESE ARE DEPRECATED, SHOULD BE REMOVED AFTER
    # UPDATING ALL PROCEDURES
    verscale1 = Instrument.control('CH1:SCA?', 'CH1:SCA %f',
                                   """This command specifies the vertical \
                                   scale of channel 1 in V""",
                                   validator=strict_range, values=[1e-3, 10])
    verpos1 = Instrument.control('CH1:POS?', 'CH1:POS %f',
                                 """ This command specifies the channel 1 \
                                 vertical position.""")
    termination1 = Instrument.control('CH1:TER?', 'CH1:TER %s',
                                      """This command specifies channel 1 \
                                      input termination to 1M or 50 by: \
                                      FIF,MEG,?. """,
                                      validator=strict_discrete_set,
                                      values=['FIF', 'MEG'])
    # all informations with 'CH2?'
    verscale2 = Instrument.control('CH2:SCA?', 'CH2:SCA %f',
                                   """This command specifies the vertical \
                                   scale of channel 2 in V.""",
                                   validator=strict_range,
                                   values=[1e-3, 10])
    verpos2 = Instrument.control('CH2:POS?', 'CH2:POS %f',
                                 """This command specifies the channel 2 \
                                 vertical position.""")
    termination2 = Instrument.control('CH2:TER?', 'CH2:TER %s',
                                      """This command specifies channel 2 \
                                      input termination to 1M or 50 by: \
                                      FIF,MEG,?.""",
                                      validator=strict_discrete_set,
                                      values=['FIF', 'MEG'])

    # trigger
    triggertyp = Instrument.control('TRIG:A:TYP?', 'TRIG:A:TYP %s',
                                    """This command sets the type of A trigger \
                                    (edge, logic, pulse, bus or video).""",
                                    validator=strict_discrete_set,
                                    values=['EDG', 'LOGI',
                                            'PULS', 'BUS', 'VID'])
    triggerlevel1 = Instrument.control('TRIG:A:LEV:CH1?', 'TRIG:A:LEV:CH1 %f',
                                       """Sets the threshold voltage level \
                                       channel 1 in V.""",
                                       validator=strict_range,
                                       values=[-3.2, 3.2])
    triggerlevel2 = Instrument.control('TRIG:A:LEV:CH2?', 'TRIG:A:LEV:CH2 %f',
                                       """Sets the threshold voltage level \
                                       channel 2 in V.""",
                                       validator=strict_range,
                                       values=[-3.2, 3.2])
    triggermode = Instrument.control('TRIG:A:MOD?', 'TRIG:A:MOD %s',
                                     """This command specifies the A trigger \
                                     mode - either AUTO or NORMAL.""",
                                     validator=strict_discrete_set,
                                     values=['AUTO', 'NORM'])
    triggerholdoff = Instrument.control('TRIG:A:HOLD:TIM?',
                                        'TRIG:A:HOLD:TIM %f',
                                        """This command specifies the A \
                                        trigger holdoff time in sec.""",
                                        validator=strict_range,
                                        values=[20e-9, 8])
    triggerstate = Instrument.measurement('TRIG:STATE?',
                                          """Returns the current state of the \
                                          triggering system.""")

    # only for trigger typ 'EDG' for the following statements:

    triggercoupling = Instrument.control('TRIG:A:EDGE:COUP?',
                                         'TRIG:A:EDGE:COUP %s',
                                         """This command specifies the type of \
                                         coupling for the A edge trigger: \
                                         AC,DC,... """,
                                         validator=strict_discrete_set,
                                         values=['AC', 'DC'])
    triggersource = Instrument.control('TRIG:A:EDGE:SOU?',
                                       'TRIG:A:EDGE:SOU %s',
                                       """This command specifies the source \
                                       for the A edge trigger: \
                                       AUX, CH1, CH2...""",
                                       validator=strict_discrete_set,
                                       values=['AUX', 'CH1', 'CH2'])
    triggerslope = Instrument.control('TRIG:A:EDGE:SLOP?',
                                      'TRIG:A:EDGE:SLOP %s',
                                      """This command specifies the slope for \
                                      the A edge trigger: rising, falling or \
                                      either.""",
                                      validator=strict_discrete_set,
                                      values=['RIS', 'FALL', 'EITH'])

    # acquire
    acquirmod = Instrument.control('ACQ:MOD?', 'ACQ:MOD %s',
                                   """Specifies the acquisition mode of the \
                                   oscilloscope for all analog channel \
                                   waveforms.""",
                                   validator=strict_discrete_set,
                                   values=['SAM', 'PEAK', 'HIR', 'AVE', 'ENV'])
    acquirereclen = Instrument.control('HOR:RECO?', 'HOR:RECO %f',
                                       """This command specifies the record \
                                       length. [1e3,1e4,1e5,1e6,5e6,10e6].""",
                                       validator=strict_discrete_set,
                                       values=[1e3, 1e4, 1e5, 1e6, 5e6, 10e6])
    acqidilaymode = Instrument.control('HOR:DEL:MOD?', 'HOR:DEL:MOD %s',
                                       """This command specifies the \
                                       horizontal delay mode in sec.""",
                                       validator=strict_discrete_set,
                                       values=['ON', 'OFF'])
    singelrun = Instrument.control('ACQ:STOPA?', 'ACQ:STOPA %s',
                                   """This command specifies whether the \
                                   acquisition is continuous or single \
                                   sequence.""",
                                   validator=strict_discrete_set,
                                   values=['RUNST', 'SEQ'])
    acqu_state = Instrument.control('ACQ:STATE?', 'ACQ:STATE %d',
                                    """Starts(1) or stops(0) the acquisition \
                                    system.""")

    # time settings
    horizontalscal = Instrument.control('HOR:SCA?', 'HOR:SCA %f',
                                        """This command specifies the \
                                        horizontal scale in seconds.""",
                                        validator=strict_range,
                                        values=[1e-9, 400])
    # only use when acquidilaymode = OFF
    horizontalpos = Instrument.control('HOR:POS?', 'HOR:POS %f',
                                       """This command specifies the \
                                       horizontal position, in percent, that \
                                       is used when delay is off.""",
                                       validator=strict_range,
                                       values=[0, 100])
    # only use when acquidiliaymode = ON
    horizontaldelaytime = Instrument.control('HOR:DEL:TIM?', 'HOR:DEL:TIM %f',
                                             """This command specifies the \
                                             horizontal delay time in \
                                             seconds.""",
                                             validator=strict_range,
                                             values=[-5e3, 5e3])

    # data typ settings:
    datasource = Instrument.control(':DAT:SOU?', ':DAT:SOU %s',
                                    """ Sets the source waveform to be \
                                    transferred to Channel.""")
    datastart = Instrument.control(':DAT:START?', ':DAT:START %d',
                                   """This, along with DATa:STOP, specifies \
                                   the portion of the waveform record that \
                                   will be transferred.""")
    datastop = Instrument.control(':DAT:STOP?', ':DAT:STOP %d',
                                  """Sets data stop point.""")

    # Auto setting of osci
    autoset = Instrument.setting('AUTOS %s', """Sets the vertical, horizontal and \
                                 trigger controls to provide a stable display \
                                 of the appropriate waveform. This is \
                                 equivalent to pressing the front panel \
                                 Autoset button.""")

    # useful functions
    def select(self):
        """
        select CH1 and CH2 to be visible on the oscilloscope screen

        Returns
        -------
        None.

        """
        self.write('sel:ch1 ON')
        self.write('sel:ch2 ON')

    def autoset_triggerlevel(self):
        self.write('FPA:PRESS TRIGL')

    def getwaveform(self, start=1, stop=10000, channel='CH1'):
        """
        get the waveform from the oscilloscope

        Parameters
        ----------
        start : TYPE
            the start number of the data points, example 1
        stop : TYPE
            the stop number of the data points, example 1000/record length
        channel : TYPE, optional
            defines the channel which is given back. The default is 'CH1'.

        Returns
        -------
        d : TYPE
            returns the datapoints of the chosen channel

        """
        self.datasource = channel
        self.datastart = start
        self.datastop = stop
        self.write(':WFMO:ENC BIN')
        self.write(':WFMO:BYT_N 2')
        self.write(':WFMO:BN_F RI')
        self.write(':WFMO:BYT_O MSB')

        format_string = FORMATTER_LOOKUP['2']['RI']
        is_big_endian = True

        d = self.adapter.connection.query_binary_values(
            'curve?',
            datatype=format_string,
            is_big_endian=is_big_endian,
            container=np.array)

        return np.array(d)

    def get_timescale(self):
        """
        get the timescale of the oscilloscope

        Returns
        -------
        tstart : TYPE
            the start time
        tscale : TYPE
            the time scale
        record : TYPE
            the recordlength for example 1000 data points

        """
        record = int(self.ask('horizontal:recordlength?'))
        tscale = float(self.ask('wfmoutpre:xincr?'))
        tstart = float(self.ask('wfmoutpre:xzero?'))
        return tstart, tscale, record

    def get_vscale(self, channel):
        """

        Parameters
        ----------
        channel : TYPE
            the channel for example: 'CH1' or 'CH2'

        Returns
        -------
        vscale : TYPE
            the vscale of the given channel
        voff : TYPE
            the offset of the oscilloscope
        vpos : TYPE
            the position of the zero

        """
        self.write('data:source '+channel)
        vscale = float(self.ask('wfmoutpre:ymult?'))  # volts / level
        voff = float(self.ask('wfmoutpre:yzero?'))  # reference voltage
        vpos = float(self.ask('wfmoutpre:yoff?'))  # reference position (level)
        return vscale, voff, vpos

    def reset(self):
        """
        resets the oscilloscope

        Returns
        -------
        None.

        """
        self.write('*rst')

    def get_scale(self):
        """
        uses the auto set function of the oscilloscope \
        and gives the best vscale for channel 1 back

        Returns
        -------
        scale for channel 1

        """
        self.write('sel:ch2 off')
        self.write('sel:ch1 on')
        self.write('AUTOS EXEC')
        scale = self.verscale1
        self.write('AUTOS UND')
        self.write('sel:ch2 on')
        return scale/1.5

    def busy(self):
        """
        asks the oscilloscope  if it is busy

        Returns
        -------
        state : TYPE
            DESCRIPTION.

        """
        state = self.ask('BUSY?')
        return state

    def force_trig(self):
        """
        forces a trigger if oscilloscope was ready before, \
        otherwise nothing happen

        Returns
        -------
        None.

        """
        self.write('TRIG FORC')
