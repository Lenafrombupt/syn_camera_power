try:
    import ongpym
    del ongpym
except ImportError:
    from pathlib import Path
    file = Path(__file__). resolve()
    package_root_directory = str(file)[:str(file).find('ONGPyMeasureSuite')] \
        + 'ONGPyMeasureSuite'
    exec(open(str(package_root_directory)+'/initialize.py').read())

import sys
import logging
from pymeasure.experiment import Procedure, Results
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment.results import unique_filename
from pymeasure.experiment import FloatParameter, IntegerParameter
import numpy as np


from ongpym.instruments.keysight.e36106a import E36106A
from time import sleep

from ..config import ADDRESS_E36106A

sys.modules['cloudpickle'] = None
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class electrode_resistance_experiment(Procedure):

    # Define Parameters
    V_min = FloatParameter('Minimum Voltage', default=0, minimum=0,
                           maximum=100)
    V_max = FloatParameter('Maximum Voltage', default=10, minimum=0,
                           maximum=100)
    V_step = FloatParameter('Voltage Stepsize', default=1, minimum=0.001,
                            maximum=25)
    N_avg = IntegerParameter('Number of Averages per Step', default=1,
                             minimum=1, maximum=100)

    DATA_COLUMNS = ['V set [V]', 'V [V]', 'I [mA]', 'R [Ohm]', 'P [mW]']

    def startup(self):
        log.info('Starting Resistance Measurement.')
        self.emit('progress', 0)

        # Connect to the voltage source and reset it
        self.src = E36106A(ADDRESS_E36106A)
        self.src.reset()

    def execute(self):
        log.info('Measurement in progress.')
        Vs = np.arange(self.V_min, self.V_max, self.V_step)
        for j, Vj in enumerate(Vs):
            self.src.voltage_range = Vj
            self.src.enable()
            sleep(1)
            V_set = []
            I_set = []
            for _ in np.arange(self.N_avg):
                V_set.append(self.src.voltage)
                I_set.append(self.src.current)
            self.src.disable()
            V = np.average(np.array(V_set))
            I0 = np.average(np.array(I_set))

            data_curr = {'V set [V]': Vj, 'V [V]': V, 'I [mA]': I0,
                         'R [Ohm]': V/(I0*1e-3), 'P [mW]': V*I0}
            self.emit('results', data_curr)
            self.emit('progress', j/len(Vs)*100)

    def shutdown(self):
        self.src.disconnect()


class electrode_resistance_interface(ManagedWindow):
    def __init__(self):
        super(electrode_resistance_interface, self).__init__(
            procedure_class=electrode_resistance_experiment,
            inputs=['V_min', 'V_max', 'V_step', 'N_avg'],
            displays=['V_min', 'V_max', 'V_step', 'N_avg'],
            x_axis='P [mW]',
            y_axis='R [Ohm]',
            directory_input=True,
            sequencer=False
        )
        self.setWindowTitle('DC Resistance Measurement')

    def queue(self, *, procedure=None):
        directory = self.directory

        if directory == '':
            directory = r"C:\Users\ONGD11_01\Documents\ONGPyMeasure_trash"

        if procedure is None:
            procedure = self.make_procedure()

        filename = unique_filename(directory)
        print(filename)

        results = Results(procedure, filename)

        experiment = self.new_experiment(results)

        self.manager.queue(experiment)


if __name__ == "__main__":
    from pymeasure.display.Qt import QtGui

    app = QtGui.QApplication(sys.argv)
    window = electrode_resistance_interface()
    window.show()
    sys.exit(app.exec_())
