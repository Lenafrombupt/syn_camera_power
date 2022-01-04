import logging
from pymeasure.instruments import Instrument
from .adapters import GWInstekAdapter
from numpy import inf as npinf

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class AFG2125(Instrument):
    def __init__(self, port, **kwargs):
        super(AFG2125, self).__init__(
            GWInstekAdapter(port), "GW Instek AFG-2125 Function Generator",
            **kwargs)

    signal = Instrument.control("SOUR:FUNC?\n", "SOUR:FUNC %s\n",
                                """ Signal type selected to apply.""")

    frequency = Instrument.control("SOUR:FREQ?\n", "SOUR:FREQ %f\n",
                                   """ Frequency of the output.""")

    amplitude = Instrument.control("SOUR:AMPL?\n", "SOUR:AMPL %f\n",
                                   """ Peak-to-peak amplitude of the output. \
                                   Maximum is dependent by the termination \
                                   setting.""")

    offset = Instrument.control("SOUR:DCO?\n", "SOUR:DCO %f\n",
                                """ DC Offset (in Volts) of the output. \
                                Maximum is dependent on the termination \
                                setting·""")

    duty_cycle = Instrument.control("SOUR:SQU:DCYC?\n", "SOUR:SQU:DCYC %f\n",
                                    """ Duty Cycle of the square signal. \
                                    This parameter has no effect if a signal \
                                    other than the square is selected.""")

    symmetry = Instrument.control("SOUR:RAMP:SYMM?\n", "SOUR:RAMP:SYMM %f\n",
                                  """ Symmetry of the ramp signal. \
                                  This parameter has no effect if a signal \
                                  other than the ramp is selected.""")

    high_impedance = \
        Instrument.control("OUTP:LOAD?\n", "OUTP:LOAD %s\n",
                           """ State of the impedance setting of the AFG. \
                           True = High Impedance, False = 50 Ohms. """,
                           get_process=lambda v: bool(['DEF', npinf].index(v)),
                           set_process=lambda v: ['DEF', 'INF'][int(v)])

    output = Instrument.control("OUTP?\n", "OUTP %s\n",
                                """ Output state of the AFG (True/False).""",
                                get_process=lambda v: bool(v),
                                set_process=lambda v: ['OFF', 'ON'][int(v)])
