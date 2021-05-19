#!/usr/bin/env python3
# Copyright (C) 2017-2021 PHYTEC America, LLC

import argparse
import os
import struct
import sys
import binascii
import yaml
from smbus2 import SMBus, i2c_msg
import crc8

# Defaults defined by the PHYTEC EEPROM API version
API_VERSION = 1
EEPROM_SIZE = 32    # bytes
MAX_KIT_OPTS = 16
MIN_BOM_REV = 'A0'

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

def eeprom_read(yml_parser):
    """ Get i2c bus and i2c dev out of the config files.
        Read out the eeprom-id page.
    """
    try:
        eeprom_bus = SMBus(yml_parser['PHYTEC']['i2c_bus'], force=True)
        i2c_dev = yml_parser['PHYTEC']['i2c_dev']
        eeprom_offset = yml_parser['PHYTEC']['eeprom_offset']
        eeprom_data = i2c_msg.read(i2c_dev, EEPROM_SIZE)
        eeprom_bus.i2c_rdwr(eeprom_data)
        eeprom_exit(eeprom_bus)
        return bytes(eeprom_data)
    except IOError as err:
        sys.exit(err)

def eeprom_write(addr, string):
    try:
        eeprom_file = open(eeprom_sysfs, 'wb')
        eeprom_file.seek(addr)
        eeprom_file.write(string)
        eeprom_file.flush()
        eeprom_file.close()
    except IOError as err:
        sys.exit(err)

def write_binary(string):
    try:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_DIR)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        output_file = os.path.join(output_path, '%s-%s.%s'\
                    % (args.som, args.options, ep['kit_opt'][-2:]))
        eeprom_file = open(output_file, 'wb')
        eeprom_file.write(string)
        eeprom_file.close()
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
            yml_file = os.path.join(yml_path, "{}-{}.yml".format(args.som, args.ksx))

        config_file = open(yml_file, 'r')
        yml_parser = yaml.safe_load(config_file)
        config_file.close()
        operation[args.operation](args, yml_parser)
    except IOError as err:
        sys.exit(err)

def load_som_config(args):
    """ Load the argparser information to the ep dict with the correct type. """
    ofset = ord('a') - 1
    ep['api_version'] = API_VERSION
    ep['som_revision'] = int(args.rev[0])
    if args.rev[1] != '0':
        ep['som_sub_revision'] = str(format((ord(args.rev[1]) - ofset),'04b'))
    else:
        ep['som_sub_revision'] = format(0, '04b')
    ep['opttree_revision'] = format(int(args.opt), '04b')
    ep['sub_revision'] = ep['opttree_revision'] + ep['som_sub_revision']
    ep['sub_revision'] = int(ep['sub_revision'], 2)
    ep['som_type'] = get_som_type(args)
    if ep['som_type'] <= 1:
        ep['base_article_number'] = int(args.som[4:])
        ep['ksp_number'] = 0
    elif ep['som_type'] <= 3:
        if int(args.ksx[4:]) <= 255:
            ep['base_article_number'] = int(args.ksx[4:])
            ep['ksp_number'] = 0
        else:
            ksp_bytes = '{0:{fill}16b}'.format(int(args.ksx[4:]), fill='0')
            ksp_lower_byte = int(ksp_bytes[8:], 2)
            ksp_higher_byte = int(ksp_bytes[:8], 2)
            ep['base_article_number'] = int(ksp_lower_byte)
            ep['ksp_number'] = int(ksp_higher_byte)
    else:
        ep['base_article_number'] = int(args.som[4:])
        if int(args.ksx[4:]) <= 255:
            ep['ksp_number'] = int(args.ksx[4:])
        else:
            sys.exit('KSX-number out of bounce.')
    ep['bom_rev'] = bytes(args.bom_rev, 'utf-8')
    ep['kit_opt'] = bytes(args.options, 'utf-8')
    if len(ep['kit_opt']) <= 17:
        ep['kit_opt_full'] = ep['kit_opt']
        for i in range(len(ep['kit_opt']), 17):
            ep['kit_opt_full'] += bytes('\0', 'utf-8')

