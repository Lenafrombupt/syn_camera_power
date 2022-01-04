try:
    import ongpym
    del ongpym
except ImportError:
    from pathlib import Path
    file = Path(__file__). resolve()
    package_root_directory = str(file)[:str(file).find('ONGPyMeasureSuite')] \
        + 'ONGPyMeasureSuite'
    exec(open(str(package_root_directory)+'/initialize.py').read())

import os
import sys


import logging
from pymeasure.display.windows import ManagedWindow

from pymeasure.experiment import Procedure, Results
from pymeasure.experiment import (FloatParameter, BooleanParameter,
                                  IntegerParameter)
from pymeasure.experiment.results import unique_filename
from pymeasure.experiment.parameters import Parameter

from ongpym.instruments.tektronix.mdo3052 import MDO3052
from ongpym.instruments.toptica.topticactl import TopticaCTL
from ongpym.config import ADDRESS_MDO3052, ADDRESS_TOPTICACTL, PATH_TRASH

from scipy.signal import find_peaks
from lmfit.models import LinearModel, LorentzianModel
import matplotlib.pyplot as plt
import numpy as np
from time import sleep

sys.modules['cloudpickle'] = None
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def fitter(x, y, double, x_original):
    """
    Parameters
    ----------
    x : TYPE
        Values for the x axis.
    y : TYPE
        Values for the y axis.
    double : TYPE
        Is True if two peaks are given.
    x_original : TYPE
        The whole values for the x axis.

    Returns
    -------
    val : TYPE
        [FSR,Q,Q2,lam,lam2,FWHM,FWHM2].
    fit : TYPE
        Fitted data points.

    """
    if double:
        peaks, _ = find_peaks(-y, distance=len(y)/2)

        mu = x[peaks]

        lor_mod = LorentzianModel(prefix='lor_')
        line_mod = LinearModel(prefix='line_')
        lor2_mod = LorentzianModel(prefix='lor2_')

        pars = lor_mod.guess(y, x=x, negative=True, center=mu[0])
        pars += lor2_mod.guess(y, x=x, negative=True, center=mu[1])
        pars += line_mod.guess(y, x=x)

        mod = lor_mod+line_mod+lor2_mod

        out = mod.fit(y, pars, x=x)

        fit = mod.eval(out.params, x=x_original)

    else:
        peaks, _ = find_peaks(-y, distance=len(y))

        mu = x[peaks]

        lor_mod = LorentzianModel(prefix='lor_')
        line_mod = LinearModel(prefix='line_')

        pars = lor_mod.guess(y, x=x, negative=True, center=mu[0])
        pars += line_mod.guess(y, x=x)

        mod = lor_mod+line_mod

    out = mod.fit(y, pars, x=x)

    fit = mod.eval(out.params, x=x_original)

    FWHM = 2*out.best_values['lor_sigma']
    lam = out.best_values['lor_center']
    Q = lam/FWHM

    if double:
        FSR = out.best_values['lor2_center'] - out.best_values['lor_center']
        lam2 = out.best_values['lor2_center']
        FWHM2 = 2*out.best_values['lor2_sigma']
        Q2 = lam2/FWHM2
        val = np.array([FSR, Q, Q2, lam, lam2, FWHM, FWHM2])
        return val, fit
    else:
        val = np.array([Q, lam, FWHM])
        return val, fit


