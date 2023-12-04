#!/usr/bin/env python3
# Copyright (C) 2017-2023 PHYTEC America, LLC
""" PHYTEC-EEPROM-FLASHTOOL

    The tool is supposed to create, write, read and display the hardware introspection
    for our boards. The information is stored at a eeprom-id page and is necessary for
    our bootloader to boot up with the correct configuration. It is also a way to verify
    which board is used.

"""

import argparse
import sys

from src.io import get_yml_parser
from src.io import eeprom_write
from src.io import eeprom_read
from src.io import binary_write
from src.io import binary_read
from src.encoding import get_eeprom_data
from src.encoding import eeprom_data_to_struct
from src.encoding import struct_to_eeprom_data
from src.encoding import print_eeprom_data
from src.encoding import YmlParser

EEPROM_SIZE = 32    # bytes


def read_som_config(args, yml_parser: YmlParser):
    """Reads from either a binary or an EEPROM device and prints the content."""
    eeprom_data = get_eeprom_data(args, yml_parser)
    if "file" in args and args.file:
        eeprom_struct = binary_read(args, eeprom_data, EEPROM_SIZE)
    else:
        eeprom_struct = eeprom_read(yml_parser, EEPROM_SIZE)
    eeprom_data = struct_to_eeprom_data(eeprom_struct, yml_parser)
    print_eeprom_data(eeprom_data)


def write_som_config(args, yml_parser: YmlParser):
    """Writes the EEPROM data into an EEPROM device."""
    eeprom_data = get_eeprom_data(args, yml_parser)
    eeprom_struct = eeprom_data_to_struct(eeprom_data)
    eeprom_write(yml_parser, eeprom_struct)
    print_eeprom_data(eeprom_data)
    print('EEPROM flash successful!')


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


def main(args):
    """ Set up parsing for commandline arguments. """
    parser = argparse.ArgumentParser(description='PHYTEC SOM EEPROM configuration tool')

    subparsers = parser.add_subparsers(help="EEPROM operation commands", dest='command')
    subparsers.required = True

    parser_read = subparsers.add_parser('read', help="Reads the product configuration from an " \
        "EEPROM device and dumps it to the console.")
    parser_read.set_defaults(func=read_som_config)
    parser_read.add_argument('-som', dest='som', nargs='?', default=None, help='PCX-### format')
    parser_read.add_argument('-ksx', dest='ksx', nargs='?', default=None, help='KSX-####')
    parser_read.add_argument('-file', dest='file', nargs='?', default="", type=str,
                             help='Binary file to be read')

    parser_write = subparsers.add_parser('write', help="Writes a product configuration to the " \
        "EEPROM device.")
    parser_write.set_defaults(func=write_som_config)
    parser_write.add_argument('-som', dest='som', nargs='?', default=None, help='PCX-### format')
    parser_write.add_argument('-ksx', dest='ksx', nargs='?', default=None, help='KSX-####')
    parser_write.add_argument('-kit', dest='kit', help='Kitoptions from Optiontree')
    parser_write.add_argument('-rev', dest='rev', nargs='?', default='00', help='Board revision',
                              type=str)
    parser_write.add_argument('-opt', dest='opt', nargs='?', default=0, type=int,
                              help='Optiontree revision')
    parser_write.add_argument('-bom', dest='bom', nargs='?', default='00', help='BoM revision',
                              type=str)

    parser_create = subparsers.add_parser('create', help="Creates a binary file at the output " \
        "directory which can then be written to the EEPROM device with dd or via JTAG.")
    parser_create.set_defaults(func=create_binary)
    parser_create.add_argument('-som', dest='som', nargs='?', default=None, help='PCX-### format')
    parser_create.add_argument('-ksx', dest='ksx', nargs='?', default=None, help='KSX-####')
    parser_create.add_argument('-kit', dest='kit', help='Kitoptions from Optiontree')
    parser_create.add_argument('-rev', dest='rev', nargs='?', default='00', help='Board revision',
                               type=str)
    parser_create.add_argument('-opt', dest='opt', nargs='?', default=0, type=int,
                               help='Optiontree revision')
    parser_create.add_argument('-bom', dest='bom', nargs='?', default='00', help='BoM revision',
                               type=str)
    parser_create.add_argument('-file', dest='file', nargs='?', default="", type=str,
                               help='Binary file to be read')

    parser_display = subparsers.add_parser('display', help="Dumps the complete configuration on " \
        "the console without communicating with a EEPROM device")
    parser_display.set_defaults(func=display_som_config)
    parser_display.add_argument('-som', dest='som', nargs='?', default=None, help='PCX-### format')
    parser_display.add_argument('-ksx', dest='ksx', nargs='?', default=None, help='KSX-####')
    parser_display.add_argument('-kit', dest='kit', help='Kitoptions from Optiontree')
    parser_display.add_argument('-rev', dest='rev', nargs='?', default='00', help='Board revision',
                                type=str)
    parser_display.add_argument('-opt', dest='opt', nargs='?', default=0, type=int,
                                help='Optiontree revision')
    parser_display.add_argument('-bom', dest='bom', nargs='?', default='00', help='BoM revision',
                                type=str)

    args = parser.parse_args()

    if not (args.som or args.ksx):
        error = "Set -som and/or -ksx."
        if "file" in args and not args.file:
            error += "Additionally, set -file."
        parser.error(error)

    yml_parser = get_yml_parser(args)
    if hasattr(args, 'func'):
        if args.func is read_som_config:
            args.kit = "0"
            args.rev = "0"
            args.bom = "0"
            args.opt = 0
        args.func(args, yml_parser)

if __name__ == '__main__':
    main(sys.argv[1:])
