#!/usr/bin/env python3
# Copyright (C) 2017-2023 PHYTEC America, LLC
""" PHYTEC-EEPROM-FLASHTOOL

    The tool is supposed to create, write, read and display the hardware introspection
    for our boards. The information is stored at a eeprom-id page and is necessary for
    our bootloader to boot up with the correct configuration. It is also a way to verify
    which board is used.

"""

import argparse

from .io import get_yml_parser
from .io import eeprom_write
from .io import eeprom_read
from .io import binary_write
from .io import binary_read
from .encoding import YmlParser
from .encoding import EepromData
from .encoding import EEPROM_V2_SIZE
from .encoding import EEPROM_V3_DATA_HEADER_SIZE
from .encoding import get_eeprom_data
from .encoding import eeprom_data_to_struct
from .encoding import eeprom_data_to_blocks
from .encoding import struct_to_eeprom_data
from .encoding import blocks_to_eeprom_data
from .encoding import print_eeprom_data
from .blocks import add_mac_block
from .blocks import add_key_value_block

def write_clearance() -> bool:
    """Notifies the user about potential risks and asks for the write clearance."""
    print("""You're about to flash a new image to the EEPROM!
Image data is read by our BSPs and flashing the wrong image
can lead to boot failure or misbehaving hardware.""")

    reply = str(input("Do you really want to continue? (y/N) ")).lower().strip()
    if reply in ('y', 'Y'):
        return True
    return False


def read_content(args, eeprom_data: EepromData, eeprom_size: int, offset: int = 0):
    """Helper to read either from a binary file or an EEPROM chip."""
    if "file" in args and args.file:
        return binary_read(args, eeprom_data, eeprom_size, offset)
    return eeprom_read(eeprom_data.yml_parser, eeprom_size, offset)


def write_content(args, eeprom_data: EepromData, eeprom_struct: bytes):
    """Helper to write either to a binary file or an EEPROM chip."""
    if "file" in args and args.file:
        binary_write(args, eeprom_data, eeprom_struct)
    else:
        flash_eeprom = True if "always_write" in args and args.always_write else write_clearance()
        if flash_eeprom:
            eeprom_write(eeprom_data.yml_parser, eeprom_struct)
            print('EEPROM flash successful!')
        else:
            print("Skipped flashing EEPROM!")


def read_eeprom_data(args, yml_parser: YmlParser, error: str) -> EepromData:
    """Helper to read either from a binary file or EEPROM chip and convert it into the eeprom
       data format."""
    eeprom_data = get_eeprom_data(args, yml_parser)
    if not eeprom_data.is_v3():
        raise ValueError(error)
    eeprom_size = EEPROM_V2_SIZE + EEPROM_V3_DATA_HEADER_SIZE
    eeprom_struct = read_content(args, eeprom_data, eeprom_size)
    eeprom_data = struct_to_eeprom_data(eeprom_struct, yml_parser)
    if eeprom_data.is_v3():
        eeprom_blocks = read_content(args, eeprom_data, eeprom_data.v3_payload_length, eeprom_size)
        eeprom_data = blocks_to_eeprom_data(eeprom_data, eeprom_blocks)
    return eeprom_data


def write_eeprom_data(args, eeprom_data: EepromData):
    """Helper to convert eeprom data into a struct with all blocks attached and writes to either
       a binary file or the EEPROM chip."""
    eeprom_struct = eeprom_data_to_struct(eeprom_data)
    if eeprom_data.is_v3():
        eeprom_struct += eeprom_data_to_blocks(eeprom_data)
    write_content(args, eeprom_data, eeprom_struct)
    print_eeprom_data(eeprom_data)


def read_som_config(args, yml_parser: YmlParser):
    """Reads from either a binary or an EEPROM device and prints the content."""
    eeprom_data = get_eeprom_data(args, yml_parser)
    eeprom_size = EEPROM_V2_SIZE + (EEPROM_V3_DATA_HEADER_SIZE if eeprom_data.is_v3() else 0)
    if "file" in args and args.file:
        eeprom_struct = binary_read(args, eeprom_data, eeprom_size)
    else:
        eeprom_struct = eeprom_read(yml_parser, eeprom_size)
    eeprom_data = struct_to_eeprom_data(eeprom_struct, yml_parser)
    if eeprom_data.is_v3():
        if "file" in args and args.file:
            eeprom_blocks = binary_read(args, eeprom_data, eeprom_data.v3_payload_length,
                                        eeprom_size)
        else:
            eeprom_blocks = eeprom_read(yml_parser, eeprom_data.v3_payload_length, eeprom_size)
        eeprom_data = blocks_to_eeprom_data(eeprom_data, eeprom_blocks)
    print_eeprom_data(eeprom_data)


def write_som_config(args, yml_parser: YmlParser):
    """Writes the EEPROM data into an EEPROM device."""
    eeprom_data = get_eeprom_data(args, yml_parser)
    eeprom_struct = eeprom_data_to_struct(eeprom_data)
    flash_eeprom = True if "always_write" in args and args.always_write else write_clearance()
    if flash_eeprom:
        eeprom_write(eeprom_data.yml_parser, eeprom_struct)
        print_eeprom_data(eeprom_data)
        print('EEPROM flash successful!')
    else:
        print_eeprom_data(eeprom_data)
        print("Skipped flashing EEPROM!")


