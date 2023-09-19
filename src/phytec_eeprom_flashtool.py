#!/usr/bin/env python3
# Copyright (C) 2017-2021 PHYTEC America, LLC
""" PHYTEC-EEPROM-FLASHTOOL

    The tool is supposed to create, write, read and display the hardware introspection
    for our boards. The information is stored at a eeprom-id page and is necessary for
    our bootloader to boot up with the correct configuration. It is also a way to verify
    which board is used.

"""

import argparse
import os
import struct
import sys
import binascii
import yaml
import crc8
import re

# Defaults defined by the PHYTEC EEPROM API version
API_VERSION = 2
EEPROM_SIZE = 32    # bytes
MAX_KIT_OPTS = 17

YML_DIR = '../configs'
OUTPUT_DIR = '../output'

# Buffer for eerprom data
ep = {
    "api_version": None,
    "som_revision": None,
    "sub_revision": None,
    "som_sub_revision": None,
    "opttree_revision": None,
    "som_type": None,
    "base_article_number": None,
    "ksp_number": None,
    "kit_opt": None,
    "kit_opt_full": None,
    "bom_rev": None,
    "crc8": None,
}

som = {
    "PCM": 0x0,
    "PCL": 0x1,
    "KSP": 0x2,
    "KSM": 0x3,
    "PCM-KSP": 0x4,
    "PCM-KSM": 0x5,
    "PCL-KSP": 0x6,
    "PCL-KSM": 0x7
}


def get_som_type_name_by_value(som_value):
    """Returns the som type name for the passed number value"""
    return list(som.keys())[list(som.values()).index(som_value)]


def decode_base_name(ep_data):
    """Decodes the product base name from ep_data"""
    if ep_data['som_type'] <= 1:
        return "{0}-{1:03}".format(get_som_type_name_by_value(ep_data['som_type']), ep_data['base_article_number'])
    elif ep_data['som_type'] <= 3:
        return "{0}-{1:04}".format(get_som_type_name_by_value(ep_data['som_type']),
                                   (ep_data['ksp_number'] << 16 + ep_data['base_article_number']))
    else:
        return "{0}-{1:03}".format(get_som_type_name_by_value(ep_data['som_type']).split('-')[0],
                                   ep_data['base_article_number'])


def decode_full_name(ep_data):
    """Decodes the product full name from ep_data"""
    base_name = decode_base_name(ep_data)
    if ep_data['som_type'] <= 1:
        full_name = "{0}-{1}".format(base_name, ep_data['kit_opt'].decode('utf-8'))
    elif ep_data['som_type'] <= 3:
        full_name = base_name
    else:
        som_type = get_som_type_name_by_value(ep_data['som_type']).split('-')
        full_name = "{0}-{1}{2:02}".format(base_name, som_type[1], ep_data['ksp_number'])

    full_name = "{0}.{1}".format(full_name, ep_data['bom_rev'].decode('utf-8'))
    return full_name

def eeprom_read(args, yml_parser):
    """ Read eeprom data from the i2c eeprom or if '-file' parameter was passed from a binary file
    """
    try:
        offset = 0
        eeprom_bin_location = args.file
        if eeprom_bin_location == "":
            eeprom_bin_location = \
                    '/sys/class/i2c-dev/i2c-%s/device/%s-%s/eeprom' \
                    % (yml_parser['PHYTEC']['i2c_bus'], str(yml_parser['PHYTEC']['i2c_bus']),
                    format(yml_parser['PHYTEC']['i2c_dev'], 'x').zfill(4))
            offset = yml_parser['PHYTEC']['eeprom_offset']

        eeprom_file = open(eeprom_bin_location, 'rb')
        eeprom_file.seek(offset)
        eeprom_data = eeprom_file.read(EEPROM_SIZE)
        eeprom_file.close()
        return bytes(eeprom_data)
    except IOError as err:
        sys.exit(err)

