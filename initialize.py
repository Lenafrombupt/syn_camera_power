import sys
from pathlib import Path


def initialize_ongpmsuite():
    file = Path(__file__). resolve()
    package_root_directory = str(file)[:str(file).find('ONGPyMeasureSuite')] \
        + 'ONGPyMeasureSuite'

    # package_root_directory = file.parents[0]
    sys.path.append(str(package_root_directory))
    print('Added '+str(package_root_directory)+' to "sys.path"')


if __name__ == '__main__':
    initialize_ongpmsuite()
    print("ONG PyMeasure Suite Initialized")