def create_binary(args, yml_parser: YmlParser):
    """Creates a binary on a local file-system."""
    eeprom_data = get_eeprom_data(args, yml_parser)
    eeprom_struct = eeprom_data_to_struct(eeprom_data)
    binary_write(args, eeprom_data, eeprom_struct)
    print_eeprom_data(eeprom_data)


def display_som_config(args, yml_parser: YmlParser):
    """Prints EEPROM data without any read/write actions."""
    eeprom_data = get_eeprom_data(args, yml_parser)
    eeprom_data_to_struct(eeprom_data)
    print_eeprom_data(eeprom_data)


def write_mac_block(args, yml_parser: YmlParser):
    """Adds a MAC block to an existing binary file or updates an EEPROM device."""
    eeprom_data = read_eeprom_data(args, yml_parser, "MAC blocks are only supported with API v3")
    add_mac_block(eeprom_data, args.interface, args.mac)
    write_eeprom_data(args, eeprom_data)


def write_key_value_block(args, yml_parser: YmlParser):
    """Adds a key-value block to an existing binary file or updates an EEPROM device."""
    eeprom_data = read_eeprom_data(args, yml_parser,
                                   "Key Value blocks are only supported with API v3")
    add_key_value_block(eeprom_data, args.key, args.value)
    write_eeprom_data(args, eeprom_data)


def add_mandatory_arguments(parser):
    """Adds all mandatory arguments to the parser. Mandatory are -som and -ksx."""
    parser.add_argument('-som', dest='som', nargs='?', default=None, help='PCX-### format')
    parser.add_argument('-ksx', dest='ksx', nargs='?', default=None, help='KSX-####')


def add_optional_arguments(parser):
    """Adds all optional arguments to the parser. Optional are -kit, -rev, -opt, and -bom."""
    parser.add_argument('-kit', dest='kit', help='Kitoptions from Optiontree')
    parser.add_argument('-rev', dest='rev', nargs='?', default='00', help='Board revision',
                        type=str)
    parser.add_argument('-opt', dest='opt', nargs='?', default=0, type=int,
                        help='Optiontree revision')
    parser.add_argument('-bom', dest='bom', nargs='?', default='00', help='BoM revision', type=str)


def add_file_argument(parser):
    """Adds the file argument to the parser."""
    parser.add_argument('-file', dest='file', nargs='?', default="", type=str,
                        help='Binary file to be read')


def add_always_write_argument(parser):
    """Adds the -y argument to always write to EEPROM chips."""
    parser.add_argument('-y', dest='always_write', action='store_true',
                        help='Do no ask before flashing a new image to the EEPROM chip.')

def main(args):
    """ Set up parsing for commandline arguments. """
    parser = argparse.ArgumentParser(description='PHYTEC SOM EEPROM configuration tool')

    subparsers = parser.add_subparsers(help="EEPROM operation commands", dest='command')
    subparsers.required = True

    parser_read = subparsers.add_parser('read', help="Reads the product configuration from an " \
        "EEPROM device and dumps it to the console.")
    parser_read.set_defaults(func=read_som_config)
    add_mandatory_arguments(parser_read)
    add_file_argument(parser_read)

    parser_write = subparsers.add_parser('write', help="Writes a product configuration to the " \
        "EEPROM device.")
    parser_write.set_defaults(func=write_som_config)
    add_mandatory_arguments(parser_write)
    add_always_write_argument(parser_write)
    add_optional_arguments(parser_write)

    parser_create = subparsers.add_parser('create', help="Creates a binary file at the output " \
        "directory which can then be written to the EEPROM device with dd or via JTAG.")
    parser_create.set_defaults(func=create_binary)
    add_mandatory_arguments(parser_create)
    add_optional_arguments(parser_create)
    add_file_argument(parser_create)

    parser_display = subparsers.add_parser('display', help="Dumps the complete configuration on " \
        "the console without communicating with a EEPROM device")
    parser_display.set_defaults(func=display_som_config)
    add_mandatory_arguments(parser_display)
    add_optional_arguments(parser_display)

    parser_add_mac = subparsers.add_parser('add-mac', help="Adds a MAC address block to an " \
        "existing EEPROM binary or updates the content of an EEPROM device.")
    parser_add_mac.set_defaults(func=write_mac_block)
    parser_add_mac.add_argument('interface', type=int, help='Number of the Ethernet interface')
    parser_add_mac.add_argument('mac', type=str, help='MAC address in XX:XX:XX:XX:XX:XX format')
    add_mandatory_arguments(parser_add_mac)
    add_always_write_argument(parser_add_mac)
    add_file_argument(parser_add_mac)

    parser_add_key_value = subparsers.add_parser('add-key-value', help="Adds a key-value block " \
        "to an existing EEPROM binary or updates the content of an EEPROM device.")
    parser_add_key_value.set_defaults(func=write_key_value_block)
    parser_add_key_value.add_argument('key', type=str, help='Name of the key')
    parser_add_key_value.add_argument('value', type=str, help='Value to the key')
    add_mandatory_arguments(parser_add_key_value)
    add_always_write_argument(parser_add_key_value)
    add_file_argument(parser_add_key_value)

    args = parser.parse_args()

    if not (args.som or args.ksx or ("file" in args and args.file)):
        error = "Set -som and/or -ksx."
        if "file" in args:
            error += " Additionally, set -file."
        parser.error(error)

    yml_parser = get_yml_parser(args)
    if hasattr(args, 'func'):
        if args.func in (read_som_config, write_mac_block, write_key_value_block):
            args.kit = "0"
            args.rev = "0"
            args.bom = "0"
            args.opt = 0
        args.func(args, yml_parser)
