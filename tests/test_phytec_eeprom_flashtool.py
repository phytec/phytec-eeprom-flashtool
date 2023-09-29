import pytest
import yaml
import os
import sys

sys.path.append('../src')
sys.path.append('src')
import phytec_eeprom_flashtool

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

    config_file = open(yml_file, 'r')
    yml_parser = yaml.safe_load(config_file)
    config_file.close()
    pytest.OUTPUT_STRINGS = yml_parser['Output_strings']
    return yml_parser['Test_data']

def test_read(test_data, capsys):
    file = os.path.join(TESTDATA_PATH, test_data['file_name'])
    args = ['-o', 'read'] + test_data['read_args'].split() + ['-file', file]
    phytec_eeprom_flashtool.main(args)
    captured = capsys.readouterr()
    output = captured.out.splitlines()
    output = [x.strip() for x in output]
    try:
        for name, out_string in pytest.OUTPUT_STRINGS.items():
            search_string = out_string.format(test_data['data'][name])
            index = output.index(search_string)
            del output[index]
    except ValueError as err:
        pytest.fail('Output not found: {0}\nOutput:\n{1}'.format(err, output))
    search_string = "CRC8-Checksum correct if 0: {0}".format(test_data['data']['crc'])
    index = output.index(search_string)
    del output[index]

def test_create(test_data, capsys, tmp_path):
    if not ('create_args' in test_data):
        pytest.skip("create_args missing")
    bin_file_name = os.path.join(tmp_path, "eeprom_data.bin")
    args = ['-o', 'create'] + test_data['create_args'].split() + ['-file', bin_file_name]
    phytec_eeprom_flashtool.main(args)
    captured = capsys.readouterr()
    output = captured.out.splitlines()
    output = [x.strip() for x in output]
    for name, out_string in pytest.OUTPUT_STRINGS.items():
        search_string = out_string.format(test_data['data'][name])
        index = output.index(search_string)
        del output[index]
    bin_check_file_name = os.path.join(TESTDATA_PATH, test_data['file_name'])
    file1 = open(bin_file_name, "rb").read()
    file2 = open(bin_check_file_name, "rb").read()
    assert file1 == file2

