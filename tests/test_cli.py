"""Tests for the cli calls"""
import subprocess


def test_cli_directoy():
    command = "python3 src/phytec_eeprom_flashtool.py -d src/../configs/ display PCL-066-3022210I.A0 1"
    print(command)
    result = subprocess.run(command.split(' '))
    assert result.returncode == 0

def test_cli_display():
    command = "python3 src/phytec_eeprom_flashtool.py display PCL-066-3022210I.A0 1"
    print(command)
    result = subprocess.run(command.split(' '))
    assert result.returncode == 0
