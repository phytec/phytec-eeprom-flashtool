# SPDX-FileCopyrightText: 2025 PHYTEC
#
# SPDX-License-Identifier: MIT

"""Module to handle all blocks."""
#pylint: disable=import-error
from dataclasses import dataclass
import struct
import re

from .common import crc8_checksum_calc

# This sub version defines the available blocks. Increase this number when new blocks are
# available.
API_V3_SUB_VERSION = 0
# 1 uchar, 1 ushort, 1 uchar
API_V3_BLOCK_HEADER_ENCODING = "<1B1H1B"
API_V3_BLOCK_HEADER_SIZE = 4


@dataclass
class EepromV3BlockInterface:
    """Block interface to define the block header and the API to print and pack each block."""

    def __init__(self, size: int, block_type: int, encoding: str, next_block: int = 0):
        self.length = size + 4
        self.block_type = block_type
        self.encoding = API_V3_BLOCK_HEADER_ENCODING + encoding
        self.next_block = next_block
    crc8_header: int = 0
    crc8_payload: int = 0

    def pack_crc(self, eeprom_struct) -> bytes:
        """Generates CRC8 checksums for the block header and payload and includes them in the
        packed EEPROM data."""
        self.crc8_header = crc8_checksum_calc(eeprom_struct[:API_V3_BLOCK_HEADER_SIZE - 1])
        self.crc8_payload = crc8_checksum_calc(eeprom_struct[API_V3_BLOCK_HEADER_SIZE:-1])
        return eeprom_struct[:3] + struct.pack('B', self.crc8_header) + eeprom_struct[4:-1] + \
            struct.pack('B', self.crc8_payload)

    @staticmethod
    def unpack(eeprom_struct: bytes):
        """Static method to unpack the block header and generate a EepromV3BlockInterface obj."""
        unpacked = struct.unpack(API_V3_BLOCK_HEADER_ENCODING,
                                 eeprom_struct[:API_V3_BLOCK_HEADER_SIZE])
        if crc8_checksum_calc(eeprom_struct[:API_V3_BLOCK_HEADER_SIZE]):
            raise AssertionError("Block header crc8 mismatch!")
        return EepromV3BlockInterface(0, int(unpacked[0]), "", int(unpacked[1]))


########## API V3.0 ##########


@dataclass
class EepromDataMACBlock(EepromV3BlockInterface):
    """Block with a MAC adress and the Ethernet interface number it should get assigned to."""
    payload_length: int = 8
    payload_encoding: str = "1B6s1B"

    def __init__(self, interface: int, mac: str):
        super().__init__(self.payload_length, 0, self.payload_encoding)
        if interface < 0:
            raise ValueError("Ethernet interface number must be equal or greater then 0.")
        if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
            raise ValueError("MAC is not in XX:XX:XX:XX:XX:XX format.")
        self.interface = interface
        self.mac = mac.lower().split(':')

    def __repr__(self):
        header = "MAC Address block"
        return  f"""{header}
{'*' * len(header)}
{"Interface":16s}:  {self.interface}
{"MAC":16s}:  {':'.join(self.mac)}
{"CRC-Checksum":16s}:  0x{self.crc8_payload:x}"""

    def pack(self, next_block_address: int) -> bytes:
        """Pack the MAC block and generate both CRC8 checksums."""
        eeprom_struct = struct.pack(
            self.encoding,
            self.block_type,
            next_block_address,
            0, # skip CRC8
            self.interface,
            bytes.fromhex(format(int(''.join(self.mac), 16), '012x')),
            0, # skip CRC8
        )
        return self.pack_crc(eeprom_struct)

    @staticmethod
    def unpack(eeprom_struct: bytes):
        """Static method to unpack the MAC block and generate a EepromDataMACBlock object."""
        block_encoding = API_V3_BLOCK_HEADER_ENCODING + EepromDataMACBlock.payload_encoding
        block_size = API_V3_BLOCK_HEADER_SIZE + EepromDataMACBlock.payload_length
        unpacked = struct.unpack(block_encoding, eeprom_struct[:block_size])
        if crc8_checksum_calc(eeprom_struct[:block_size]):
            raise AssertionError("Block payload crc8 mismatch!")
        mac = unpacked[4].hex()
        mac = [mac[i:i+2] for i in range(0, len(mac), 2)]
        mac_block = EepromDataMACBlock(int(unpacked[3]), ':'.join(mac))
        mac_block.pack(int(unpacked[1]))
        return mac_block