def fitplot(name, directory, xvalue, yvalue, wl_start, wl_stop,
            logplot=False, fit=False, double=False, save=False):
    """
    Parameters
    ----------
    name : TYPE
        Name of the file.
    directory : TYPE
        Directroy of the file.
    xvalue : TYPE
        Values for the x axis.
    yvalue : TYPE
        Values for the y axis.
    wl_start : TYPE
        Where the start of the scan was.
    wl_stop : TYPE
        Where the stop of the scan was.
    logplot : TYPE, optional
        Is true if the plot is a log plot. The default is False.
    fit : TYPE, optional
        Is true if one peak should be fitted. The default is False.
    double : TYPE, optional
        Is true if two peaks should be fitted. The default is False.
    save : TYPE, optional
        Is True if the plot should be saved. The default is False.

    Returns
    -------
    fit_values : TYPE
        [FSR,Q,Q2,lam,lam2,FWHM,FWHM2].
    fit_curve : TYPE
        Fitted data.

    """

    b = np.argwhere(xvalue >= wl_start)[:, 0]
    c = np.argwhere(xvalue[b] <= wl_stop)[:, 0]

    x_fit = xvalue[b][c]
    y_fit = yvalue[b][c]

    if fit or double:
        fit_values, fit_curve = fitter(x_fit, y_fit, double, xvalue)

    if save:
        fig, ax = plt.subplots()
        ax.set(xlabel='Wavelength [nm]',
               title='transmission experiment of: ' + str(name))
        if logplot:
            ax.plot(xvalue, 10.0*np.log10(yvalue), '.k')
            ax.set_ylabel('Signal [dB]')
            if fit or double:
                if double:
                    ax.plot(xvalue, 10*np.log10(fit_curve), '--r',
                            label='FSR=' + str(int(fit_values[0]*10000)/10)
                            + ' pm\nQ1=' + str(int(fit_values[1]*10)/10)
                            + '\nQ2=' + str(int(fit_values[2]*10)/10)
                            + '\nFWHM1=' + str(int(fit_values[5]*10000)/10)
                            + ' pm \nFWHM2=' + str(int(fit_values[6]*10000)/10)
                            + ' pm\n$\lambda$1='
                            + str(int(fit_values[3]*100)/100)
                            + ' nm'+' \n$\lambda$2='
                            + str(int(fit_values[4]*100)/100) + ' nm')

                else:
                    ax.plot(xvalue, 10*np.log10(fit_curve), '--r',
                            label='Q=' + str(int(fit_values[0]*10)/10)
                            + '\nFWHM=' + str(int(fit_values[2]*10000)/10)
                            + ' pm\n$\lambda$='
                            + str(int(fit_values[1]*100)/100) + ' nm')
        else:
            ax.plot(xvalue, yvalue, '.k')
            ax.set_ylabel('Voltage[V]')
            if fit or double:
                if double:
                    ax.plot(xvalue, fit_curve, '--r',
                            label='FSR=' + str(int(fit_values[0]*10000)/10)
                            + ' pm\nQ1=' + str(int(fit_values[1]*10)/10)
                            + '\nQ2=' + str(int(fit_values[2]*10)/10)
                            + '\nFWHM1=' + str(int(fit_values[5]*10000)/10)
                            + ' pm \nFWHM2=' + str(int(fit_values[6]*10000)/10)
                            + ' pm\n$\lambda$1='
                            + str(int(fit_values[3]*100)/100) + ' nm'
                            + ' \n$\lambda$2='
                            + str(int(fit_values[4]*100)/100) + ' nm')

                else:
                    ax.plot(xvalue, fit_curve, '--r',
                            label='Q=' + str(int(fit_values[0]*10)/10)
                            + '\nFWHM=' + str(int(fit_values[2]*10000)/10)
                            + ' pm\n$\lambda$='
                            + str(int(fit_values[1]*100)/100) + ' nm')

        ax.legend()
        plt.savefig(directory)

    if fit or double:
        return fit_values, fit_curve
    else:
        return 0, xvalue*0


def plot_name(file):
    """
    Parameters
    ----------
    file : TYPE
        path of the csv file.

    Returns
    -------
    TYPE
        returns the same directory for the file, but now for .png data.

    """
    return os.path.abspath(file[:-3] + 'png')


def unique(dic, filename, count):
    """
    Parameters
    ----------
    dic : TYPE
        Directrory of the file.
    filename : TYPE
        the filename.
    count : TYPE
        a integer which is added behinde the name.

    Returns
    -------
    file_n : TYPE
        a unique filename in the given directory.

    """
    dic_n = os.path.abspath(dic)
    file = os.path.join(dic_n, filename + '_' + str(count) + '.csv')
    file_n = file
    i = 0
    while os.path.exists(file_n):
        i += 1
        file_n = file[:-4] + '_' + str(i) + '.csv'

    return file_n


