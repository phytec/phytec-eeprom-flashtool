#!/usr/bin/env python3

import os
import sys

from setuptools import setup, find_packages

# Tool version is defined in phytec_eeprom_flashtool/src/__init__.py

def read(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with open(os.path.join(here, rel_path)) as fp:
        return fp.read()


def get_version(rel_path: str) -> str:
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            # __version__ = "0.9"
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

if __name__ == "__main__":
    setup(
        name='phytec-eeprom-flashtool',
        version=get_version('phytec_eeprom_flashtool/src/__init__.py'),
        description='PHYTEC EEPROM Flashtool',
        packages=find_packages(),
        include_package_data=True,
        package_data={'': ['**/*.yml', '**/*.rst']},
        author='PHYTEC Holding AG',
        author_email='support@phytec.de',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
            "Typing :: Typed",
        ],
        python_requires='>=3.9',
        install_requires=['pyyaml', 'smbus2', 'crc8'],
        entry_points={
            'console_scripts': ['phytec_eeprom_flashtool = phytec_eeprom_flashtool.__main__:cmd_main']
        },
    )
