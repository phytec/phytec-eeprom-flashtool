.. SPDX-FileCopyrightText: 2025 PHYTEC
.. SPDX-License-Identifier: CC-BY-4.0

Hardware Introspection at PHYTEC
################################

To be able to handle our high number of SoM variants, extension boards,
development Kits and customer projects (KSP/KSM), we need to have a consolidated
way of getting introspection data from our systems during runtime. For ARM SoCs
we do not have a standardized way of providing this information to the OS and
the different users, like we have with UEFI and SMBIOS on x86. We decided on
using eeproms on each SoM and hardware componente where introspection should be
available. Every client board (base board, expansion, display etc.) could be
equipped with an eeprom to have some introspection data available.

This EEPROM tool is the reference implementation for coding and decoding the
product information to an EEPROM binary blobs.

The basic idea is to write all relevant hardware version information to a known
location. Every piece of information is rarely used in the software, but
available. For example, if there is a software dependency to a pcb revision in
the future, the information will be available and we take actions. Additionally
the option tree is written. The option tree maps which components are assembled
in this specific device variant. If we have to deal with product
discontinuations for certain parts, we can deal with the information and make
the software compatible to all variants without further infrastructure.

For our customers the major benefit is, that we can provide a single software
version which can run on all variants in the field. So it is not required to
implement a software variant handling for parts bought from PHYTEC. It is not
intended as a user API tool.

Bootloader implementation
*************************

The bootloader implementation defines some of the main requirements. RAM
detection is done in the secodary program loader (SPL), the first step
after the ROM-loader. This runs out of the SRAM and can handle only minimal c
code. So the whole system is not allowed to be complex. Typical solutions are
gpio solder jumper, one-wire or i2c eeproms, which we choose.

As a product matures to series production status, bootloaders will be deployed
in the field and even might not be updatedable. At the least, updating the
boootloader is consider risky, mostly not power cut safe, so it is important to
fixate the API revision for a product, as soon it is in production.

If we have a MAC address written in the EEPROM, it needs to be used by the
bootloader and the kernel as the device MAC address. If we do not have a MAC
written, the bootloader should take the MAC provided from another product
specific source. This could either be the SoC fuses, the Ethernet PHY's attached
EEPROM or something else.

Bootloader security consideration
*********************************

For critical systems with physical access security all external data needs to be
encrypted. This cannot be done in the SPL. In that case we need to remap all
functionality implemented in the SPL to another methed, for example use the SoC
internal fuses for RAM detection.

For this reason every bootloader is required to have an config option to
explicitly select the compiled in DDR timings. With this compile time switch,
one can provide signed or encrypted boot binaries without a dependency to
external data structures.

Hardware implementation
***********************

Because every SoM has its specific design goals and set of requirements, the
EEPROM implementation differs depending on the product. Some products write the
data to the ID-Page of the EEPROM, so the user area is free for customer data.
Some products carry two EEPROMs, one for the PHYTEC introspection, one to be
used for the customer. Some products have a write protect pin, controlled by the
SoC or defined by the base board layout. If there is only one EEPROM, the
introspection data has a product specific size limit. Everything after the data
structure is available for user data.

Further details can be found in the corresponding hardware manual of the
product.

Handling in product manufacturing
*********************************

The EEPROM tool is used for coding the product information to the binary format
for flashing. The tool is running on a server and provides the blob to be added
to the product bill of materials. The BOM is fixed for each product. The customer
will be informed about changes. With this process, it is fully reproducible.

During manufacturing the blob will be read from the BOM-Database and flashed
using JTAG before the first boot. As usually RAM detection is implemented, we do
not need a special production bootloader with this process.

There are also rules regading the MAC address. Some products requring a MAC as a
serial number, some products use the SoC Vendors MAC address, some require the
customer to write custom MAC address ranges. If we need to program a serial
number or a MAC address, this will be done in the last step and usually from
within a booted system, either bootloader or linux. If we do not write a MAC, we
write zeros.

Working with the introspection data
***********************************

The idea for the customer is not to interfere with the introspection data. For
every product there is a defined way to store product meta data without
interfering with the PHYTEC data structure. As explained in the hardware
section, have a look at the specific hardware manual to see the specific
solution for your SoM.

To work with the data in the field, one has to refere to the specific hardware
and software manual of the product. The EEPROM Tool can be install on any linux
device. It can read out and decode the information. It can code and write the
EEPROM information if the EEPROM is set to write enable.

Alternatively one can dump the EEPROM binary and decode it on a PC using the
EEPROM Tool.
