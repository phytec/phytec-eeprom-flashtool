#!/usr/bin/env python2
# Copyright (C) 2017 PHYTEC America, LLC

import argparse
import ConfigParser
import os
import struct
import sys

# Defaults defined by the PHYTEC EEPROM API version
api_version = 0
header = 0x07052017
eeprom_size = 32	# bytes
max_kit_opts = 16
min_bom_rev = 'A0'

cfg_dir = '/configs/'

# Global dicts for storing eeprom data and i2c settings
ep = {
	'header': None,
	'api_version': None,
	'mod_version': None,
	'som_pcb_rev': None,
	'mac': None,
	'ksp': None,
	'kspno': None,
	'kit_opt': None,
	'bs': None,
}

i2c_cfg = {
	'i2c_bus': None,
	'i2c_dev': None,
	'eeprom_offset': None,
	'eeprom_sysfs': None,
}

def i2c_eeprom_init():
	i2c_cfg['i2c_bus'] = cfg_parser.getint('PHYTEC', 'i2c_bus')
	i2c_cfg['i2c_dev'] = cfg_parser.getint('PHYTEC', 'i2c_dev')
	i2c_cfg['eeprom_offset'] = cfg_parser.getint('PHYTEC', 'eeprom_offset')
	i2c_cfg['eeprom_sysfs'] = \
		'/sys/class/i2c-dev/i2c-%d/device/%d-%04d/eeprom' \
		% (i2c_cfg['i2c_bus'], i2c_cfg['i2c_bus'], i2c_cfg['i2c_dev'])

def eeprom_read(i2c_bus, i2c_dev, addr, num_bytes):
	try:
		eeprom_file = open(i2c_cfg['eeprom_sysfs'], 'r')
		eeprom_file.seek(addr)
		read_eeprom = eeprom_file.read(num_bytes)
		eeprom_file.close()
		return read_eeprom
	except IOError as err:
		sys.exit(err)

def eeprom_write(i2c_bus, i2c_dev, addr, string):
	try:
		eeprom_file = open(i2c_cfg['eeprom_sysfs'], 'w')
		eeprom_file.seek(addr)
		eeprom_file.write(string)
		eeprom_file.flush()
		eeprom_file.close()
	except IOError as err:
		sys.exit(err)

def open_som_config():
	try:
		if args.dir != None:
			cfg_path = os.path.abspath(args.dir) + '/'
		else:
			cfg_path = \
				os.path.dirname(os.path.realpath(sys.argv[0])) \
				+ cfg_dir
		config_file = open(cfg_path + args.som + '.ini')
		cfg_parser.readfp(config_file)
		config_file.close()
	except IOError as err:
		sys.exit(err)

def load_som_config(eeprom_dict):
	eeprom_dict['header'] = header
	eeprom_dict['api_version'] = api_version
	eeprom_dict['mod_version'] = cfg_parser.getint('PHYTEC', 'mod_version')
	eeprom_dict['som_pcb_rev'] = args.som_pcb_rev
	eeprom_dict['mac'] = get_mac_addr()
	eeprom_dict['kit_opt'] = args.options
	if eeprom_dict['kit_opt'][:3] == 'KSP':
		eeprom_dict['ksp'] = 1
		eeprom_dict['kspno'] = int(eeprom_dict['kit_opt'].split('KSP')[1])
		eeprom_dict['kit_opt'] = \
			cfg_parser.get('KSP', eeprom_dict['kit_opt'])
	elif eeprom_dict['kit_opt'][:3] == 'KSM':
		eeprom_dict['ksp'] = 2
		eeprom_dict['kspno'] = int(eeprom_dict['kit_opt'].split('KSM')[1])
		eeprom_dict['kit_opt'] = \
			cfg_parser.get('KSP', eeprom_dict['kit_opt'])
	else:
		eeprom_dict['ksp'] = 0
		eeprom_dict['kspno'] = 0
	eeprom_dict['kit_opt'] += args.bom_rev
	eeprom_dict['bs'] = count_eeprom_dict_bits(eeprom_dict)

