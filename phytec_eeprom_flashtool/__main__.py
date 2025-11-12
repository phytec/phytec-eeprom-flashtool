# SPDX-FileCopyrightText: 2025 PHYTEC
#
# SPDX-License-Identifier: MIT

"""Main Wrapper"""
import sys
from .src.phytec_eeprom_flashtool import main

def cmd_main():
    """Main function"""
    main(sys.argv[1:])

if __name__  == "__main__":
    cmd_main()
