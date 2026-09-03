# SPDX-FileCopyrightText: 2025 PHYTEC
#
# SPDX-License-Identifier: MIT

"""Main Wrapper"""
import sys
from .src.phytec_eeprom_flashtool import main

def cmd_main():
    """Main function"""
    try:
        main(sys.argv[1:])
    except (ValueError, AssertionError) as err:
        sys.exit(f"Error: {err}")

if __name__  == "__main__":
    cmd_main()
