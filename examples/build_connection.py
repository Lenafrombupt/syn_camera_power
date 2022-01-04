try:
    import ongpym
    del ongpym
except:
    from pathlib import Path
    file = Path(__file__). resolve()  
    package_root_directory = str(file)[:str(file).find('ONGPyMeasureSuite')] + 'ONGPyMeasureSuite'
    exec(open(str(package_root_directory)+'/initialize.py').read())

import sys
sys.modules['cloudpickle'] = None

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

from pymeasure.experiment import Procedure, Results
from pymeasure.display.windows import ManagedWindow

from pymeasure.experiment.results import unique_filename
from pymeasure.experiment import FloatParameter, IntegerParameter

import numpy as np


from ongpym.instruments.keysight.e36106a import E36106A
from time import sleep
import pyvisa

ADDRESS_E36106A = 'TCPIP::10.4.58.232::inst0::INSTR'
rm = pyvisa.highlevel.ResourceManager()
def new_func(rm):
    rm.list_resources()

new_func(rm)
print