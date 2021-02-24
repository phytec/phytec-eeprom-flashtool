PHYTEC EEPROM Flashtool
=======================

This tool is intended for reading from and writing to PHYTEC SOM EEPROM chips.

Use of this tool requires a properly-formatted configuration file for each
target PHYTEC platform (PCM-057.yml for PCM-057 boards, for example).
By default, this tool looks for configuration files in a 'configs' subdirectory
to where the script is currently located.

Usage
#####

This tool has three different modes and an optional argument to parse the config directory.

Read
****

Reads the product configuration from an EEPROM chips and dumps it to the console. It takes the
product name as parameter.

.. code-block:: bash

    phytec_eeprom_flashtool.py read <som>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool.py read PCL-066

Write
*****

Writes a product configuration to the EEPROM chip. This commands takes the article number and the
PCB revision number as parameter.

.. code-block:: bash

    phytec_eeprom_flashtool.py write <bom> <pcb_rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool.py write PCL-066-3022210I.A0 2

Create
******

Creates a binary file which can then be written to the EEPROM chip with dd or via JTAG.
It also dumps the complete configuration on the console.

.. code-block:: bash

    phytec_eeprom_flashtool.py create <bom> <pcb_rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool.py create PCL-066-3022210I.A0 2

Display
*******

Dumps the complete configuration on the console without communicating with a EEPROM chip. It takes
the article number and the PCB revision number as paraemter.

.. code-block:: bash

    phytec_eeprom_flashtool.py display <bom> <pcb_rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool.py display PCL-066-3022210I.A0 2

License
#######

Copyright (C) 2017 PHYTEC America, LLC. Released under the `license`_.

.. _license: COPYING.MIT