def nosampl_validator(nofsampl):
    if nofsampl >= 1:
        nofsampl_new = 1
    if 1 < nofsampl <= 10:
        nofsampl_new = 10
    if nofsampl >= 100:
        nofsampl_new = 100
    return nofsampl_new


class transmission_experiment(Procedure):
    wl_start = FloatParameter('start wavelength [nm]', minimum=1460.0,
                              maximum=1570.0, default=1555.0)
    wl_stop = FloatParameter('stop wavelength [nm]', minimum=1460.0,
                             maximum=1570.0, default=1556.0)
    speed = FloatParameter('speed [nm/s]', maximum=5.0, default=0.1)

    laserpower = FloatParameter('laserpower [mW]', default=60, maximum=60.0)

    auto_scale = BooleanParameter('autoscale', default=False)
    vertic = FloatParameter('scale [mV]', minimum=1, maximum=1e4, default=50)

    vertic1_off = FloatParameter('offset in devisions', default=-4)

    nofsampl = IntegerParameter('No. of samples in 1000 (1,10,100)',
                                default=10)

    saveplot = BooleanParameter('save plot', default=True)
    yscalelog = BooleanParameter('logscale plot', default=False)

    fit_data = BooleanParameter('fit one peak', default=False)
    fit_double = BooleanParameter('fit two peaks', default=False)

    averig = BooleanParameter('average', default=False)

    avnom = IntegerParameter('Average cycles', default=5)

    dicforplot = Parameter('', default='empty')

    name = Parameter('filename', 'noname')

    DATA_COLUMNS = ['Wavelength', 'Voltage', 'Triggervoltage',
                    'fit', 'time_orig']

    def startup(self):
        """
        Returns
        -------
        None.

        """
        nofsampl_new = nosampl_validator(self.nofsampl)

        log.info("Connecting to laser and setting it up")

        self.laser = TopticaCTL(ADDRESS_TOPTICACTL)

        self.laser.power_stabilization = True
        self.laser.wavelength_set = self.wl_start
        self.laser.power_set = self.laserpower

        log.info("Connecting to osciloscope and setting it up")

        self.osci = MDO3052(ADDRESS_MDO3052)
        if self.auto_scale:
            vscale_new = self.osci.get_scale()

        self.laser.wavelength_set = self.wl_start-1*self.speed

        log.info("making the laser scan setup")
        self.laser.scan_setup(self.wl_start, self.wl_stop,
                              self.speed, trigger=True)
        self.emit('progress', 30.0)
        self.osci.reset()
        self.osci.select()

        self.osci.acqu_state = 0
        self.osci.singelrun = 'SEQ'

        self.osci.acquirereclen = nofsampl_new*1000
        self.osci.triggertyp = 'EDG'
        self.osci.triggermode = 'NORM'
        self.osci.triggersource = 'CH2'
        self.osci.triggerslope = 'RIS'
        self.osci.acqidilaymode = 'OFF'
        self.osci.termination1 = 'FIF'

        self.osci.horizontalpos = 10

        self.osci.verscale2 = 1
        self.osci.triggerlevel2 = 2.5
        if self.auto_scale:
            self.osci.verscale1 = vscale_new
        else:
            self.osci.verscale1 = self.vertic/1000

        self.osci.verpos1 = self.vertic1_off
        self.emit('progress', 40.0)

    def execute(self):
        """
        Returns
        -------
        None.

        """
        nofsampl_new = nosampl_validator(self.nofsampl)
        mtime = (self.wl_stop-self.wl_start)/self.speed

        htime = mtime

        log.info("set osci to the right timescale")
        self.osci.horizontalscal = (mtime)/9.0
        while self.osci.horizontalscal < mtime/9.0:
            htime += (0.1*mtime)
            self.osci.horizontalscal = (htime)/9.0

        if self.averig:
            rep = self.avnom
        else:
            rep = 1

        new_rec = nofsampl_new*1000
        self.emit('progress', 41.0)

        d = np.zeros(new_rec)
        trig = np.zeros(new_rec)

        for i in range(rep):
            log.info('started '+str(i+1)+'. repetition')

            self.osci.acqu_state = 1
            log.info('Osciloscope ready and waiting for trigger')

            sleep(0.8*htime+2)
            self.laser.start_scan()
            log.info('Laserscan started')
            k = 0

            while self.osci.acqu_state == 1.0:
                log.info('scan in progress')
                sleep(2)
                k += 2
                if 60+k/2 <= 99.0:
                    self.emit('progress', 41.0+i/2)
                if k >= 80:
                    log.info('push stop on osci to end your measurement, \
                             if the plot on the osci is visible')

            log.info('PC extracts data from osciloscope')

            d += self.osci.getwaveform(1, new_rec, channel='CH1')
            trig += self.osci.getwaveform(1, new_rec, channel='CH2')

        self.emit('progress', 99.0)
        log.info('scaling of data')
        tstart, tscale, rec = self.osci.get_timescale()
        t = np.linspace(tstart, tstart+rec*tscale, rec)
        wavelength = t*self.speed+self.wl_start
        vscale, voff, vpos = self.osci.get_vscale('CH1')
        trscale, troff, trpos = self.osci.get_vscale('CH2')

        scaled = (d/rep-vpos)*vscale-voff
        trscaled = ((trig/rep-trpos)*trscale-troff)

        log.info('plotting and postprocessing of data started')

        fit_values, fit_curve = fitplot(self.name, self.dicforplot, wavelength,
                                        scaled, self.wl_start, self.wl_stop,
                                        logplot=self.yscalelog,
                                        fit=self.fit_data,
                                        double=self.fit_double,
                                        save=self.saveplot)

        log.info('plotting and postprocessing done')

        log.info('emiting data to the file')
        for i in range(len(scaled)):
            data = {
                'Wavelength': wavelength[i],
                'Voltage': scaled[i],
                'Triggervoltage': trscaled[i],
                'fit': fit_curve[i],
                'time_orig': t[i]
            }
            self.emit('results', data)

            if self.should_stop():
                break
        log.info('emitting data done')

        self.emit('progress', 100.0)

    def shutdown(self):
        """
        Returns
        -------
        None.

        """

        self.laser.power_set = self.laserpower
        self.laser.close()


