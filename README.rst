PHYTEC EEPROM Flashtool
=======================

This tool is intended for reading from and writing to PHYTEC SOM EEPROM chips.

Use of this tool requires a properly-formatted configuration file for each
target PHYTEC platform (PCM-057.yml for PCM-057 boards, for example).
By default, this tool looks for configuration files in a 'configs' subdirectory
to where the script is currently located.

Installation
############

- The packets virtualenv must be installed on your distribution::

        apt install virtualenv

- Clone the repository locally::

        git clone git@github.com:phytec/phytec-eeprom-flashtool.git
        cd phytec-eeprom-flashtool

- Create a virtualenv::

        virtualenv -p python3 venv
        . venv/bin/activate

- Install this package and all dependencies::

        pip install .
        pip install -r requirements.txt

You can leave the virtualenv by running ``deactivate`` in the bash. Do not
forget to source the virtualenv again next time you want to use it.

Usage
#####

This tool has four different modes and required/optional arguments.

Read
****

Reads the product configuration from an EEPROM chips and dumps it to the console.
Alternatively it can read a binary file by passing the filename via -file argument.
It takes the argument -som followed by the product name as parameter.
Required arguments: -som <som>

.. code-block:: bash

    phytec_eeprom_flashtool.py read -som <som>

If the product configuration is made by a KSM/KSP or a PCM/PCL-KSM/KSP then the
optional argument -ksx is used.

For a pure KSM/KSX -ksx replaces the parameter -som.
Required arguments: read -ksx <KSM/KSP>

.. code-block:: bash

    phytec_eeprom_flashtool.py read -ksx <KSP/KSX>

If the product configuration is a PCM/PCL-KSM/KSP then -som is used to enter
the PCM/PCL number and the argument -ksx is additionally specified.
Required arguments: read -som <som> -ksx <KSM/KSP>


.. code-block:: bash

    phytec_eeprom_flashtool.py read -som <som> -ksx <KSP/KSX>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool.py read -som PCL-066
    phytec_eeprom_flashtool.py read -ksx KSP08
    phytec_eeprom_flashtool.py read -som PCL-066 -ksx KSP-24
    phytec_eeprom_flashtool.py read -som PCL-066 -file binary_file.bin

Write
*****

Writes a product configuration to the EEPROM chip.
This commands takes the the argument -som followed by the argument -kit for the article number.
The -rev for the PCB revision, the -opt for the optiontree revision and the -bom
for the bom revision are optional and default 0.

.. code-block:: bash

    phytec_eeprom_flashtool.py write -som <som> -kit <bom> -bom <bom rev>

KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool.py write -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

PCM/PCL-KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool.py write -som <som> -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool.py write -som PCL-066 -kit 3022210I -bom A0
    phytec_eeprom_flashtool.py write -ksx KSP08 -kit 3322115I -bom A0
    phytec_eeprom_flashtool.py write -som PCL-066 -ksx KSP24 -kit 3022210I -bom A0

Create
******

Creates a binary file at the output directory which can then be written to the
EEPROM chip with dd or via JTAG.
It also dumps the complete configuration on the console.
The default filename and directory can be changed by the -file argument.
The other necessary and optional arguments are the same as for the write command.

.. code-block:: bash

    phytec_eeprom_flashtool.py create -som <som> -kit <bom> -bom <bom rev>

KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool.py create -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

PCM/PCL-KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool.py create -som <som> -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool.py create -som PCL-066 -kit 3022210I -bom A0
    phytec_eeprom_flashtool.py create -ksx KSP08 -kit 3022210I -bom A0
    phytec_eeprom_flashtool.py create -som PCL-066 -ksx KSP24 -kit 3022210I -bom A0
    phytec_eeprom_flashtool.py create -som PCL-066 -kit 3022210I -bom A0 -file eeprom.dat

Display
*******

Dumps the complete configuration on the console without communicating with a
EEPROM chip. It takes same arguments as for create or write.

.. code-block:: bash

    phytec_eeprom_flashtool.py display -som <som> -kit <bom> -bom <bom rev>

KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool.py display -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

PCM/PCL-KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool.py display -som <som> -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool.py display -som PCL-066 -kit 3022210I -bom A0
    phytec_eeprom_flashtool.py display -ksx KSP08 -kit 3322115I -bom A0
    phytec_eeprom_flashtool.py display -som PCL-066 -ksx KSP24 -kit 3022210I -bom A0

License
#######

Copyright (C) 2017 PHYTEC America, LLC. Released under the `license`_.

.. _license: COPYING.MIT
