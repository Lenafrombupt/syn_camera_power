 
import logging

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import truncated_range

from pymeasure.adapters import VISAAdapter
from pymeasure.adapters import VXI11Adapter
from time import sleep

class E36106A(Instrument):
    """ Represents the Keysight E36106A Power supply 
    interface for interacting with the instrument
    """
    
    ###############
    # Current (A) #
    ###############
    current_range = Instrument.control(
        ":CURR?", ":CURR %g",
        """ A floating point property that controls the DC current range in
        Amps, which can take values from 0 to 25 A.
        Auto-range is disabled when this property is set. """,
        validator=truncated_range,
        values=[0, 0.4],
    )
    
    current = Instrument.measurement(":MEAS:CURR?",
                                     """ Reads a setting currenti in Amps"""
                                     )
    
    ###############
    # Voltage (V) #
    ###############
    voltage_range = Instrument.control(
        ":VOLT?", ":VOLT %g V",
        """ A floating point property that controls the DC voltage range in
        Volts, which can take values from 0 to 100 V.
        Auto-range is disabled when this property is set. """,
        validator=truncated_range,
        values=[0, 100]
    )

    voltage = Instrument.measurement("MEAS:VOLT?",
        """ Reads a DC voltage measurement in Volts. """
     )
    
    ##############
    #_status (0/1) #
    ##############
    _status = Instrument.measurement(":OUTP?",
        """ Read power supply current output status. """,
    )
    
    ###############
    # Calibration #
    ###############
    
    def save_calibration(self):
        self.write('CAL:SAVE')
    
    def enable(self):
        """ Enables the flow of current.
        """
        self.write(":OUTP 1")

    def disable(self):
        """ Disables the flow of current.
        """
        self.write(":OUTP 0")

    def is_enabled(self):
        """ Returns True if the current supply is enabled.
        """
        return bool(self._status)
    
    def __init__(self, adapter, **kwargs):
        super(E36106A, self).__init__(
            adapter, "Keysight E36106A power supply", **kwargs
        )
        
        # Set up data transfer format
        if isinstance(self.adapter, VISAAdapter):
            self.adapter.datatype='float32'
            self.adapter.converter='f'
            self.adapter.separator=','
            self.adapter.is_binary=False
            # self.adapter.config(
            #     datatype='float32',
            #     converter='f',
            #     separator=','
            # )
            
    def check_errors(self):
        """ Read all errors from the instrument."""
        while True:
            err = self.values(":SYST:ERR?")
            if int(err[0]) != 0:
                errmsg = "Keysight E36106A: %s: %s" % (err[0],err[1])
                log.error(errmsg + '\n')
            else:
                break
            
    def disconnect(self):
        """ Disconnect the Power Supply """
        self.adapter.manager.close()

    def reset(self):
        self.write("*RST")