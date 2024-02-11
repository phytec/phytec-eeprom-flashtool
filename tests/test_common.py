import pytest
from phytec_eeprom_flashtool.src.common import str_to_revision
from phytec_eeprom_flashtool.src.common import sub_revision_to_str
from phytec_eeprom_flashtool.src.common import crc8_checksum_calc


@pytest.mark.parametrize("value, expect", [
    ("1", (1, '0000')),
    ("1a", (1, '0001')),
    ("3a", (3, '0001')),
    ("3b", (3, '0010')),
    ("3o", (3, '1111')),
])
def test_str_to_revision(value, expect):
    """test str_to_revision"""
    revs = str_to_revision(value)
    assert revs == expect

@pytest.mark.parametrize("value", [
    ("3p"),
])
def test_str_to_revision_failure(value):
    """test str_to_revision"""
    with pytest.raises(ValueError):
        str_to_revision(value)


@pytest.mark.parametrize("value, expect", [
    ("0001", ('a')),
])
def test_sub_revision_to_str(value, expect):
    """test sub_revision_to_str"""
    revs = sub_revision_to_str(value)
    assert revs == expect


@pytest.mark.parametrize("value, expect", [
    (bytes("cafe", 'utf-8'), 118),
])
def test_crc8_checksum_calc(value, expect):
    """test crc8_checksum_calc"""
    crc8 = crc8_checksum_calc(value)
    assert crc8 == expect, f"CRC8 doesn't match. Expected {expect} but calculated {crc8}"
    assert not crc8_checksum_calc(value + bytes(chr(crc8), 'utf-8'))
