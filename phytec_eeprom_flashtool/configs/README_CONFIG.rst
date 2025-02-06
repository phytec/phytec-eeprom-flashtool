A configuration file contains:
--------------------------------

# PHYTEC EEPROM Flashtool Config File           //General header
# product: PCM-069 / phyCORE-i.MX8 MM           //Product information
# Copyright (C) 2025 PHYTEC                     //Copyright

""" The PHYTEC-node configurates the environment for the phytec-eeprom-flashtool """
PHYTEC:
  eeprom_offset: 0x0                            //At the moment, the eeprom offset is 0 for all boards
  i2c_bus: 0                                    //i2c bus number where the eeprom is connected to
  i2c_dev: 0x51                                 //i2c address (This is the normal eeprom page. This should be our new default.
  api: 3                                        //Sets API to v3. Not required for v2.

""" Kit contains all option-headlines from the option tree in the correct order """
Kit:
  0: Controller Mini                            //the first digit from the kit options
  1: Controller Nano                            //the second digit etc.
  2: LPDDR
  [...]

""" This displays the different options for the first kit_option digit """
Controller Mini:
  '0': Nano
  '1': Quad (VPU, GPU)  IMX8MM6
  '2': Quad Lite (No VPU, GPU) IMX8MM5
  [...]

""" This displays the different options for the second kit_option digit """
Controller Nano:
  '0': Mini
  '1': Quad (GPU) IMX8MN6
  '2': Quad Lite (No GPU) IMX8MN5
  [...]

""" This displays the different options for the third kit_option digit """
LPDDR:
  '0': 512MB DDR4 RAM 1 Bank
  '1': 1GB DDR4 RAM 1 Bank
  '2': 1.5GB DDR4 RAM 1 Bank

""" This displays the different options for the fourth kit_option digit """
eMMC:
  '0': No eMMC
  '1': 4GB eMMC
  '2': 8GB eMMC
  [...]

""" This displays the different options for the fifth kit_option digit """
Quad SPI Nor:
  '0': no SPI-Nor
  '1': 4MB
  [...]

""" This displays the different options for the sixth kit_option digit """
Ethernet:
  '0': RGMII
  '1': 10/100/1000 ethernet PHY

""" This displays the different options for the seventh kit_option digit """
Display:
  '0': MIPI DSI
  '1': LVDS

""" This displays the different options for the eighth kit_option digit """
Temp:
  C: Commercial 0C to +70C (1.8 GHz Mini, 1.5 GHz Nano)
  I: Industrial -40C to +85C (1.6 GHz Mini, 1.4 GHz Nano)