def print_eeprom_dict(args, yml_parser):
    """ Print out the data which the user enters. """
    print()
    if ep['som_type'] <=1:
        print('%s-%s.%s EEPROM contents.' % (args.som, (ep['kit_opt'].decode('utf-8')),
                                            (ep['bom_rev'].decode('utf-8'))))
    elif ep['som_type'] <= 3:
        print('%s-%s.%s EEPROM contents.' % (args.ksx, (ep['kit_opt'].decode('utf-8')),
                                            (ep['bom_rev'].decode('utf-8'))))
    else:
        print('%s-%s-%s.%s EEPROM contents.' % (args.som, args.ksx,
                         (ep['kit_opt'].decode('utf-8')), (ep['bom_rev'].decode('utf-8'))))
    print()
    print('%-20s:\t%-40d' % ('API version', ep['api_version']))
    if args.operation == 'read':
        print('%-20s:\t%-5d%-s' % ('SOM PCB revision', int(ep['som_revision']),
                                  ep['som_sub_revision']))
    else:
        print('%-20s:\t%-5d%-s' % ('SOM PCB revision', int(ep['som_revision']),
                                  str(args.rev[1])))
    print('%-20s:\t%-40s' % ('Optiontree revision', args.opt))
    if ep['som_type'] <= 1:
        print('%-20s:\t%-40s' % ('SoM type', args.som[:3]))
    elif ep['som_type'] <= 3:
        print('%-20s:\t%-40s' % ('SoM type', args.ksx[:3]))
    else:
        print('%-20s:\t%-s-%s' % ('SoM type', args.som[:3], args.ksx[:3]))
    print('%-20s\n%-20s:\t0x%-40s' % ('Base article number', 'KSX number low',
                                     format(ep['base_article_number'], 'x')))
    print('%-20s:\t0x%-40s' % ('KSX number high', format(ep['ksp_number'], 'x')))
    print()
    print('Verbose kit options:')
    for i in range(0, yml_parser['PHYTEC']['kit_options']):
        kit_opt = yml_parser['Kit'][i]
        print('%-20s:\t%-40s' % (kit_opt, yml_parser[kit_opt][chr(ep['kit_opt'][i])]))
    print()

def crc8_checksum_calc(eeprom_struct):
    """ Create a crc8 checksum from the packed eeprom-data. """
    hash = crc8.crc8()
    hash.update(eeprom_struct)
    crc8_sum = hash.hexdigest()
    return int(crc8_sum, 16)

def dict_to_struct():
    try:
        length = len(yml_parser['PHYTEC']['ep_encoding'])
        eeprom_struct = struct.pack(
            yml_parser['PHYTEC']['ep_encoding'][:length-3],
            ep['api_version'],
            ep['som_pcb_rev'],
            ep['ksp'],
            ep['kspno'],
            bytes(ep['kit_opt'], 'utf-8'),
        )
        eeprom_struct += struct.pack('6x')
        ep['crc8'] = crc8_checksum_calc(eeprom_struct)
        eeprom_struct += struct.pack('B', ep['crc8'])
        print('%-20s:\t%-40s' % ('CRC8-Checksum', format(ep['crc8'], 'x')))
    except IOError as err:
        sys.exit(err)

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

        ep['kit_opt'] = ep['kit_opt_full'][:yml_parser['PHYTEC']['kit_options']]
        ep['sub_revision'] = format(ep['sub_revision'], '08b')
        ep['som_sub_revision'] = ep['sub_revision'][4:]
        ep['opttree_revision'] = int(ep['sub_revision'][:4])
        ofset = ord('a') - 1
        if int(ep['som_sub_revision']) != 0:
            ep['som_sub_revision'] = chr(int(ep['som_sub_revision']) + ofset)
        else:
            ep['som_sub_revision'] = 0
    except IOError as err:
        sys.exit(err)

def read_som_config(args, yml_parser):
    eeprom_data = eeprom_read(yml_parser)
    struct_to_dict(eeprom_data, yml_parser)
    print_eeprom_dict(args, yml_parser)
    print('CRC8-Checksum correct if 0:', crc8_checksum_calc(eeprom_data))

def display_som_config(args, yml_parser):
    format_args(args)
    load_som_config(args)
    print_eeprom_dict(args, yml_parser)

def write_som_config():
    load_som_config(args)
    write_eeprom = dict_to_struct()
    eeprom_write(yml_parser['PHYTEC']['eeprom_offset'], write_eeprom)
    print('EEPROM flash successful!')

def create_binary():
    load_som_config(args)
    print_eeprom_dict(args, yml_parser)
    data_to_write = dict_to_struct()
    write_binary(data_to_write)

def format_args(args):
    """ Bring the argparser parameters to a usable format. """
    try:
        if args.som:
            som_split = args.som.split('-')
        if len(args.rev) != 2:
            args.rev = args.rev + '0'
        if args.ksx:
            ksx_split = args.ksx.split('-')
        kit_opt_split = args.kit.split('.')
        args.options = kit_opt_split[0]
        args.bom_rev = kit_opt_split[1]
    except IOError as err:
        sys.exit('BOM argument is malformed. Exiting.')

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
    parser.add_argument('-opt', dest='opt', nargs='?', default=0, type=int, help='Optiontree revision')
    args = parser.parse_args()

    if not (args.som or args.ksx):
        parser.error('Either -som or -ksx or both need to be set.')

    open_som_config(args)

if __name__ == '__main__':
    main()