class transmission_interface(ManagedWindow):

    def __init__(self):
        super(transmission_interface, self).__init__(
            procedure_class=transmission_experiment,
            inputs=['wl_start', 'wl_stop', 'speed', 'laserpower',
                    'averig', 'avnom', 'saveplot', 'yscalelog',
                    'fit_data', 'fit_double', 'nofsampl', 'auto_scale',
                    'vertic', 'name'],
            displays=['wl_start', 'wl_stop', 'speed', 'nofsampl'],
            x_axis='Wavelength',
            y_axis='Voltage',
            directory_input=True,
            sequencer=True,
            sequencer_inputs=['wl_start', 'wl_stop', 'speed']
        )
        self.setWindowTitle('Widescan')

    runner = 0

    def queue(self, *, procedure=None):
        """
        Parameters
        ----------
        * : TYPE
            DESCRIPTION.
        procedure : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """

        directory = self.directory

        if procedure is None:
            procedure = self.make_procedure()

        if directory == '':
            directory = PATH_TRASH

        if procedure.name == 'noname':
            filename = unique_filename(directory,
                                       suffix='_'+str(self.runner),
                                       datetimeformat="%Y_%m_%d",
                                       index=True)

        else:
            filename = unique(directory, str(procedure.name), str(self.runner))

        plotname = plot_name(filename)
        self.runner += 1

        if procedure.wl_start < procedure.wl_stop:
            try:
                TopticaCTL(ADDRESS_TOPTICACTL)
            except RuntimeError:
                log.info('laser not connected')
                return
            try:
                osci = MDO3052(ADDRESS_MDO3052)
                osci.horizontalscal
            except RuntimeError:
                log.info('Oscilloscope is not connected')
                return
            procedure.dicforplot = plotname
            results = Results(procedure, filename)
            experiment = self.new_experiment(results)

            self.manager.queue(experiment)
        else:
            log.info('start wavelangth must be smaller than stop wavelength')


if __name__ == "__main__":
    from pymeasure.display.Qt import QtGui

    app = QtGui.QApplication(sys.argv)
    window = transmission_interface()
    window.show()
    sys.exit(app.exec_())
