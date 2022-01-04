try:
    import ongpym
    del ongpym
except ImportError:
    from pathlib import Path
    file = Path(__file__). resolve()
    package_root_directory = str(file)[:str(file).find('ONGPyMeasureSuite')] \
        + 'ONGPyMeasureSuite'
    exec(open(str(package_root_directory)+'/initialize.py').read())

from ongpym.instruments.keysight.n7744c import N7744C
from ongpym.instruments.keysight.n7776c import N7776C
from time import sleep
import sys

import matplotlib.pyplot as plt

visa_address_pm = 'TCPIP0::100.65.8.121::inst0::INSTR'
pm = N7744C(visa_address_pm)


visa_address_laser = 'TCPIP0::100.65.2.53::inst0::INSTR'
laser = N7776C(visa_address_laser)
laser.reset()

# pm.zero_all()

laser.output = 1
while not laser.output == 1:
    sleep(0.1)

pm.reset()

laser.trigger_out = 'stf'
laser.trigger_in = 'ign'

laser.wl_start = 1560
laser.wl_stop = 1560.5
laser.sweep_step = 0.0001
laser.sweep_speed = 0.5
laser.sweep_mode = 'cont'

laser.wl_logging = 1

laser.output_power_unit = 0
laser.output_power = 10

if not laser.sweep_check == [0.0, 'OK']:
    print('Error in the sweep settings. Abort!')
    sys.exit()

pm.ch1.stop_logging()

pm.ch1.continuous_mode = 0
pm.ch1.loop_number = 1
pm.ch1.power_unit = 1
pm.ch1.auto_range = 0
pm.ch1.auto_gain = 0
pm.ch1.range = -30
pm.ch1.wavelength = 1550e-9
pm.ch1.trigger_input_setting = 'sme'
pm.ch1.setup_logging(N=min(int(laser.sweep_points), 1000000), tau_avg=1e-6)

pm.ch1.start_logging()
sleep(5)

laser.sweep = 1

while not laser.sweep == 0:
    sleep(1)
    print('Sweep in progress', pm.ch1._function_state)

# pm.ch1.stop_logging()

power_data = pm.ch1.get_result()
wavelength_data = laser.get_wl_data()

fig, ax = plt.subplots()
ax.plot(wavelength_data, power_data, 'ob')
fig.show()

laser.output = 0
laser.close()
pm.close()
