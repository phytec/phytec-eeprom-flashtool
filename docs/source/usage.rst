.. SPDX-FileCopyrightText: 2025 PHYTEC
.. SPDX-License-Identifier: CC-BY-4.0

Usage
#####

This tool provides five core operations along with extended support for managing block-based metadata inside EEPROM chips.

Version
*******

Print the current version of the tool:

.. code-block:: bash

   phytec_eeprom_flashtool -v
   phytec_eeprom_flashtool --version

Read
****

Reads the product configuration from an EEPROM chip or binary file and prints it to the console.

**Basic usage:**

.. code-block:: bash

   phytec_eeprom_flashtool read -som <SOM>

**For PCM/PCL-KSM/KSP combinations:**

.. code-block:: bash

   phytec_eeprom_flashtool read -som <SOM> -ksx <KSM/KSP>

**For standalone KSM/KSP:**

.. code-block:: bash

   phytec_eeprom_flashtool read -ksx <KSM/KSP>

**Reading from a file (optional `-file` or `-f`):**

.. code-block:: bash

   phytec_eeprom_flashtool read -som <SOM> -f <path/to/file>

**Examples:**

.. code-block:: bash

   phytec_eeprom_flashtool read -som PCL-066
   phytec_eeprom_flashtool read -ksx KSP08
   phytec_eeprom_flashtool read -som PCL-066 -ksx KSP24
   phytec_eeprom_flashtool read -som PCL-075 -f output/PCL-075-7432CE11I.A0_10_0000

Write
*****

Writes a product configuration to the EEPROM chip.

**Basic usage:**

.. code-block:: bash

   phytec_eeprom_flashtool write -som <SOM> -kit <ARTICLE> -pcb <PCB_REV> -bom <BOM_REV> [-opt <OPTIONTREE_REV>]

**KSM/KSP variant:**

.. code-block:: bash

   phytec_eeprom_flashtool write -ksx <KSM/KSP> -kit <ARTICLE> -pcb <PCB_REV> -bom <BOM_REV>

**PCM/PCL-KSM/KSP combination:**

.. code-block:: bash

   phytec_eeprom_flashtool write -som <SOM> -ksx <KSM/KSP> -kit <ARTICLE> -pcb <PCB_REV> -bom <BOM_REV>

**Examples:**

.. code-block:: bash

   phytec_eeprom_flashtool write -som PCL-066 -kit 3022210I -pcb 1a -bom A0
   phytec_eeprom_flashtool write -ksx KSP08 -kit 3322115I -pcb 2 -bom A0
   phytec_eeprom_flashtool write -som PCL-066 -ksx KSP24 -kit 3022210I -pcb 1 -bom A0

Create
******

Generates a binary file with the EEPROM content and prints its configuration. This binary can later be written using `dd` or JTAG.

**Basic usage (same arguments as `write`):**

.. code-block:: bash

   phytec_eeprom_flashtool create -som <SOM> -kit <ARTICLE> -pcb <PCB_REV> -bom <BOM_REV> [-opt <OPTIONTREE_REV>] [-file <filename>]

**Examples:**

.. code-block:: bash

   phytec_eeprom_flashtool create -som PCL-066 -kit 3022210I -pcb 1a -bom A0
   phytec_eeprom_flashtool create -ksx KSP08 -kit 3022210I -pcb 2 -bom A0
   phytec_eeprom_flashtool create -som PCL-066 -ksx KSP24 -kit 3022210I -pcb 1 -bom A0
   phytec_eeprom_flashtool create -som PCL-066 -kit 3022210I -pcb 1 -bom A0 -file eeprom.dat

Display
*******

Prints the product configuration to the console **without accessing the EEPROM**.

Supports all arguments used in the `create` and `write` modes. You can also display the content of a binary file using `-file`.

**Examples:**

.. code-block:: bash

   phytec_eeprom_flashtool display -som PCL-066 -kit 3022210I -pcb 1a -bom A0
   phytec_eeprom_flashtool display -ksx KSP08 -kit 3322115I -pcb 2 -bom A0
   phytec_eeprom_flashtool display -som PCL-066 -ksx KSP24 -kit 3022210I -pcb 1 -bom A0
   phytec_eeprom_flashtool display -som PCL-066 -kit 3022210I -pcb 1 -bom A0 -file eeprom.dat

Blocks
******

Blocks allow extending EEPROM configurations with additional structured information (e.g., MAC addresses, serial numbers).

Each block operation supports `-som`, `-ksx`, or `-file` to identify the target.

.. note::
   Writing a block reads the current EEPROM image, appends the block, and writes the updated content back. Removing a block is not supported.

MAC Block
=========

Adds a MAC address for a specific Ethernet interface.

**Syntax:**

.. code-block:: bash

   phytec_eeprom_flashtool add-mac -som <SOM> <interface_index> <MAC_ADDRESS>

**File-based variant:**

.. code-block:: bash

   phytec_eeprom_flashtool add-mac -som <SOM> <interface_index> <MAC_ADDRESS> -f <binary_file>

**Example:**

.. code-block:: bash

   phytec_eeprom_flashtool add-mac -som PCM-071 0 00:91:da:dc:1f:c5
   phytec_eeprom_flashtool add-mac -som PCM-071 1 00:91:da:dc:1f:c6 -f output/binary_file

Serial Block
============

Adds a serial number to the EEPROM configuration. Internally stored as a key-value pair with `serial` as the key.

.. warning::
   This serial number is not write-protected or tamper-proof and should not be relied on for secure identification.

**Syntax:**

.. code-block:: bash

   phytec_eeprom_flashtool add-serial -som <SOM> <SERIAL>

**File-based variant:**

.. code-block:: bash

   phytec_eeprom_flashtool add-serial -som <SOM> <SERIAL> -f <binary_file>

**Example:**

.. code-block:: bash

   phytec_eeprom_flashtool add-serial -som PCM-071 C0FFEE

Key-Value Block
===============

Adds a generic UTF-8 encoded key-value pair to the EEPROM.

**Syntax:**

.. code-block:: bash

   phytec_eeprom_flashtool add-key-value -som <SOM> <KEY> <VALUE>

**File-based variant:**

.. code-block:: bash

   phytec_eeprom_flashtool add-key-value -som <SOM> <KEY> <VALUE> -f <binary_file>

**Example:**

.. code-block:: bash

   phytec_eeprom_flashtool add-key-value -som PCM-071 SERIAL CAFE1234