def eeprom_write(string, yml_parser):
    """ Write data to eeprom-id page.

    Args:
        string: 32-Byte string
    """
    try:
        eeprom_bus = \
            '/sys/class/i2c-dev/i2c-%s/device/%s-%s/eeprom' \
            % (yml_parser['PHYTEC']['i2c_bus'], str(yml_parser['PHYTEC']['i2c_bus']),
            format(yml_parser['PHYTEC']['i2c_dev'], 'x').zfill(4))
        eeprom_file = open(eeprom_bus, 'wb')
        eeprom_file.seek(yml_parser['PHYTEC']['eeprom_offset'])
        eeprom_file.write(string)
        eeprom_file.flush()
        eeprom_file.close()
    except IOError as err:
        sys.exit(err)

def write_binary(string, args, yml_parser):
    """ Creates a 32-Byte file which can be written to the eeprom-id page with dd.

    Args:
        string: 32-Byte string
    """
    try:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_DIR)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        if ep['som_type'] <= 1:
            output_file = os.path.join(output_path, '%s-%s.%s_%s%s_%d'\
                    % (args.som, args.kit, (ep['bom_rev']).decode('utf-8'),
                      ep['som_revision'], sub_revision_to_str(ep['som_sub_revision']), int(ep['opttree_revision'])))
        elif ep['som_type'] <= 3:
            output_file = os.path.join(output_path, '%s-%s.%s_%s%s_%d'\
                    % (args.ksx, args.kit, (ep['bom_rev']).decode('utf-8'),
                      ep['som_revision'], sub_revision_to_str(ep['som_sub_revision']), int(ep['opttree_revision'])))
        else:
            output_file = os.path.join(output_path, '%s-%s-%s.%s_%s%s_%d'\
                     % (args.som, args.ksx, args.kit, (ep['bom_rev']).decode('utf-8'),
                       ep['som_revision'], sub_revision_to_str(ep['som_sub_revision']), int(ep['opttree_revision'])))

        eeprom_file = open(output_file, 'wb')
        eeprom_file.seek(yml_parser['PHYTEC']['eeprom_offset'])
        eeprom_file.write(string)
    except IOError as err:
        sys.exit(err)

def open_som_config(args):
    """ Opens *.yml configuration files at the config dir. """
    try:
        yml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), YML_DIR)
        if args.som and not args.ksx:
            yml_file = os.path.join(yml_path, "{}.yml".format(args.som))
        elif not args.som and args.ksx:
            yml_file = os.path.join(yml_path, "{}.yml".format(args.ksx))
        else:
            yml_file = os.path.join(yml_path, "{}.yml".format(args.som))

        config_file = open(yml_file, 'r')
        yml_parser = yaml.safe_load(config_file)
        config_file.close()
        operation[args.operation](args, yml_parser)
    except IOError as err:
        sys.exit(err)

def load_som_config(args):
    """ Load the argparser information to the ep dict with the correct type. """
    ep['api_version'] = API_VERSION
    ep['som_revision'], ep['som_sub_revision'] = str_to_revision(args.rev)
    ep['opttree_revision'] = format(int(args.opt), '04b')
    ep['sub_revision'] = ep['opttree_revision'] + ep['som_sub_revision']
    ep['sub_revision'] = int(ep['sub_revision'], 2)
    ep['som_type'] = get_som_type(args)
    if ep['som_type'] <= 1:
        ep['base_article_number'] = int(args.som[4:])
        ep['ksp_number'] = 0
    elif ep['som_type'] <= 3:
        if int(args.ksx[4:]) <= 255:
            ep['base_article_number'] = int(args.ksx[3:])
            ep['ksp_number'] = 0
        else:
            ksp_bytes = '{0:{fill}16b}'.format(int(args.ksx[3:]), fill='0')
            ksp_lower_byte = int(ksp_bytes[8:], 2)
            ksp_higher_byte = int(ksp_bytes[:8], 2)
            ep['base_article_number'] = int(ksp_lower_byte)
            ep['ksp_number'] = int(ksp_higher_byte)
    else:
        ep['base_article_number'] = int(args.som[4:])
        if int(args.ksx[3:]) <= 255:
            ep['ksp_number'] = int(args.ksx[3:])
        else:
            sys.exit('KSX-number out of bounce.')
    ep['bom_rev'] = bytes(args.bom, 'utf-8')
    ep['kit_opt'] = bytes(args.kit, 'utf-8')
    if len(ep['kit_opt']) <= MAX_KIT_OPTS:
        ep['kit_opt_full'] = ep['kit_opt']
        for i in range(len(ep['kit_opt']), MAX_KIT_OPTS):
            ep['kit_opt_full'] += bytes('\0', 'utf-8')

