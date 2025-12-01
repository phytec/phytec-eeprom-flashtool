.. SPDX-FileCopyrightText: 2025 PHYTEC
..
.. SPDX-License-Identifier: MIT

EEPROM Memory Layout Specification
##################################

This document specifies the EEPROM memory layout. It is intended as a reference for interpreting EEPROM data and **not** for the EEPROM Flashtool software implementation itself.

API Version 0
*************

API v0 has been the first implementation of introspection data and is not used on any product any more. EEPROM Tool support is available in the branch "release/pcm-057_am57x_api_v0"

It introduces a fixed 32-byte data structure containing key product metadata. All fields are composed of unsigned characters or character arrays, byte ordered.

.. list-table:: API v0 EEPROM Layout
   :widths: 10 25 10 55
   :header-rows: 1

   * - Address
     - Field
     - Length
     - Description
   * - 0
     - header
     - 4
     - PHYTEC EEPROM header identifier
   * - 4
     - api_version
     - 1
     - EEPROM layout API version, always `0`
   * - 5
     - mod_version
     - 1
     - Module Type (PCM/PFL/PCA)
   * - 6
     - som_pcb_rev
     - 1
     - SoM PCB revision
   * - 7
     - mac
     - 6
     - MAC address (6 bytes)
   * - 13
     - ksp
     - 1
     - custom module type: 1 = KSP, 2 = KSM
   * - 14
     - kspno
     - 1
     - Number/identifier for KSP/KSM module
   * - 15
     - kit_opt
     - 11
     - Option tree for variants
   * - 26
     - reserved
     - 5
     - Reserved bytes (not used)
   * - 31
     - bs
     - 1
     - Checksum/bits set in previous bytes

Header
======

As a header identifier, we write the integer date `0x07052017`. This is done
in litte endian byte ording. This is the only exception to other byte ordered
data.

MAC address
===========

The MAC address is always optional. If none is written, we write zeros. If a
product or a customer requires a MAC, we need to define this on a customer or
product basis. It is stored byte ordered.

bs - Checksum
=============
For AM57x The checksum has never be implemented in API v0 and can be ignored.

For RK3288 the check is implemented in that way in u-boot:

.. code-block:: c

   int hw = 0;
   while (p < e) {
       hw += hweight8(*p);
       p++;
   }

API Version 1
*************

API v1 is actively used only on the phyCORE-AM57x (PCM-057). EEPROM Tool support is available in the branch "release/pcm-057_am57x_api_v1"

.. list-table:: API v1 EEPROM Layout
   :widths: 10 15 10 55
   :header-rows: 1

   * - Address
     - Field
     - Byte Size
     - Description
   * - 0
     - api_version
     - 1
     - EEPROM layout API version, always `1`
   * - 1
     - som_pcb_rev
     - 1
     - SoM PCB revision
   * - 2
     - ksp
     - 1
     - custom module type: 1 = KSP, 2 = KSM
   * - 3
     - kspno
     - 1
     - Number/identifier for KSP/KSM module
   * - 4
     - kit_opt
     - 11
     - Option tree for variants
   * - 15
     - reserved
     - 10
     - Reserved bytes (not used)
   * - 25
     - mac
     - 6
     - MAC address (6 bytes)
   * - 31
     - hw8
     - 1
     - Checksum/bits set in previous bytes

MAC address
===========

The MAC address is always optional. If none is written, we write zeros. If a
product or a customer requires a MAC, we need to define this on a customer or
product basis.

hw8 - Checksum
==============

The ``hw8`` field is a data integrity check field that contains the total count of
bits set to '1' across all preceding data fields in the structure. It is usually
called Hamming weight. Here is an example implementation for one byte:

.. code-block:: c

    u8 count = 0;
    while (val) {
        count += val & 1;
        val >>= 1;
    }
    return count;

API Version 2
*************

API v2 is a consolidation of previous versions. The main characteristics are still a fixed 32-byte data structure. All fields are unsigned characters or character arrays.

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

API v3 is backwards compatible with API v2. The block specification for the
first 32 bytes is unchanged. Just the revision is incremented. Additionally we
introduced an extension format. A linked list with a block structure without
fixed size is used to add customizable data fields to the EEPROM.

.. note::
   The minimum EEPROM image size for API v3 is **40 bytes** (32 bytes from API
   v2 + 8 bytes header). Products reserving only the ID-Page in the EEPROM
   cannot be used with API v3.

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
-----------

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
---------

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
---------------

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
