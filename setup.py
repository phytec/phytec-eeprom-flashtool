#!/usr/bin/env python3

from setuptools import setup

def get_version():
    return '1.0.0'

if __name__ == "__main__":
    setup(
        name='eeprom-flashtool',
        version=get_version(),
        description='PHYTEC EEPROM Flashtool',
        packages=['src'],
        author='PHYTEC America, LLC',
        author_email='mmckee@phytec.com',
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
        ],
        python_requires='>=3.6',
        install_requires=['pyyaml', 'smbus2', 'crc8'],
        entry_points={},
        include_package_data=True,
    )