def print_eeprom_dict(yml_parser):
    """ Print out the eeprom data. """
    print('EEPROM contents:')
    print()
    print("Decoded information:")
    print('%-20s:\t%-40s' % ('Full name', decode_full_name(ep)))
    pcb_revision = str(ep['som_revision'])
    if int(ep['som_sub_revision']) > 0:
        pcb_revision = pcb_revision + sub_revision_to_str(ep['som_sub_revision'])
    print('%-20s:\t%-40s' % ('PCB revision', pcb_revision))
    print()
    print("Raw information:")
    print('%-20s:\t%-40d' % ('API version', ep['api_version']))
    print('%-20s:\t%-5d%-s' % ('SOM PCB revision', int(ep['som_revision']),
                              ep['som_sub_revision']))
    print('%-20s:\t%-40s' % ('Optiontree revision', ep['opttree_revision']))
    print('%-20s:\t%-40s' % ('SoM type', get_som_type_name_by_value(ep['som_type'])))
    print('%-20s\n%-20s:\t0x%-40s' % ('Base article number', 'KSX number low',
                                     format(ep['base_article_number'], 'x')))
    print('%-20s:\t0x%-40s' % ('KSX number high', format(ep['ksp_number'], 'x')))
    print('%-20s:\t%-40s' % ('Options', ep['kit_opt'].decode('utf-8')))
    print()
    print('Verbose kit options:')
    for i in range(0, len(yml_parser['Kit'])):
        kit_opt = yml_parser['Kit'][i]
        print('%-20s:\t%-40s' % (kit_opt, yml_parser[kit_opt][chr(ep['kit_opt'][i])]))
    print()

def crc8_checksum_calc(eeprom_struct):
    """ Create a crc8 checksum from the packed eeprom-data. """
    hash = crc8.crc8()
    hash.update(eeprom_struct)
    crc8_sum = hash.hexdigest()
    return int(crc8_sum, 16)

def dict_to_struct(yml_parser):
    """ Pack the ep dict to a 32-Byte string. """
    length = len(yml_parser['PHYTEC']['ep_encoding'])
    eeprom_struct = struct.pack(
        yml_parser['PHYTEC']['ep_encoding'][:length-3],
        ep['api_version'],
        ep['som_revision'],
        ep['sub_revision'],
        ep['som_type'],
        ep['base_article_number'],
        ep['ksp_number'],
        ep['kit_opt_full'],
        ep['bom_rev']
    )
    eeprom_struct += struct.pack(yml_parser['PHYTEC']['ep_encoding'][7:9])
    ep['crc8'] = crc8_checksum_calc(eeprom_struct)
    eeprom_struct += struct.pack('B', ep['crc8'])
    print('%-20s:\t%-40s' % ('CRC8-Checksum', format(ep['crc8'], 'x')))

    return eeprom_struct

def struct_to_dict(eeprom_struct, yml_parser):
    """ Unpack the 32-byte string which is read out of the eeprom-id page. """
    try:
        unpacked = struct.unpack(yml_parser['PHYTEC']['ep_encoding'], eeprom_struct)

        ep['api_version'] = unpacked[0]
        ep['som_revision'] = unpacked[1]
        ep['sub_revision'] = unpacked[2]
        ep['som_type'] = unpacked[3]
        ep['base_article_number'] = unpacked[4]
        ep['ksp_number'] = unpacked[5]
        ep['kit_opt_full'] = unpacked[6]
        ep['bom_rev'] = unpacked[7]
        ep['crc8'] = unpacked[8]

        ep['kit_opt'] = ep['kit_opt_full'][:len(yml_parser['Kit'])]
        ep['sub_revision'] = format(ep['sub_revision'], '08b')
        ep['som_sub_revision'] = ep['sub_revision'][4:]
        ep['opttree_revision'] = int(ep['sub_revision'][:4], 2)
        ep['som_sub_revision'] = sub_revision_to_str(ep['som_sub_revision'])
    except IOError as err:
        sys.exit(err)

