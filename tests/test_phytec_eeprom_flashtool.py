import pytest
import yaml
import os
import sys
import subprocess

TESTDATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata')

def pytest_configure():
    pytest.OUTPUT_STRINGS = {}

@pytest.fixture()
def test_data(request):
    return request.param

def pytest_generate_tests(metafunc):
    testdata = get_test_data('test_data.yaml')
    metafunc.parametrize('test_data', testdata, indirect=True)

def get_test_data(test_data):
    yml_file = os.path.join(TESTDATA_PATH, test_data)

    with open(yml_file, 'r') as config_file:
        yml_parser = yaml.safe_load(config_file)
    pytest.OUTPUT_STRINGS = yml_parser['Output_strings']
    return yml_parser['Test_data']

def test_read(test_data, capsys):
    command = ['phytec_eeprom_flashtool', 'read'] + test_data['read_args'].split()
    read(test_data, command)

def test_autodetect(test_data, capsys):
    command = ['phytec_eeprom_flashtool', 'read']
    read(test_data, command)

def read(test_data, command):
    file = os.path.join(TESTDATA_PATH, test_data['file_name'])
    command = command + ['-file', file]
    print(command)
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if file.endswith("_bad_crc"):
        assert result.returncode == 1
        output = result.stderr.decode('utf-8').split('\n')
        output = [s.strip() for s in output]
        assert "AssertionError: API v2 crc8 mismatch!" in output
    else:
        assert result.returncode == 0
        output = result.stdout.decode('utf-8').split('\n')
        output = [s.strip() for s in output]
        print("\n".join(output))
        try:
            for name, out_string in pytest.OUTPUT_STRINGS.items():
                search_string = out_string.format(test_data['data'][name])
                index = output.index(search_string)
                del output[index]
        except ValueError as err:
            pytest.fail(f"Output not found: {err}\nOutput:\n{output}")

def test_create(test_data, capsys, tmp_path):
    if not ('create_args' in test_data):
        pytest.skip("create_args missing")
    bin_file_name = os.path.join(tmp_path, "eeprom_data.bin")
    command = ['phytec_eeprom_flashtool', 'create'] + test_data['create_args'].split() + \
        ['-file', bin_file_name]
    print(command)
    result = subprocess.run(command, stdout=subprocess.PIPE)
    assert result.returncode == 0
    output = result.stdout.decode('utf-8').split('\n')
    output = [s.strip() for s in output]
    print("\n".join(output))
    for name, out_string in pytest.OUTPUT_STRINGS.items():
        search_string = out_string.format(test_data['data'][name])
        index = output.index(search_string)
    bin_check_file_name = os.path.join(TESTDATA_PATH, test_data['file_name'])
    file1 = open(bin_file_name, "rb").read()
    file2 = open(bin_check_file_name, "rb").read()
    assert file1 == file2
