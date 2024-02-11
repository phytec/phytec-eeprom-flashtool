#!/usr/bin/env python3

from setuptools import setup
from setuptools import find_packages

def get_version():
    return '3.1.0'

if __name__ == "__main__":
    setup(
        name='phytec-eeprom-flashtool',
        version=get_version(),
        description='PHYTEC EEPROM Flashtool',
        packages=find_packages(),
        include_package_data=True,
        package_data={'': ['**/*.yml', '**/*.rst']},
        author='PHYTEC Holding AG',
        author_email='support@phytec.de',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            "Typing :: Typed",
        ],
        python_requires='>=3.8',
        install_requires=['pyyaml', 'smbus2', 'crc8'],
        entry_points={
            'console_scripts': ['phytec_eeprom_flashtool = phytec_eeprom_flashtool.__main__:cmd_main']
        },
    )
