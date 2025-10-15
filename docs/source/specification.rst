.. SPDX-FileCopyrightText: 2025 PHYTEC
..
.. SPDX-License-Identifier: MIT

EEPROM Memory Layout Specification
##################################

This document specifies the EEPROM memory layout for Flashtool API versions 2 and 3. It is intended as a reference for interpreting EEPROM data and **not** for the EEPROM Flashtool software implementation itself.

API Version 1 (Deprecated)
**************************

API v1 is deprecated and was only used on the phyCORE-AM57x (PCM-057). Due to significant structural changes, it was superseded by API v2 and is no longer compatible with modern tooling.

API Version 2
*************

API v2 introduces a fixed 32-byte data structure containing key product metadata. All fields are composed of unsigned characters or character arrays.

.. list-table:: API v2 EEPROM Layout
   :widths: 10 25 10 55
   :header-rows: 1

   * - Address
     - Field
     - Length
     - Description
   * - 0
     - API Version
     - 1 byte
     - Always `2` for API v2
   * - 1
     - PCB Revision
     - 1 byte
     - Main PCB revision number
   * - 2
     - PCB Sub-revision and Option Tree Version
     - 1 byte
     - See `PCB Sub-revision and Option Tree Version`_ section
   * - 3
     - Hardware Type
     - 1 byte
     - See `Hardware Types`_ section
   * - 4
     - Part Number / KSP Low
     - 1 byte
     - Lower digits of the article number or KSP number
   * - 5
     - KSP High
     - 1 byte
     - Upper digits of the KSP number, if used
   * - 6
     - Standard Options
     - 17 bytes
     - Hardware option flags and product configuration details
   * - 23
     - BOM Revision
     - 2 bytes
     - For example, "A0" for initial revision
   * - 25
     - MAC Address
     - 6 bytes
     - 1 Ethernet MAC can be stored
   * - 31
     - Checksum
     - 1 byte
     - CRC8 (ITU-T) over bytes 0–30 for integrity checking

PCB Sub-revision and Option Tree Version
========================================

The lower nibble describes the PCB sub-revision Bit [3:0]. If there is no sub
revision the value is 0x00. Sub revision starting with 0x01 represents an "A".

The upper nibble describes the Option Tree version Bit [7:4]. Typically the
value is 0x0. If the option tree layout changes during an active lifecycle of
the product, the value will be increased. This is rarely the case and will be
avoided under all circumstances.

Hardware Types
==============

.. list-table:: Hardware Type Values
   :widths: 15 35 50
   :header-rows: 1

   * - Code
     - Type
     - Description
   * - 0x00
     - PCM
     - phyCORE module
   * - 0x01
     - PCL
     - Solder-on module (Lötmodul)
   * - 0x02
     - KSP
     - Custom carrier board project
   * - 0x03
     - KSM
     - Custom SOM project
   * - 0x04 to 0x07
     - Combined Types
     - Reserved / To be defined (e.g., PCM-KSP, PCM-KSM, etc.)
   * - 0x08
     - PFL-G-PT
     - phyFLEX Module Feature Set Gamma Prototype
   * - 0x09
     - PFL-G-SP
     - phyFLEX Module Feature Set Gamma Standard Product
   * - 0x0A
     - PFL-G-KP
     - phyFLEX Module Feature Set Gamma KSP Customer Design
   * - 0x0B
     - PFL-G-KM
     - phyFLEX Module Feature Set Gamma KSM Customer Variant


Part Number and KSP Encoding
============================

Field 4 and 5 usage depends on the hardware type:

- For `PCM` or `PCL`: Field 4 stores the part number (e.g., 70 for PCM-070). Field 5 is zero.
- For `PCM-KSP`, `PCL-KSP`, etc.: Field 4 holds the base part number, field 5 holds the KSP number.
- For `KSP` or `KSM`: Field 4 stores the lower byte, and field 5 the upper byte of the KSP number.

Standard Product Options
========================

Up to 17 option bytes define specific product configurations (e.g., DDR size,
RTC presence). These values are read by bootloaders like U-Boot to load
appropriate hardware configurations.

Option encoding may be direct (e.g., `0x01` for 1GB DDR) or bit-mapped where
multiple settings share a single byte. Valid Values are [ 0-9 ] and [ A-Z ] as
defined in the option tree. Unused bytes are filled up with 0x00.

