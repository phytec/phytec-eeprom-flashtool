"""Module with common functions."""
import re
from typing import Union, Tuple
import crc8  # type: ignore

REV_A_OFFSET = ord('a') - 1


def str_to_revision(revision_str: str) -> Tuple[int, str]:
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


def sub_revision_to_str(sub_revision: Union[int, str]) -> str:
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
