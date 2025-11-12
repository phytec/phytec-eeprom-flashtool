# SPDX-FileCopyrightText: 2025 PHYTEC
#
# SPDX-License-Identifier: MIT

"""Module with common functions."""
import re
from pathlib import Path
import crc8  # type: ignore
import yaml

REV_A_OFFSET = ord('a') - 1


def str_to_revision(revision_str: str) -> tuple[int, str]:
    """Converts a string into a tuple of revision and sub revision."""
    rev_digits = len(revision_str)
    rev_digits_re = re.search(r'[^0-9]', revision_str)
    if rev_digits_re is not None:
        rev_digits = rev_digits_re.start()
    revision = int(revision_str[0:rev_digits])
    sub_revision = 0
    if len(revision_str) > rev_digits:
        sub_revision = ord(revision_str[rev_digits]) - REV_A_OFFSET
    if sub_revision > 15:
        raise ValueError("PCB subversion has to be a character between 'a' and 'o'!")
    return revision, format(sub_revision, '04b')


def sub_revision_to_str(sub_revision: int | str) -> str:
    """Converts a sub revision into a string."""
    if int(sub_revision) <= 0:
        return "0"

    if isinstance(sub_revision, str):
        sub_revision = chr(int(sub_revision, 2) + REV_A_OFFSET)
    return str(sub_revision)


def crc8_checksum_calc(eeprom_struct: bytes) -> int:
    """Create a CRC8 checksum from the packed EEPROM data."""
    hash_ = crc8.crc8()
    hash_.update(eeprom_struct)
    crc8_sum = hash_.hexdigest()
    return int(crc8_sum, 16)


def hw8_checksum_calc(eeprom_struct: bytes) -> int:
    """Calculates the total number of bits set to 1 in the given EEPROM data."""
    return sum(bin(field).count("1") for field in eeprom_struct)


def get_max_option_count() -> int:
    """Returns the maximum allowed number of product options."""
    config_path = Path(__file__).parent.parent / 'constants.yml'
    with open(config_path, 'r', encoding='UTF-8') as config_file:
        config = yaml.safe_load(config_file)
        return config['MAX_OPTION_COUNT']
