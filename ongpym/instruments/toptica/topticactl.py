import logging
from pymeasure.instruments import Instrument
from .adapters import TopticaAdapter
from pymeasure.instruments.validators import strict_range, strict_discrete_set

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def cmd_set(name, valstr):
    cmd = "> (param-set! '"
    cmd += name + ' ' + valstr
    cmd += ")\n"
    return cmd


def cmd_get(name):
    cmd = "> (param-ref '"
    cmd += name
    cmd += ")\n"
    return cmd


def cmd_cmd(name):
    cmd = "> (exec '"
    cmd += name
    cmd += ")\n"
    return cmd


def str2bool(value_str):
    return True if value_str == '#t' else False


def bool2str(value_bool):
    return '#t' if value_bool else '#f'


class TopticaCTL(Instrument):
    def __init__(self, adapter, **kwargs):
        super(TopticaCTL, self).__init__(
            TopticaAdapter(adapter), "TopticaCTL Tunable Laser Source",
            **kwargs)
    WAVELENGTH_RANGE = [1460, 1570]
    POWER_RANGE = [0.5, 60]

    state_dict = {'ERROR': -100,
                  'Standby': -90,
                  'Motor referencing and FLOW initialization in progress': -8,
                  'FLOW initialization in progress': -7,
                  'Motor not referenced, yet': -6,
                  'Motor referencing in progress': -5,
                  'Motor referenced': -4,
                  'Drift compensation in progress': -3,
                  'FLOW optimization in progress': -2,
                  'SMILE optimization in progress': -1,
                  'Idle/Stopped': 0,
                  'Target set wavelength is about to be reached': 1,
                  'Starting motor scan': 2,
                  'Scan in progress': 3,
                  'Restarting scan': 4,
                  'Paused': 5,
                  'Remotely controlled': 6}

    state = Instrument.measurement(cmd_get('laser1:ctl:state'),
                                   """Parameter indicating the current state of \
                                   the CTL scan engine. """,
                                   values=state_dict,
                                   map_values=True)

    emission = Instrument.measurement(cmd_get('emission'),
                                      """ Parameter indicating whether laser \
                                      emission is switched on.""",
                                      get_process=str2bool)

    wavelength = Instrument.measurement(cmd_get('laser1:ctl:wavelength-act'),
                                        """ Current Wavelength reading \
                                        in nm.""")

    wavelength_set = \
        Instrument.control(cmd_get('laser1:ctl:wavelength-set'),
                           cmd_set('laser1:ctl:wavelength-set', '%g'),
                           """ Floating point property controlling the \
                           wavelength setpoint in nm. """,
                           validator=strict_range,
                           values=WAVELENGTH_RANGE)

    power = Instrument.measurement(cmd_get('laser1:ctl:power:power-act'),
                                   """ Parameter indicating the approximate \
                                   output power level of the CTL in mW.""")

    power_set = \
        Instrument.control(cmd_get('laser1:power-stabilization:setpoint'),
                           cmd_set('laser1:power-stabilization:setpoint',
                                   '%g'),
                           """ Parameter to specify the target power in mW.""",
                           validator=strict_range,
                           values=POWER_RANGE)

    power_stabilization = Instrument.control(
        cmd_get('laser1:power-stabilization:enabled'),
        cmd_set('laser1:power-stabilization:enabled', '%s'),
        """ Parameter to enable/disable the power stabilization.""",
        validator=strict_discrete_set,
        values=[True, False],
        set_process=bool2str,
        get_process=str2bool)

    scan_mode = Instrument.control(
        cmd_get('laser1:wide-scan:continuous-mode'),
        cmd_set('laser1:wide-scan:continuous-mode', '%s'),
        """ Parameter to enable/disable wide-scan repeat mode.""",
        validator=strict_discrete_set,
        values={'single': '#f', 'repeat': '#t'},
        map_values=True)

    scan_shape = Instrument.control(
        cmd_get('laser1:wide-scan:shape'),
        cmd_set('laser1:wide-scan:shape', '%d'),
        """ Parameter to enable/disable wide-scan repeat mode.""",
        validator=strict_discrete_set,
        values={'sawtooth': 0, 'triangle': 1},
        map_values=True)

    scan_state = Instrument.measurement(
        cmd_get('laser1:wide-scan:state'),
        """ Parameter indicating the current state of the wide-scan:
        0 - disabled
        1 - waiting for start condition to be reached
        2 - scan active
        3 - waiting for stop condition to be reached
        """,
        values={'disabled': 0,
                'waiting for start condition to be reached': 1,
                'scan active': 2,
                'waiting for stop condition to be reached': 3},
        map_values=True)

    scan_speed = Instrument.control(cmd_get('laser1:wide-scan:speed'),
                                    cmd_set('laser1:wide-scan:speed', '%g'),
                                    """control speed of widescan.""")

    piezo_frequency = Instrument.control(
        cmd_get('laser1:scan:frequency'),
        cmd_set('laser1:scan:frequency', '%f'),
        """ Parameter to control the scan \
        frequency (in Hz) for piezo-scannig.""")
    piezo_Vpp = Instrument.control(
        cmd_get('laser1:scan:amplitude'),
        cmd_set('laser1:scan:amplitude', '%f'),
        """ Parameter to control the peak-to-peak \
        amplitude of the piezo-scan.""")
    piezo_Vo = Instrument.control(
        cmd_get('laser1:scan:offset'),
        cmd_set('laser1:scan:offset', '%f'),
        """ Parameter to control the offset of the piezo-scan.""")

    piezo_start = Instrument.control(
        cmd_get('laser1:scan:start'),
        cmd_set('laser1:scan:start', '%f'),
        """ Parameter to control the start value of the piezo-scan period.""")
    piezo_stop = Instrument.control(
        cmd_get('laser1:scan:stop'),
        cmd_set('laser1:scan:stop', '%f'),
        """ Parameter to control the stop value of the piezo-scan period.""")

    piezo_signal = Instrument.control(
        cmd_get('laser1:scan:signal-type'),
        cmd_set('laser1:scan:signal-type', '%g'),
        """ Parameter to specify the waveform of the scan signal.
        0: sine
        1: triangle
        2: triangle rounded
        """,
        validator=strict_discrete_set,
        values=[0, 1, 2])

    piezo_enabled = Instrument.control(
        cmd_get('laser1:scan:enabled'),
        cmd_set('laser1:scan:enabled', '%s'),
        """ Parameter to enable/disable the signal generator.""",
        validator=strict_discrete_set,
        values=[True, False],
        set_process=bool2str,
        get_process=str2bool)

    def scan_setup(self, wl_start, wl_stop, speed, trigger=True,
                   trigger_wl=None, shape='sawtooth', mode='single'):
        self.write(cmd_set('laser1:wide-scan:scan-begin', str(wl_start)))
        self.write(cmd_set('laser1:wide-scan:scan-end', str(wl_stop)))
        self.write(cmd_set('laser1:wide-scan:speed', str(speed)))

        self.write(cmd_set('laser1:wide-scan:trigger:output-enabled',
                   bool2str(trigger)))
        if trigger:
            if trigger_wl is None:
                self.write(cmd_set('laser1:wide-scan:scan-begin',
                           str(wl_start-1*speed)))
                self.write(cmd_set('laser1:wide-scan:trigger:output-threshold',
                           str(wl_start)))
            else:
                self.write(cmd_set('laser1:wide-scan:trigger:output-threshold',
                           trigger_wl))

        self.scan_shape = shape
        self.scan_mode = mode

    def start_scan(self):
        self.write(cmd_cmd('laser1:wide-scan:start'))

    def stop_scan(self):
        self.write(cmd_cmd('laser1:wide-scan:stop'))

    def __del__(self):
        self.close()

    def close(self):
        self.adapter.connection.close()
