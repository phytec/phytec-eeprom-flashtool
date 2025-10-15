Hardware Introspection at PHYTEC
********************************

To be able to handle our high number of SoM variants, extension boards, development Kits and customer projects (KSP/KSM), we need to have a consolidated way of getting introspection data from our systems during runtime. For ARM SoCs we do not have a standardized way of providing this information to the OS and the different users, like we have with UEFI and SMBIOS on x86. We decided on using eeproms on each SoM and hardware componente where introspection should be available. Every client board (base board, expansion, display etc.) could be equipped with an eeprom to have some introspection data available.

This EEPROM tool is the reference implementation for generating EEPROM binary blobs using our ERP system database.

The basic function is to write all relevant hardware version information to a known location. All the information is rarely used, but available. If there is a software dependency to a pcb revision, the information is available. Additionally the option tree is written. The option tree maps which components are assembled in this specific device variant. If we have to deal with product discontinuations for certain parts, we can deal with the information and make the software compatible to all variants without further infrastructure.

For our customers the major benefit is, that we can provide a single software version which can run on all variants in the field. So it is not required to implement a software variant handling for parts bought from PHYTEC. It is not intended as a user API tool.

Working with the introspection data
===================================

The idea for the customer is not to interfere with the introspection data. Some products write the data to the ID-Page of the EEPROM, so the user area is free for customer data. Some products carry two EEPROMs, one for the PHYTEC introspection, one to be used for the customer. If there is only one EEPROM, the introspection data has a product specific size limit. Everything behind the data structure is available for user data.

To work with the data in the field, one has to refere to the specific manual of the product. The EEPROM Tool can be install on any linux device and read out. Alternatively one can dump the eeprom binary and decoded on a PC using the EEPROM Tool.
