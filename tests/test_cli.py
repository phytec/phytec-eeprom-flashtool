"""Tests for the cli calls"""
import subprocess

def test_cli_display():
    command = ['phytec_eeprom_flashtool.py', 'display', '-som', 'PCL-066', '-kit', '3022210I',
        '-bom', 'A0', '-rev', '1a']
    print(" ".join(command))
    result = subprocess.run(command)
    assert result.returncode == 0
