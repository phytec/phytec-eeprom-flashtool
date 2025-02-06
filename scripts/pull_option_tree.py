#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The programs pulls a product option tree from the business logic server and stores it as an
EEPROM tool yaml file.
"""

import argparse
from datetime import datetime
import logging
from pathlib import Path
import sys

import requests
import yaml


# global definitions
URL = "https://phytecphptool.phytec.de/api/v2/optiontree/"

#################################
# Operations on the Option Tree #
#################################


def load_option_tree(product_name):
    """Load the most recent optrion tree from our webservice."""
    # Get JSON from REST API
    resp = requests.get(URL + product_name + "/decode", timeout=30)

    # Parse JSON to get option tree dict
    resp_dict = resp.json()

    # check for 404 return
    if resp.status_code == 404:
        logging.error(resp_dict["message"])
        print(f"Error: {resp_dict['message']}")
        sys.exit(1)

    if isinstance(resp_dict, dict) and resp_dict.get('status', 0) == 422:
        logging.error(resp_dict["message"])
        print(f"Error: {resp_dict['message']}")
        sys.exit(1)

    return resp_dict


def parse_option_tree(product_name, has_extended_options):
    """Parses the option tree from our webservice and prepare the structure."""
    response = load_option_tree(product_name)

    data = {}
    opt_index = 0
    bit_index = 0
    for entry in response:
        header = entry['header']
        option_name = header['FullName']
        if not has_extended_options and header.get('Extended', False):
            logging.info("Found extended option: {option_name}. Skipping.")
            continue
        if opt_index not in data:
            data[opt_index] = {'options': {}}
        if 'name' in data[opt_index] and not 'Reserved' == header['Name']:
            data[opt_index]['name'] = f"{option_name} / {data[opt_index]['name']}"
        elif not ('Reserved' == header['Name'] and header['Type'] == 'Binary'):
            data[opt_index]['name'] = option_name

        data[opt_index]['options'][option_name] = {}
        option_entry = data[opt_index]['options'][option_name]
        for option in entry['options']:
            option_entry[option['Position']] = option['FullName']

        # Only increase option index when
        #   Type == Alphanumeric
        # or
        #   Type == Binary and fourth option
        if header['Type'] == 'Binary' and bit_index < 3:
            bit_index += 1
        else:
            bit_index = 0
            opt_index += 1
    return data


def get_option_tree(product_name, has_extended_options = False):
    """Build the finial option tree structure with the pre-parsed structured."""
    data = parse_option_tree(product_name, has_extended_options)

    opttree = {'Kit': {}}
    for index, opt in data.items():
        opttree['Kit'][index] = opt['name']
        if len(opt['options']) > 1:
            opttree[opt['name']] = group_binary(opt['options'])
        else:
            opttree[opt['name']] = opt['options'][opt['name']]

    return opttree


def group_binary(options, index=0, result=None, old_key=0, old_value=""):
    """Group binary option to one entry"""
    if result is None:
        result = {}
    name = list(options.keys())[index]
    for k, v in list(options.values())[index].items():
        key = old_key + pow(2, index) * int(k)
        if not str(name).startswith("Reserved"):
            value = f"{v} / {old_value}" if old_value else v
        else:
            value = old_value
        if index == len(options) - 1:
            result[f"{key:X}"] = value
            continue
        group_binary(options, index + 1, result, key, value)
    if index == 0:
        return dict(sorted(result.items()))
    return result


def product_has_extend_options(product_name):
    """Tries to read a poduct config to figure out whether this product uses extended options.
    Will return False when no config exists or the config is unreadable."""
    yaml_file = Path(__file__).resolve().parent.parent / "phytec_eeprom_flashtool/configs" / \
                f"{product_name}.yml"
    if not yaml_file.is_file():
        return False
    with open(yaml_file, 'r', encoding="utf-8") as file:
        try:
            config = yaml.safe_load(file)
            if not 'PHYTEC' in config:
                return False
            return config['PHYTEC'].get('extended_options', 0) > 0
        except yaml.YAMLError as exc:
            logging.error(str(exc))
            print(f"Error: {exc}")
            sys.exit(1)
    return False


def print_option_tree(product_name):
    """Fetch the option tree for a product and print it afterwards."""
    has_extended_options = product_has_extend_options(product_name)
    data = get_option_tree(product_name, has_extended_options)
    print(yaml.dump(data, sort_keys=False))


def write_option_tree(product_name):
    """Update an existing YML config file or create a new one."""
    has_extended_options = product_has_extend_options(product_name)
    data = get_option_tree(product_name, has_extended_options)

    yaml_file = Path(__file__).resolve().parent.parent / "phytec_eeprom_flashtool/configs" / \
                f"{product_name}.yml"

    logging.info(yaml_file)
    if not yaml_file.is_file():
        with open(yaml_file, 'w', encoding="utf-8") as file:
            file.write("---\n")
            file.write("# PHYTEC EEPROM Flashtool Config File\n")
            file.write(f"# product: {product_name}\n")
            file.write(f"# Copyright (C) {datetime.today().strftime('%Y')} PHYTEC\n")
            file.write("\n")
            file.write("PHYTEC:\n")
            file.write("  eeprom_offset: 0x0\n")
            file.write("  i2c_bus: 0x0\n")
            file.write("  i2c_dev: 0x0\n")
            file.write("  api: 3\n")
            file.write("  extended_options: 0\n")
            file.write("  max_image_size: 4096\n")

    # Keep the comment block and 'PHYTEC' key. Remove the 'Kit' section and all
    # following options. They will be re-added with content from the option tree.
    with open(yaml_file, 'r+', encoding="utf-8") as file:
        config = file.readlines()
        file.seek(0)
        for line in config:
            if line.startswith("Kit:"):
                break
            file.write(line)
        file.truncate()

    with open(yaml_file, 'a', encoding="utf-8") as file:
        # write the option tree to the yaml file
        yaml.dump(data, file, sort_keys=False)


def main(): # pylint: disable=missing-function-docstring
    # check if we run python >= 3.6
    if sys.version_info < (3, 6):
        print("Error: This script requires Python 3.6 or higher, as it relies on " \
              "deterministic ordering of dict elements.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Config Sync Tool')
    subparsers = parser.add_subparsers(help="Sync Operations", dest='command')
    parser.add_argument('product_name', help='The product string like PCL-077')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='enable debug output')
    subparsers.required = True

    parser_print = subparsers.add_parser('print', help="Print the option tree")
    parser_print.set_defaults(func=print_option_tree)

    parser_write = subparsers.add_parser('write', help="Write the option tree to the YML file")
    parser_write.set_defaults(func=write_option_tree)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    if hasattr(args, 'func'):
        args.func(args.product_name)


if __name__ == "__main__":
    main()