def check_eeprom_dict(eeprom_dict):
	if eeprom_dict['header'] != header:
		sys.exit('PHYTEC EEPROM header is invalid!')
	if eeprom_dict['api_version'] != api_version:
		sys.exit('PHYTEC EEPROM API Version does not match script version!')
	if eeprom_dict['som_pcb_rev'] < 0 or eeprom_dict['som_pcb_rev'] > 9:
		sys.exit('Read PHYTEC EEPROM PCB Revision is out of bounds!')
	if eeprom_dict['ksp'] < 0 or eeprom_dict['ksp'] > 2:
		sys.exit('Read PHYTEC EEPROM KSP identifier is out of bounds!')
	if not cfg_parser.has_option('Known', eeprom_dict['kit_opt'][:-2]):
		sys.exit('PHYTEC EEPROM kit options not valid within '
			'configuration file!')
	if eeprom_dict['ksp'] != 0:
		ksp_str = 'KSP' if eeprom_dict['ksp'] == 1 else 'KSM'
		ksp_str += '%02d' % (eeprom_dict['kspno'])
		max_bom_rev = cfg_parser.get('Known', ksp_str)
	else:
		max_bom_rev = cfg_parser.get('Known',
			eeprom_dict['kit_opt'][:-2])
	if eeprom_dict['kit_opt'][-2:] < min_bom_rev \
			or eeprom_dict['kit_opt'][-2:] > max_bom_rev:
		sys.exit('Read PHYTEC EEPROM SOM revision is out of bounds!')

def print_eeprom_dict(eeprom_dict):
	print
	print '%s-%s.%s EEPROM contents and configuration [%s]:' % (args.som,
		eeprom_dict['kit_opt'][:-2], eeprom_dict['kit_opt'][-2:],
		args.command)
	print
	print '%-20s\t%-40d' % ('API version', eeprom_dict['api_version'])
	print '%-20s\t%-40d' % ('Mod version', eeprom_dict['mod_version'])
	print '%-20s\t%-40d' % ('SOM PCB revision', eeprom_dict['som_pcb_rev'])
	print '%-20s\t%-40d' % ('KSP style', eeprom_dict['ksp'])
	print '%-20s\t%-40d' % ('KSP number', eeprom_dict['kspno'])
	print '%-20s\t%-40d' % ('Bits set', eeprom_dict['bs'])
	mac_str = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (tuple(map(ord, eeprom_dict['mac'])))
	print '%-20s\t%-40s' % ('MAC address', mac_str)
	print
	print 'Verbose kit options:'
	for i in range(0, len(eeprom_dict['kit_opt'][:-2])):
		kit_opt = cfg_parser.get('Kit', str(i))
		opt_str = cfg_parser.get(kit_opt, eeprom_dict['kit_opt'][i])
		print '%-20s\t%-40s' % (kit_opt, opt_str)
	print

def get_mac_addr():
	eth_name = cfg_parser.get('PHYTEC', 'eth_name')
	eth_sysfs = '/sys/class/net/%s/address' % (eth_name)
	try:
		mac_file = open(eth_sysfs)
		mac_read = mac_file.read()
		mac_file.close()
		mac_read = mac_read.split(':')
		mac_str = ''.join(map(lambda x: chr(int(x, base=16)), mac_read))
	except IOError as err:
		print 'Failed to get MAC address. Using default of ' \
			'00:00:00:00:00:00.'
		return '\x00\x00\x00\x00\x00\x00'
	return mac_str

def count_eeprom_dict_bits(eeprom_dict):
	count = 0
	count += bin(eeprom_dict['header']).count('1')
	count += bin(eeprom_dict['api_version']).count('1')
	count += bin(eeprom_dict['mod_version']).count('1')
	count += bin(eeprom_dict['som_pcb_rev']).count('1')
	count += sum(map(lambda x: bin(ord(x)).count('1'),
		eeprom_dict['mac']))
	count += bin(eeprom_dict['ksp']).count('1')
	count += bin(eeprom_dict['kspno']).count('1')
	for i in eeprom_dict['kit_opt']:
		if i.isalpha():
			count += bin(ord(i)).count('1')
		else:
			count += bin(int(i)).count('1')
	# reserved should always be zero padded so no more bits set
	return count

