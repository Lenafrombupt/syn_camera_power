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

from pymeasure.display.Qt import QtGui
from ongpym.experiments.power_change_step import power_change_step_interface
# import sys
# sys.modules['cloudpickle'] = None



app = QtGui.QApplication(sys.argv)
window = power_change_step_interface()
window.show()
sys.exit(app.exec_())