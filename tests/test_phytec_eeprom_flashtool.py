# SPDX-FileCopyrightText: 2025 PHYTEC
#
# SPDX-License-Identifier: MIT

import pytest
import yaml
import os
import sys
import subprocess
import shutil

from phytec_eeprom_flashtool.src.io import YML_DIR

TESTDATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata')

def pytest_configure():
    pytest.OUTPUT_STRINGS = {}

@pytest.fixture()
def test_data(request):
    return request.param

def pytest_generate_tests(metafunc):
    if 'test_data' not in metafunc.fixturenames:
        return
    testdata = get_test_data('test_data.yaml')
    metafunc.parametrize('test_data', testdata, indirect=True)

def get_test_data(test_data):
    yml_file = os.path.join(TESTDATA_PATH, test_data)

    with open(yml_file) as config_file:
        yml_parser = yaml.safe_load(config_file)
    pytest.OUTPUT_STRINGS = yml_parser['Output_strings']
    return yml_parser['Test_data']

def get_product_api_version(test_data):
    """Returns the API version the product of a test data entry is configured for."""
    som_type = test_data['data']['som_type'].split('-')[0]
    base_article_number = test_data['data']['base_article_number']
    yml_file = YML_DIR / f'{som_type}-{base_article_number:03d}.yml'
    with open(yml_file) as config_file:
        return int(yaml.safe_load(config_file)['PHYTEC'].get('api', 2))

def get_legacy_test_data():
    """Returns all test data entries with EEPROM data in API v2 format on a product which is
       configured for API v3."""
    return [test_data for test_data in get_test_data('test_data.yaml')
            if test_data['data']['api_version'] == 2 and get_product_api_version(test_data) == 3]

def get_api_v3_test_data():
    """Returns all test data entries with EEPROM data in API v3 format."""
    return [test_data for test_data in get_test_data('test_data.yaml')
            if test_data['data']['api_version'] == 3 and 'create_args' in test_data]

def data_file_id(test_data):
    return test_data['file_name']

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
    result = subprocess.run(command, capture_output=True)
    if file.endswith("_bad_crc"):
        assert result.returncode == 1
        output = result.stderr.decode('utf-8').split('\n')
        output = [s.strip() for s in output]
        assert "Error: Checksum mismatch in the first 32 bytes!" in output
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

@pytest.mark.parametrize('legacy_data', get_legacy_test_data(), ids=data_file_id)
def test_block_commands_on_legacy_eeprom_data_fail(legacy_data, tmp_path):
    """Block commands must fail with a migration hint on legacy API v2 EEPROM data."""
    # The block commands resolve '-file' for both reading and writing, so a regression would
    # overwrite the tracked test data.
    file = shutil.copyfile(os.path.join(TESTDATA_PATH, legacy_data['file_name']),
                           os.path.join(tmp_path, legacy_data['file_name']))
    som_args = legacy_data['read_args'].split() + ['-file', file]
    with open(file, 'rb') as image:
        content_before = image.read()
    sub_commands = [
        ['add-mac', '0', '12:34:56:78:9a:bc'],
        ['read-mac', '0'],
        ['add-serial', '1234567890'],
        ['read-serial'],
        ['add-key-value', 'key', 'value'],
        ['read-key-value', 'key'],
    ]
    for sub_command in sub_commands:
        command = ['phytec_eeprom_flashtool'] + sub_command + som_args
        print(" ".join(command))
        result = subprocess.run(command, capture_output=True)
        assert result.returncode != 0, f"{' '.join(command)} must not succeed on v2 data!"
        stderr = result.stderr.decode('utf-8')
        assert "are only supported with API v3, but the EEPROM data is in API v2 format." \
            in stderr, f"Missing migration hint: {stderr}"
        assert "Please migrate the data to API v3 first with the 'write' command." in stderr
    with open(file, 'rb') as image:
        assert content_before == image.read()


@pytest.mark.parametrize('v3_data', get_api_v3_test_data(), ids=data_file_id)
def test_block_commands_on_v3_eeprom_data(v3_data, tmp_path):
    """Creates API v3 EEPROM data and adds a MAC block. This is the migration path for
       boards with legacy API v2 EEPROM data."""
    file = os.path.join(tmp_path, "eeprom_data.bin")
    command = ['phytec_eeprom_flashtool', 'create'] + v3_data['create_args'].split() + \
        ['-file', file]
    print(" ".join(command))
    result = subprocess.run(command, capture_output=True)
    assert result.returncode == 0

    som_args = v3_data['read_args'].split() + ['-file', file]
    command = ['phytec_eeprom_flashtool', 'add-mac', '0', '12:34:56:78:9a:bc'] + som_args
    print(" ".join(command))
    result = subprocess.run(command, capture_output=True)
    assert result.returncode == 0

    command = ['phytec_eeprom_flashtool', 'read-mac', '0'] + som_args
    print(" ".join(command))
    result = subprocess.run(command, capture_output=True)
    assert result.returncode == 0
    assert "12:34:56:78:9a:bc" in result.stdout.decode('utf-8')


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