BOM Revision
============

Bill of material lists (BOM) have a revisions with a fixed format:

- Byte 17 letter [ A-Z ]
- Byte 18  number [ 0-9 ]

Examples: "A0" or "B3"

MAC
===

An EUI-48 Mac address can be stored as hexadecimal value. If the MAC address is
not written, the field will be filled with 0x0. In many products the MAC will be
used as the serial number.

Checksum
========

Checksum in field 31 is CRC8 (ITU-T) calculated over bytes 0–30. Software should
recalculate it and verify after EEPROM read.

API Version 3
*************

To overcome size limitations in API v2, API v3 introduces an extensible format
with linked block structures.

Goals:

- Maintain compatibility with v2 (first 32 bytes unchanged, except version field = 3)
- Enable flexible extension via blocks with no fixed size limits

.. note::
   The minimum EEPROM image size for API v3 is **40 bytes** (32 bytes from API v2 + 8 bytes header).

Structure:

* **Data**: Entire EEPROM image
* **Data Header**: 8-byte metadata following the v2 block
* **Data Payload**: Contains a list of typed blocks
* **Block Header**: Each block starts with a 4-byte header
* **Block Payload**: Content specific to the block type

Data Header
===========

.. list-table:: API v3 Header
   :widths: 10 25 10 55
   :header-rows: 1

   * - Address
     - Field
     - Length
     - Description
   * - 32
     - Payload Size
     - 2 bytes
     - Total size of all blocks in the Data Payload.
   * - 34
     - Block Count
     - 1 byte
     - Number of blocks in the Data Payload.
   * - 35
     - Sub Version
     - 1 byte
     - Specifies block format version.
   * - 36
     - Reserved
     - 3 bytes
     - Reserved for future use.
   * - 39
     - Header Checksum
     - 1 byte
     - CRC8 (ITU-T) over bytes 32–38.

Data Payload
============

Payload starts at offset `0x40`. Software should:

- Read and validate each Block Header
- Read corresponding Block Payload
- Follow `Next Block Address` pointer to traverse the block chain

Block Header
============

Each block starts with a 4-byte header:

.. list-table:: Block Header Structure
   :widths: 10 25 10 55
   :header-rows: 1

   * - Offset
     - Field
     - Length
     - Description
   * - 0
     - Block Type
     - 1 byte
     - Identifies block type. See `Block Types`_.
   * - 1
     - Next Block Address
     - 2 bytes
     - Offset to next block (relative to start of Payload).
   * - 3
     - Block Checksum
     - 1 byte
     - CRC8 (ITU-T) of this block’s header and payload.

Block Types
***********

.. list-table:: Block Type Identifiers
   :widths: 15 35 50
   :header-rows: 1

   * - ID
     - Name
     - Description
   * - 0x00
     - MAC Address
     - Stores a MAC and associated interface.
   * - 0x01
     - Key Value
     - Generic key-value pair in ASCII format.

MAC Block
*********

Used to assign a MAC address to an Ethernet interface.

.. list-table:: MAC Block Structure (8 Bytes)
   :widths: 10 25 10 55
   :header-rows: 1

   * - Offset
     - Field
     - Length
     - Description
   * - 0
     - Ethernet Interface
     - 1 byte
     - Interface index (U-Boot specific).
   * - 1
     - MAC Address
     - 6 bytes
     - ASCII string, lowercase hex digits, no colons (e.g., `00b0d063c226`).
   * - 7
     - Payload Checksum
     - 1 byte
     - CRC8 (ITU-T) over this block’s content.

Key Value Block
***************

Stores generic key-value metadata in ASCII.

.. list-table:: Key Value Block Structure
   :widths: 10 25 10 55
   :header-rows: 1

   * - Offset
     - Field
     - Length
     - Description
   * - 0
     - Key Length
     - 1 byte
     - Number of bytes in key.
   * - 1
     - Value Length
     - 1 byte
     - Number of bytes in value.
   * - 2
     - Key Entry
     - `x` bytes
     - Key string (no null-termination).
   * - 2 + x
     - Value Entry
     - `y` bytes
     - Value string (no null-termination).
   * - 2 + x + y
     - Payload Checksum
     - 1 byte
     - CRC8 (ITU-T) for block content.
