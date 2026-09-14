.. SPDX-FileCopyrightText: 2025 PHYTEC
.. SPDX-License-Identifier: CC-BY-4.0

Product Overview Table
======================

This table maps our products to the used EEPROMs for hardware introspection, the I2C addresses and the API revision used.

For our SoMs, we have a set of common base boards and extension boards. To be able to use these products interchangeable, we need to set a global address space.

Secondly, as we will fixate the API revision as soon as a product is release for mass market, we need to log the revision.

.. note::
   A `-` denotes that a field is not applicable. Products carrying more than
   one EEPROM list the bus, address and user of each device separated by `/`.

.. csv-table:: Products and API Revision
   :header-rows: 1
   :widths: 35 16 8 17 17 7
   :file: product_overview.csv
