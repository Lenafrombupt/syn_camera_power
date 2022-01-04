from pymeasure.instruments import Instrument
import numpy as np


class N7776C(Instrument):
    def __init__(self, address, **kwargs):
        super(N7776C, self).__init__(
            address, "N7776C Tunable Laser Source", **kwargs)

    def reset(self):
        self.write('*RST')

    output = Instrument.control('SOUR0:POW:STAT?',
                                'SOUR0:POW:STAT %g',
                                """ Laser State (on/off) of the source """)
    output_power = Instrument.control('SOUR0:POW?', 'SOUR0:POW %f',
                                      """ Laser Output Power in the \
                                      set unit.""")
    output_power_unit = Instrument.control('SOUR0:POW:UNIT?',
                                           'SOUR0:POW:UNIT %g',
                                           """ Laser Output Power Unit \
                                           (0: dBm, 1: Watts) """)

    trigger_out = Instrument.control('TRIG0:OUTP?', 'TRIG0:OUTP %s',
                                     """ Specifies when an output trigger is \
                                     generated and arms the module. """)

    trigger_in = Instrument.control('TRIG0:INP?', 'TRIG0:INP %s',
                                    """ Sets the incoming trigger response \
                                    and arms the module. """)

    wl_start = Instrument.control('sour0:wav:swe:star?',
                                  'sour0:wav:swe:star %fnm',
                                  """ Start Wavelength for a sweep \
                                  (in nanometers).""")
    wl_stop = Instrument.control('sour0:wav:swe:stop?',
                                 'sour0:wav:swe:stop %fnm',
                                 """ End Wavelength for a sweep \
                                 (in nanometers).""")

    sweep_step = Instrument.control('sour0:wav:swe:step?',
                                    'sour0:wav:swe:step %fnm',
                                    """ Step width of the sweep \
                                    (in nanometers).""")
    sweep_speed = Instrument.control('sour0:wav:swe:speed?',
                                     'sour0:wav:swe:speed %fnm/s',
                                     """Speed of the sweep \
                                     (in nanometers per second)""")
    sweep_mode = Instrument.control('sour0:wav:swe:mode?',
                                    'sour0:wav:swe:mode %s',
                                    """ Sweep mode of the swept \
                                    laser source.""")

    sweep_check = Instrument.measurement('sour0:wav:swe:chec?',
                                         """Returns whether the currently set \
                                         sweep parameters (sweep mode, sweep \
                                         start, stop, width, etc.) are \
                                         consistent. If there is a sweep \
                                         configuration problem, the laser \
                                         source is not able to pass a \
                                         wavelength sweep.""")

    sweep_points = Instrument.measurement('sour0:read:points? llog',
                                          """Returns the number of datapoints \
                                          that the :READout:DATA? command will\
                                           return.""")
    sweep = Instrument.control('sour0:wav:swe?', 'sour0:wav:swe %g',
                               """ State of the wavelength sweep. Stops, \
                               starts, pauses or continues a wavelength \
                               sweep.""")

    wl_logging = Instrument.control('SOUR0:WAV:SWE:LLOG?',
                                    'SOUR0:WAV:SWE:LLOG %g',
                                    """ State (on/off) of the lambda logging \
                                    feature of the laser source.""")

    def get_wl_data(self):
        return np.array(self.adapter.
                        connection.query_binary_values('sour0:read:data? llog',
                                                       datatype=u'd'))

    def close(self):
        self.adapter.connection.close()
