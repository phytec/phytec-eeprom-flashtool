#!/usr/bin/env python3

from setuptools import setup

def get_version():
    return '3.1.0'

if __name__ == "__main__":
    setup(
        name='eeprom-flashtool',
        version=get_version(),
        description='PHYTEC EEPROM Flashtool',
        packages=['src', 'configs'],
        author='PHYTEC America, LLC',
        author_email='mmckee@phytec.com',
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            "Typing :: Typed",
        ],
        python_requires='>=3.8',
        install_requires=['pyyaml', 'smbus2', 'crc8'],
        scripts=['src/phytec_eeprom_flashtool.py'],
        entry_points={},
        include_package_data=True,
    )