def sub_revision_to_str(sub_revision):
    if int(sub_revision) != 0:
        ofset = ord('a') - 1
        if isinstance(sub_revision, str):
            sub_revision = chr(int(sub_revision, 2) + ofset)
    else:
        sub_revision = "0"
    return sub_revision

def str_to_revision(revision_str):
    ofset = ord('a') - 1
    rev_digits = len(revision_str)
    rev_digits_re = re.search(r'[^0-9]',revision_str)
    if rev_digits_re != None:
        rev_digits = rev_digits_re.start()
    revision = int(revision_str[0:rev_digits])
    sub_revision = 0
    if len(revision_str) > rev_digits:
        sub_revision = ord(revision_str[rev_digits]) - ofset
    sub_revision = format(sub_revision, '04b')
    if int(sub_revision, 2) > 15:
        raise IOError("PCB subversion has to be a character between 'a' and 'o'!")
    return revision, sub_revision

def read_som_config(args, yml_parser):
    eeprom_data = eeprom_read(args, yml_parser)
    struct_to_dict(eeprom_data, yml_parser)
    print_eeprom_dict(yml_parser)
    print('CRC8-Checksum correct if 0:', crc8_checksum_calc(eeprom_data))

def display_som_config(args, yml_parser):
    format_args(args)
    load_som_config(args)
    eeprom_data = dict_to_struct(yml_parser)
    struct_to_dict(eeprom_data, yml_parser)
    print_eeprom_dict(yml_parser)

def write_som_config(args, yml_parser):
    format_args(args)
    load_som_config(args)
    eeprom_data = dict_to_struct(yml_parser)
    eeprom_write(eeprom_data, yml_parser)
    struct_to_dict(eeprom_data, yml_parser)
    print_eeprom_dict(yml_parser)
    print('EEPROM flash successful!')

def create_binary(args, yml_parser):
    format_args(args)
    load_som_config(args)
    eeprom_data = dict_to_struct(yml_parser)
    write_binary(eeprom_data, args, yml_parser)
    struct_to_dict(eeprom_data, yml_parser)
    print_eeprom_dict(yml_parser)

def format_args(args):
    """ Bring the argparser parameters to a usable format. """
    try:
        if args.som:
            som_split = args.som.split('-')
    except IOError as err:
        sys.exit('BOM argument is malformed. Exiting.')
    try:
        if args.rev:
            str_to_revision(args.rev)
    except IOError as err:
        sys.exit(err)

def get_som_type(args):
    """ Choose the write SoM type to write it into the ep dict.

    Returns:
        hex value which will be written to the ep dict
    """
    if args.ksx and args.som:
        som_type = '%s-%s' % (args.som[:3], args.ksx[:3])
    elif args.ksx and not args.som:
        som_type = args.ksx[:3]
    else:
        som_type = args.som[:3]

    return som.get(som_type)

operation = {
    "display": display_som_config,
    "create": create_binary,
    "read": read_som_config,
    "write": write_som_config
}

def eeprom_exit(eeprom_bus):
    """ Close i2c bus after read/write function. """
    try:
        eeprom_bus.close()
    except IOError as err:
        sys.exit(err)

def main():
    """ Set up parsing for commandline arguments. """
    parser = argparse.ArgumentParser(description='PHYTEC SOM EEPROM configuration tool')
    parser.add_argument('-o', '--operation', dest='operation', default='display',
                       help='Tool operation', required=True, choices=['create', 'display',
                       'read', 'write'])
    parser.add_argument('-som', dest='som', nargs='?', default=None, help='PCX-### format')
    parser.add_argument('-kit', dest='kit', help='Kitoptions from Optiontree')
    parser.add_argument('-ksx', dest='ksx', nargs='?', default=None, help='KSX-####')
    parser.add_argument('-rev', dest='rev', nargs='?', default='00', help='Board revision', type=str)
    parser.add_argument('-bom', dest='bom', nargs='?', default='00', help='BoM revision', type=str)
    parser.add_argument('-opt', dest='opt', nargs='?', default=0, type=int, help='Optiontree revision')
    parser.add_argument('-file', dest='file', nargs='?', default="", type=str, help='Binary file to be read')
    args = parser.parse_args()

    if not (args.som or args.ksx):
        parser.error('Either -som or -ksx or both need to be set.')

    open_som_config(args)

if __name__ == '__main__':
    main()
