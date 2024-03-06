PHYTEC EEPROM Flashtool
=======================

This tool is intended for reading from and writing to PHYTEC SOM EEPROM chips.

Use of this tool requires a properly-formatted configuration file for each
target PHYTEC platform (PCM-057.yml for PCM-057 boards, for example).
By default, this tool looks for configuration files in a 'configs' subdirectory
to where the script is currently located.

Installation (Linux)
####################

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

Installation (Windows)
######################

This guide is written for PowerShell.

- First, set the Execution policy::

        PS C:> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

- Clone the repository locally::

        git clone git@github.com:phytec/phytec-eeprom-flashtool.git
        cd phytec-eeprom-flashtool

- Create a virtualenv::

        python -m venv venv
        \venv\Scripts\Activate.ps1

- Install this package and all dependencies::

        pip install .
        pip install -r requirements-windows.txt

Installation Without Virtualenv
###############################

You can run the phytec-eeprom-flashtool without a virtual environment. However, it's highly
recommended to use a virtual environment to not overwrite dependencies of other projects.

- Clone the repository locally::

        git clone git@github.com:phytec/phytec-eeprom-flashtool.git
        cd phytec-eeprom-flashtool

- Install all dependencies::

        pip install -r requirements.txt

- You can run the tool with the following command (you have to be in the root directory)::

        python -m phytec_eeprom_flashtool

Usage
#####

This tool has five different modes and required/optional arguments.

Version
*******

Prints the current version of this tool.

.. code-block:: bash

    phytec_eeprom_flashtool -v
    phytec_eeprom_flashtool --version

Read
****

Reads the product configuration from an EEPROM chips and dumps it to the console.
Alternatively it can read a binary file by passing the filename via -file argument.
It takes the argument -som followed by the product name as parameter.
Required arguments: -som <som>

.. code-block:: bash

    phytec_eeprom_flashtool read -som <som>

If the product configuration is made by a KSM/KSP or a PCM/PCL-KSM/KSP then the
optional argument -ksx is used.

For a pure KSM/KSX -ksx replaces the parameter -som.
Required arguments: read -ksx <KSM/KSP>

.. code-block:: bash

    phytec_eeprom_flashtool read -ksx <KSP/KSX>

If the product configuration is a PCM/PCL-KSM/KSP then -som is used to enter
the PCM/PCL number and the argument -ksx is additionally specified.
Required arguments: read -som <som> -ksx <KSM/KSP>


.. code-block:: bash

    phytec_eeprom_flashtool read -som <som> -ksx <KSP/KSX>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool read -som PCL-066
    phytec_eeprom_flashtool read -ksx KSP08
    phytec_eeprom_flashtool read -som PCL-066 -ksx KSP-24
    phytec_eeprom_flashtool read -som PCL-066 -file binary_file.bin

Write
*****

Writes a product configuration to the EEPROM chip.
This commands takes the the argument -som followed by the argument -kit for the article number.
The -rev for the PCB revision, the -opt for the optiontree revision and the -bom
for the bom revision are optional and default 0.

.. code-block:: bash

    phytec_eeprom_flashtool write -som <som> -kit <bom> -bom <bom rev>

KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool write -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

PCM/PCL-KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool write -som <som> -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool write -som PCL-066 -kit 3022210I -bom A0
    phytec_eeprom_flashtool write -ksx KSP08 -kit 3322115I -bom A0
    phytec_eeprom_flashtool write -som PCL-066 -ksx KSP24 -kit 3022210I -bom A0

Create
******

Creates a binary file at the output directory which can then be written to the
EEPROM chip with dd or via JTAG.
It also dumps the complete configuration on the console.
The default filename and directory can be changed by the -file argument.
The other necessary and optional arguments are the same as for the write command.

.. code-block:: bash

    phytec_eeprom_flashtool create -som <som> -kit <bom> -bom <bom rev>

KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool create -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

PCM/PCL-KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool create -som <som> -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool create -som PCL-066 -kit 3022210I -bom A0
    phytec_eeprom_flashtool create -ksx KSP08 -kit 3022210I -bom A0
    phytec_eeprom_flashtool create -som PCL-066 -ksx KSP24 -kit 3022210I -bom A0
    phytec_eeprom_flashtool create -som PCL-066 -kit 3022210I -bom A0 -file eeprom.dat

Display
*******

Dumps the complete configuration on the console without communicating with a
EEPROM chip. It takes same arguments as for create or write.

.. code-block:: bash

    phytec_eeprom_flashtool display -som <som> -kit <bom> -bom <bom rev>

KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool display -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

PCM/PCL-KSM/KSP:

.. code-block:: bash

    phytec_eeprom_flashtool display -som <som> -ksx <KSM/KSP> -kit <bom> -bom <bom rev>

Example:

.. code-block:: bash

    phytec_eeprom_flashtool display -som PCL-066 -kit 3022210I -bom A0
    phytec_eeprom_flashtool display -ksx KSP08 -kit 3322115I -bom A0
    phytec_eeprom_flashtool display -som PCL-066 -ksx KSP24 -kit 3022210I -bom A0

Blocks
######

Blocks are a flexible way to extend the general information inside the EEPROM chip by information
required for a product. For example, it allows to store multiple MACs for Ethernet interfaces.

Please keep in mind each transaction will read the content first, append the MAC and writes the
new image back to the EEPROM chip. It's not possible to remove a block.

Each command requires either the `-som` and/or `-ksx` argument to identify the EEPROM chip. The
`-f` arguments works as well for read/write operations on a local file.

MAC Block
*********

Adds a MAC block with information about the physical Ethernet interface and MAC address.

Requires the Ethernet interface number and MAC address as parameters. The following example adds
two MACs to the interface 0 and 1.

.. code-block:: bash

    phytec_eeprom_flashtool add-mac -som PCM-071 0 00:91:da:dc:1f:c5
    phytec_eeprom_flashtool add-mac -som PCM-071 1 00:91:da:dc:1f:c6

Key Value Block
---------------

Adds a key-value pair to the EEPROM chip. Both the key and value are stored as UTF-8 string.

This block can be used to write persistent data into the EEPROM chip during production or assembly
and can be used in software later.

.. code-block:: bash

    phytec_eeprom_flashtool add-key-value -som PCM-071 SERIAL CAFE1234

License
#######

Copyright (C) 2024 PHYTEC Holding AG. Released under the `license`_.

.. _license: COPYING.MIT