def dict_to_struct(eeprom_dict):
	print 'dict_to_struct, kit_opt_str:', eeprom_dict['kit_opt']

	eeprom_struct = struct.pack(
		# format: uint, 3 uchars, 6-len str, 2 uchars, 11-len str,
		# 5-len pad, 1 uchar
		'I3B6s2B11s5x1B',
		eeprom_dict['header'],
		eeprom_dict['api_version'],
		eeprom_dict['mod_version'],
		eeprom_dict['som_pcb_rev'],
		eeprom_dict['mac'],
		eeprom_dict['ksp'],
		eeprom_dict['kspno'],
		eeprom_dict['kit_opt'],
		eeprom_dict['bs']
	)
	return eeprom_struct

def struct_to_dict(eeprom_struct, eeprom_dict):
	unpacked = struct.unpack(
		# format: uint, 3 uchars, 6-len str, 2 uchars, 11-len str,
		# 5-len pad, 1 uchar
		'I3B6s2B11s5x1B',
		eeprom_struct
	)

	eeprom_dict['header'] = unpacked[0]
	eeprom_dict['api_version'] = unpacked[1]
	eeprom_dict['mod_version'] = unpacked[2]
	eeprom_dict['som_pcb_rev'] = unpacked[3]
	eeprom_dict['mac'] = unpacked[4]
	eeprom_dict['ksp'] = unpacked[5]
	eeprom_dict['kspno'] = unpacked[6]
	eeprom_dict['kit_opt'] = unpacked[7]
	eeprom_dict['bs'] = unpacked[8]

def read_som_config():
	i2c_eeprom_init()
	read_eeprom = eeprom_read(i2c_cfg['i2c_bus'], i2c_cfg['i2c_dev'],
		i2c_cfg['eeprom_offset'], eeprom_size)
	struct_to_dict(read_eeprom, ep)
	check_eeprom_dict(ep)
	print_eeprom_dict(ep)

def display_som_config():
	load_som_config(ep)
	check_eeprom_dict(ep)
	print_eeprom_dict(ep)

def write_som_config():
	i2c_eeprom_init()
	load_som_config(ep)
	check_eeprom_dict(ep)
	write_eeprom = dict_to_struct(ep)
	eeprom_write(i2c_cfg['i2c_bus'], i2c_cfg['i2c_dev'],
		i2c_cfg['eeprom_offset'], write_eeprom)
	read_eeprom = eeprom_read(i2c_cfg['i2c_bus'], i2c_cfg['i2c_dev'],
		i2c_cfg['eeprom_offset'], eeprom_size)
	if write_eeprom == read_eeprom:
		print 'EEPROM flash successful!'
	else:
		print 'EEPROM flash failed!'

def format_args():
	try:
		bom_split = args.bom.split('-')
		kit_opt_split = bom_split[2].split('.')
		args.som = '%s-%s' % (bom_split[0], bom_split[1])
		args.options = kit_opt_split[0]
		args.bom_rev = kit_opt_split[1]
	except IndexError:
		sys.exit('BOM argument is malformed. Exiting.')

def main():
	arg_parser = argparse.ArgumentParser(
		description='PHYTEC SOM EEPROM configuration tool')
	arg_parser.add_argument('-d', '--dir', help='Configuration directory',
		nargs='?', default=None, required=False)
	arg_subparser = arg_parser.add_subparsers(title='PHYTEC EEPROM commands',
		dest='command')
	read_parser = arg_subparser.add_parser('read', help='Read EEPROM')
	read_parser.add_argument('som', help='PXX-### format.')
	display_parser = arg_subparser.add_parser('display', help='Display ' \
		'verbose board configuration')
	display_parser.add_argument('bom', help='PXX-###-####.X# (or KSX##.X#) format.')
	display_parser.add_argument('som_pcb_rev', help='PCB Revision number.',
		type=int, choices=xrange(0, 10))
	write_parser = arg_subparser.add_parser('write', help='Write EEPROM')
	write_parser.add_argument('bom', help='PXX-###-####.X# (or KSX##.X#) format.')
	write_parser.add_argument('som_pcb_rev', help='PCB Revision number.',
		type=int, choices=xrange(0, 10))

	global cfg_parser
	cfg_parser = ConfigParser.SafeConfigParser()

	global args
	args = arg_parser.parse_args()

	if args.command != 'read':
		format_args()

	open_som_config()

	if args.command == 'read':
		read_som_config()
	if args.command == 'display':
		display_som_config()
	if args.command == 'write':
		write_som_config()

if __name__ == '__main__':
	main()
