"""Tests for the cli calls"""
import subprocess

def test_cli_version():
    command = ['phytec_eeprom_flashtool', '-v']
    print(" ".join(command))
    result = subprocess.run(command, stdout=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout.decode('utf-8').startswith('Version: ')

def test_cli_version():
    command = ['phytec_eeprom_flashtool', '--version']
    print(" ".join(command))
    result = subprocess.run(command, stdout=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout.decode('utf-8').startswith('Version: ')

def test_cli_display():
    command = ['phytec_eeprom_flashtool', 'display', '-som', 'PCL-066', '-kit', '3022210I-0',
        '-bom', 'A0', '-pcb', '1a']
    print(" ".join(command))
    result = subprocess.run(command)
    assert result.returncode == 0

def test_cli_create():
    command = ['phytec_eeprom_flashtool', 'create', '-som', 'PCL-066', '-kit', '3022210I-0',
        '-bom', 'A0', '-pcb', '1a']
    print(" ".join(command))
    result = subprocess.run(command)
    assert result.returncode == 0
