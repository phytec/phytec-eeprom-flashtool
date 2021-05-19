#!/usr/bin/env python3
# Copyright (C) 2017-2021 PHYTEC America, LLC

import argparse
import os
import struct
import sys
import binascii
import yaml

# Defaults defined by the PHYTEC EEPROM API version
API_VERSION = 1
EEPROM_SIZE = 32    # bytes
MAX_KIT_OPTS = 16
MIN_BOM_REV = 'A0'

YML_DIR = '../configs'
OUTPUT_DIR = '../output'

def sysfs_eeprom_init():
    global eeprom_sysfs
    try:
        eeprom_sysfs = \
            '/sys/class/i2c-dev/i2c-%s/device/%s-%s/eeprom' \
            % (yml_parser['PHYTEC']['i2c_bus'],
               str(yml_parser['PHYTEC']['i2c_bus']),
               format(yml_parser['PHYTEC']['i2c_dev'], 'x').zfill(4))
    except IOError as err:
        sys.exit(err)

def eeprom_read(addr, num_bytes):
    try:
        eeprom_file = open(eeprom_sysfs, 'rb')
        eeprom_file.seek(addr)
        read_eeprom = eeprom_file.read(num_bytes)
        eeprom_file.close()
        return read_eeprom
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

def load_som_config():
    try:
        ep['api_version'] = API_VERSION
        ep['som_pcb_rev'] = args.som_pcb_rev
        ep['kit_opt'] = args.options
        if ep['kit_opt'][:3] == 'KSP':
            ep['ksp'] = 1
            ep['kspno'] = int(ep['kit_opt'].split('KSP')[1])
            ep['kit_opt'] = yml_parser['KSP'][ep['kit_opt']]
        elif ep['kit_opt'][:3] == 'KSM':
            ep['ksp'] = 2
            ep['kspno'] = int(ep['kit_opt'].split('KSM')[1])
            ep['kit_opt'] = yml_parser['KSP'][ep['kit_opt']]
        else:
            ep['ksp'] = 0
            ep['kspno'] = 0
        ep['kit_opt'] += args.bom_rev
        if 'mac' in ep:
            ep['mac'] = get_mac_addr()
        ep['hw8'] = count_eeprom_dict_bits()
    except IOError as err:
        sys.exit(err)

def print_eeprom_dict():
    try:
        print()
        print('%s-%s.%s EEPROM contents and configuration [%s]:' % (args.som, ep['kit_opt'][:-2],
                                                                    ep['kit_opt'][-2:],
                                                                    args.command))
        print()
        print('%-20s\t%-40d' % ('API version', ep['api_version']))
        print('%-20s\t%-40d' % ('SOM PCB revision', ep['som_pcb_rev']))
        print('%-20s\t%-40d' % ('KSP style', ep['ksp']))
        print('%-20s\t%-40d' % ('KSP number', ep['kspno']))
        print('%-20s\t%-40d' % ('Bits set', ep['hw8']))
        if 'mac' in ep:
            mac_str = binascii.hexlify(ep['mac'])
            mac_str = str(mac_str).split('b', 1)
            mac_str = mac_str[1]
            mac_str = ':'.join(mac_str[i:i+2] for i in range(1, len(mac_str)-2, 2))
            print('%-20s\t%-40s' % ('MAC address', mac_str))
        print()
        print('Verbose kit options:')
        for i in range(0, len(ep['kit_opt'][:-2])):
            kit_opt = yml_parser['Kit'][i]
            opt_str = yml_parser[kit_opt][ep['kit_opt'][i]]
            print('%-20s\t%-40s' % (kit_opt, opt_str))
        print()
    except IOError as err:
        sys.exit(err)

def get_mac_addr():
    eth_name = yml_parser['PHYTEC']['eth_name']
    try:
        eth_sysfs = '/sys/class/net/%s/address' % (eth_name)
        mac_file = open(eth_sysfs, 'r')
        mac_read = mac_file.read()
        mac_file.close()
        mac_read = mac_read.replace(':', '').strip()
        mac_str = binascii.unhexlify(mac_read)
    except IOError as _:
        print('Failed to get MAC address. Using default of 00:00:00:00:00:00.')
        return b'\x00\x00\x00\x00\x00\x00'
    return mac_str

def count_eeprom_dict_bits():
    count = 0
    count += bin(ep['api_version']).count('1')
    count += bin(ep['som_pcb_rev']).count('1')
    count += bin(ep['ksp']).count('1')
    count += bin(ep['kspno']).count('1')
    count += sum([bin(ord(x)).count('1') for x in ep['kit_opt']])
    if 'mac' in ep:
        count += sum([bin(x).count('1') for x in ep['mac']])
    # reserved should always be zero padded so no more bits set
    return count

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
        if 'mac' in ep:
            eeprom_struct += struct.pack('6s', ep['mac'])
        else:
            eeprom_struct += struct.pack('6x')
        eeprom_struct += struct.pack('B', ep['hw8'])
    except IOError as err:
        sys.exit(err)

    return eeprom_struct

def struct_to_dict(eeprom_struct):
    try:
        unpacked = struct.unpack(yml_parser['PHYTEC']['ep_encoding'], eeprom_struct)

        ep['api_version'] = unpacked[0]
        ep['som_pcb_rev'] = unpacked[1]
        ep['ksp'] = unpacked[2]
        ep['kspno'] = unpacked[3]
        ep['kit_opt'] = unpacked[4].decode('utf-8')
        if 'mac' in ep:
            ep['mac'] = unpacked[5]
            ep['hw8'] = unpacked[6]
        else:
            ep['hw8'] = unpacked[5]
    except IOError as err:
        sys.exit(err)

def read_som_config():
    sysfs_eeprom_init()
    read_eeprom = eeprom_read(yml_parser['PHYTEC']['eeprom_offset'], EEPROM_SIZE)
    struct_to_dict(read_eeprom)
    print_eeprom_dict()

def display_som_config():
    load_som_config()
    print_eeprom_dict()

def write_som_config():
    sysfs_eeprom_init()
    load_som_config()
    write_eeprom = dict_to_struct()
    eeprom_write(yml_parser['PHYTEC']['eeprom_offset'], write_eeprom)
    read_eeprom = eeprom_read(yml_parser['PHYTEC']['eeprom_offset'], len(write_eeprom))
    if write_eeprom == read_eeprom:
        print('EEPROM flash successful!')
    else:
        print('EEPROM flash failed!')

def create_binary():
    load_som_config()
    print_eeprom_dict()
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

operation = {
    "display": display_som_config,
    "create": create_binary,
    "read": read_som_config,
    "write": write_som_config
}

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
