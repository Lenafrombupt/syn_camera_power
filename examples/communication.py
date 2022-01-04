try:
    import ongpym
    del ongpym
except ImportError:
    from pathlib import Path
    file = Path(__file__). resolve()
    package_root_directory = str(file)[:str(file).find('ONGPyMeasureSuite')] \
        + 'ONGPyMeasureSuite'
    exec(open(str(package_root_directory)+'/initialize.py').read())

from ongpym.instruments.tektronix.mdo3052 import MDO3052

from ongpym.config import ADDRESS_MDO3052

osc = MDO3052(ADDRESS_MDO3052)