def add_mac_block(eeprom_data, interface: int, mac: str):
    """Function to create a MAC block object and add it to the EEPROM data."""
    mac_block = EepromDataMACBlock(interface, mac)
    for block in [elm for elm in eeprom_data.blocks if isinstance(elm, EepromDataMACBlock)]:
        if block.mac == mac_block.mac:
            raise ValueError(f"EEPROM image already contains a MAC address with {block.mac}")
        if block.interface == mac_block.interface:
            raise ValueError(f"EEPROM image already contains a MAC of interface {block.interface}")
    mac_block.pack(eeprom_data.v3_next_block_address)
    eeprom_data.add_block(mac_block)


@dataclass
class EepromDataKeyValueBlock(EepromV3BlockInterface):
    """Block with a key value pair with up to 256 characters for both the key and value."""
    payload_length: int = 3
    payload_encoding: str = "2B{}s{}s1B"

    def __init__(self, key: str, value: str):
        encoding = self.payload_encoding.format(len(key), len(value))
        super().__init__(self.payload_length + len(key) + len(value), 1, encoding)
        if len(key) > 256:
            raise ValueError(f"Maximum key length is 256 characters. {len(key)} is too long.")
        if len(value) > 256:
            raise ValueError(f"Maximum value length is 256 characters. {len(value)} is too long.")
        self.key = key
        self.value = value

    def __repr__(self):
        header = "Key Value block"
        return  f"""{header}
{'*' * len(header)}
{"Key":16s}:  {self.key}
{"Value":16s}:  {self.value}
{"CRC-Checksum":16s}:  0x{self.crc8_payload:x}"""

    def pack(self, next_block_address: int) -> bytes:
        """Pack the key value block and generate both CRC8 checksums."""
        eeprom_struct = struct.pack(
            self.encoding,
            self.block_type,
            next_block_address,
            0, # skip CRC8
            len(self.key),
            len(self.value),
            bytes(self.key, 'utf-8'),
            bytes(self.value, 'utf-8'),
            0, # skip CRC8
        )
        return self.pack_crc(eeprom_struct)

    @staticmethod
    def unpack(eeprom_struct: bytes):
        """Static method to unpack the MAC block and generate a EepromDataMACBlock object."""
        # Only read first two uchars to get the key and value length
        block_encoding = API_V3_BLOCK_HEADER_ENCODING + "2Bx"
        block_size = API_V3_BLOCK_HEADER_SIZE + EepromDataKeyValueBlock.payload_length
        unpacked = struct.unpack(block_encoding, eeprom_struct[:block_size])
        # Unpack again with correct encoding format
        block_encoding = API_V3_BLOCK_HEADER_ENCODING + \
            EepromDataKeyValueBlock.payload_encoding.format(int(unpacked[3]), int(unpacked[4]))
        block_size = API_V3_BLOCK_HEADER_SIZE + EepromDataKeyValueBlock.payload_length + \
            int(unpacked[3]) + int(unpacked[4])
        unpacked = struct.unpack(block_encoding, eeprom_struct[:block_size])
        if crc8_checksum_calc(eeprom_struct[:block_size]):
            raise AssertionError("Block payload crc8 mismatch!")
        key_value_block = EepromDataKeyValueBlock(unpacked[5].decode('utf-8'),
                                                  unpacked[6].decode('utf-8'))
        key_value_block.pack(int(unpacked[1]))
        return key_value_block


def add_key_value_block(eeprom_data, key: str, value: str):
    """Function to create a key value block object and add it to the EEPROM data."""
    key_value_block = EepromDataKeyValueBlock(key, value)
    for block in [elm for elm in eeprom_data.blocks if isinstance(elm, EepromDataKeyValueBlock)]:
        if block.key == key_value_block.key:
            raise ValueError(f"EEPROM image already contains a key value pair for key {block.key}")
    key_value_block.pack(eeprom_data.v3_next_block_address)
    eeprom_data.add_block(key_value_block)


API_V3_BLOCK_MAPPING = {
    0: EepromDataMACBlock,
    1: EepromDataKeyValueBlock,
}


def unpack_block(eeprom_data, eeprom_blocks: bytes) -> int:
    """Function to unpack a block which is placed at the beginning of the bytes array. Returns the
    size of the unpacked block to point to the next block in the bytes array."""
    header = EepromV3BlockInterface.unpack(eeprom_blocks)
    block = API_V3_BLOCK_MAPPING[header.block_type].unpack(eeprom_blocks)  # type: ignore
    eeprom_data.add_block(block)
    return block.length
