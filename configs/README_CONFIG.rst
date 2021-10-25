A configuration file contains:
--------------------------------

# PCL-069 PHYTEC EEPROM Flashtool Config File   //SoM description
# board: imx8mm phyboard polis                  //Board information
# Copyright (C) 2020 PHYTEC                     //Copyright

""" The PHYTEC-node configurates the environment for the phytec-eeprom-flashtool """
PHYTEC:
  eeprom_offset: 0x0                            //At the moment, the eeprom offset is 0 for all boards
  eth_name: 'eth0'                              //primary ethernet phy
  i2c_bus: 0                                    //i2c bus number where the eeprom is connected to
  # i2c_dev: 0x59                               //i2c address (id eeprom page)
  i2c_dev: 0x51                                 //i2c address (This is the normal eeprom page. This should be our new default.
  kit_options: 8                                //Number of different options in the option tree
  ep_encoding: '6B17s2s6xB'                     //The ep_encoding is always the same (This is a tool relevant specification)
# ep_encoding_format:
# 6 uchars, 17-len str, 2-len str, 6-len pad, 1 uchar

""" Kit contains all option-headlines from the option tree in the correct order """
Kit:
  0: Controller Mini                            //the first digit from the kit_options
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

---------------------------------------------------------

Using the configuration file:
-----------------------------
There are several ways to flash the eeprom (see README.rst), but we usually
use the option to create a binary at a host and copying it to the target to
flash the eeprom. To do so, you can use a virtual environment:

host$ virtualenv -p python3 venv
host$ . venv/bin/activate
(venv) host$ pip install -r requirements.txt        //install necessary environment packages
(venv) host$ pip install -r requirements-lint.txt   //install necessary lint environment packages

Create a PCL/PCM binary:
------------------------
Example:
--------
Get a binary for PCL-069-3032311I.A0 with board revision 2.
The needed configuration file is PCL-069.yml

(venv) host$ ./src/phytec_eeprom_flashtool.py -o create -som PCL-069 -kit 3032311I -bom A0 -rev 2

Create a PCL/PCM-KSP/KSM binary:
--------------------------------
Example:
--------
Get a binary for PCM-070-KSP-02-0F2243I.A0 with board revision 2.
The needed configuration file is PCM-070.yml

(venv) host$ ./src/phytec_eeprom_flashtool.py -o create -som PCM-070 -ksx KSP-02 -rev 2 -kit 0F2243I -bom A0

Create KSP/KSM binary:
----------------------
Example:
--------
Get a binary for KSP-54-2C514C.A1 with board revision 2.
The needed configuration file is KSP-54.yml

(venv) host$ ./src/phytec_eeprom_flashtool.py -o create -ksx KSP-54 -rev 2 -kit 2C5147C -bom A1
