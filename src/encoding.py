"""Module to handle the en- and decoding of the EEPROM data."""
#pylint: disable=import-error
from typing import Dict
from dataclasses import dataclass
import struct
import sys
import crc8  # type: ignore

from src.common import str_to_revision, sub_revision_to_str

# Defaults defined by the PHYTEC EEPROM API version
API_VERSION = 2
MAX_KIT_OPTS = 17
DEFAULT_EP_FORMAT = "6B"
# 6 uchars, 17-len str, 2-len str, 6-len pad, 1 uchar
ENCODING_API2 = "6B17s2s6xB"

YmlParser = Dict[str, Dict[str, str]]


SOM = {
    "PCM": 0x0,
    "PCL": 0x1,
    "KSP": 0x2,
    "KSM": 0x3,
    "PCM-KSP": 0x4,
    "PCM-KSM": 0x5,
    "PCL-KSP": 0x6,
    "PCL-KSM": 0x7
}


#pylint: disable=too-many-instance-attributes
@dataclass
class EepromData:
    """Data class to hold all values of the API v2 EEPROM structure."""
    def __init__(self, yml_parser: YmlParser):
        self.yml_parser = yml_parser

    api_version: int
    som_revision: int
    som_sub_revision: str
    opttree_revision: str
    sub_revisions: str
    som_type: int
    base_article_number: int
    kit_opt: str
    kit_opt_full: str
    bom_rev: str
    crc8: int
    ksp_number: int = 0


    def base_name(self) -> str:
        """Returns the product base name"""
        base_name = f"{get_som_type_name_by_value(self.som_type).split('-')[0]}-"
        if self.som_type <= 1:
            base_name += f"{self.base_article_number:03}"
        elif self.som_type <= 3:
            base_name += f"{self.ksp_number << 16 + self.base_article_number:04}"
        else:
            base_name += f"{self.base_article_number:03}"
        return base_name


    def full_name(self) -> str:
        """Decodes the product full name from ep_data"""
        base_name = self.base_name()
        if self.som_type <= 1:
            full_name = f"{base_name}-{self.kit_opt}"
        elif self.som_type <= 3:
            full_name = base_name
        else:
            som_type = get_som_type_name_by_value(self.som_type).split('-')
            full_name = f"{base_name}-{som_type[1]}{self.ksp_number:02}"

        return f"{full_name}.{self.bom_rev}"


def get_eeprom_data(args, yml_parser: YmlParser) -> EepromData:
    """Generates an EEPROM data class and fill all information with argparser information."""
    eeprom_data = EepromData(yml_parser)
    eeprom_data.api_version = API_VERSION
    eeprom_data.som_revision, eeprom_data.som_sub_revision = str_to_revision(args.rev)
    eeprom_data.opttree_revision = format(int(args.opt), '04b')
    eeprom_data.sub_revisions = eeprom_data.opttree_revision + eeprom_data.som_sub_revision
    eeprom_data.som_sub_revision = sub_revision_to_str(eeprom_data.som_sub_revision)
    eeprom_data.som_type = get_som_type(args)
    if eeprom_data.som_type <= 1:
        eeprom_data.base_article_number = int(args.som[4:])
    elif eeprom_data.som_type <= 3:
        if int(args.ksx[4:]) <= 255:
            eeprom_data.base_article_number = int(args.ksx[4:])
        else:
            ksp_bytes = f"{args.ksx[4:]:016b}"
            ksp_lower_byte = int(ksp_bytes[8:])
            ksp_higher_byte = int(ksp_bytes[:8])
            eeprom_data.base_article_number = int(ksp_lower_byte)
            eeprom_data.ksp_number = int(ksp_higher_byte)
    else:
        eeprom_data.base_article_number = int(args.som[4:])
        if int(args.ksx[3:]) <= 255:
            eeprom_data.ksp_number = int(args.ksx[3:])
        else:
            sys.exit('KSX-number out of bounce.')
    eeprom_data.bom_rev = args.bom
    eeprom_data.kit_opt = args.kit
    eeprom_data.kit_opt_full = eeprom_data.kit_opt
    eeprom_data.kit_opt_full += '\0' * (MAX_KIT_OPTS - len(eeprom_data.kit_opt))

    return eeprom_data


def crc8_checksum_calc(eeprom_struct: bytes) -> int:
    """Create a CRC8 checksum from the packed EEPROM data."""
    hash_ = crc8.crc8()
    hash_.update(eeprom_struct)
    crc8_sum = hash_.hexdigest()
    return int(crc8_sum, 16)


def eeprom_data_to_struct(eeprom_data: EepromData) -> bytes:
    """Pack the EEPROM data into a string."""
    length = len(ENCODING_API2)
    eeprom_struct = struct.pack(
        ENCODING_API2[:length-3],
        eeprom_data.api_version,
        eeprom_data.som_revision,
        int(eeprom_data.sub_revisions, 2),
        eeprom_data.som_type,
        eeprom_data.base_article_number,
        eeprom_data.ksp_number,
        bytes(eeprom_data.kit_opt_full, 'utf-8'),
        bytes(eeprom_data.bom_rev, 'utf-8')
    )
    eeprom_struct += struct.pack(ENCODING_API2[7:9])
    eeprom_data.crc8 = crc8_checksum_calc(eeprom_struct)
    eeprom_struct += struct.pack('B', eeprom_data.crc8)

    return eeprom_struct


def struct_to_eeprom_data(eeprom_struct: bytes, yml_parser: YmlParser) -> EepromData:
    """Unpack the EEPROM struct which is read out of the EEPROM device."""
    try:
        unpacked = struct.unpack(ENCODING_API2, eeprom_struct)

        eeprom_data = EepromData(yml_parser)
        eeprom_data.api_version = unpacked[0]
        eeprom_data.som_revision = unpacked[1]
        eeprom_data.sub_revisions = unpacked[2]
        eeprom_data.som_type = unpacked[3]
        eeprom_data.base_article_number = unpacked[4]
        eeprom_data.ksp_number = unpacked[5]
        if len(eeprom_struct) > 6:
            #This will not be read when DEFAULT_EP_FORMAT is used
            eeprom_data.kit_opt_full = unpacked[6].decode('utf-8')
            eeprom_data.bom_rev = unpacked[7].decode('utf-8')
            eeprom_data.crc8 = unpacked[8]
            eeprom_data.kit_opt = eeprom_data.kit_opt_full[:len(yml_parser['Kit'])]

        eeprom_data.sub_revisions = format(eeprom_data.sub_revisions, '08b')
        eeprom_data.som_sub_revision = eeprom_data.sub_revisions[4:]
        eeprom_data.opttree_revision = format(int(eeprom_data.sub_revisions[:4], 2), '04b')
        eeprom_data.som_sub_revision = sub_revision_to_str(eeprom_data.som_sub_revision)
        return eeprom_data
    except IOError as err:
        sys.exit(str(err))


def print_eeprom_data(eeprom_data: EepromData):
    """ Print out the eeprom data. """
    pcb_rev = str(eeprom_data.som_revision)
    if eeprom_data.som_sub_revision != "0":
        pcb_rev += eeprom_data.som_sub_revision

    newline = '\n'
    kit_options_verbose = []
    for index, kit_opt in eeprom_data.yml_parser['Kit'].items():
        option = eeprom_data.kit_opt[int(index)]
        kit_options_verbose.append(f"{kit_opt:16s}:  {eeprom_data.yml_parser[kit_opt][option]}")

    output = f"""EEPROM Content
##############

Decoded Information
*******************
{"Full name":16s}:  {eeprom_data.full_name()}
{"PCB revision":16s}:  {pcb_rev}

Raw Information
***************
{"API version":16s}:  {eeprom_data.api_version}
{"SOM PCB rev.":16s}:  {eeprom_data.som_revision}-{eeprom_data.som_sub_revision}
{"Optiontree rev.":16s}:  {int(eeprom_data.opttree_revision, 2)}
{"SOM type":16s}:  {get_som_type_name_by_value(eeprom_data.som_type)}

Base Article Number
===================
{"Product number":16s}:  {eeprom_data.base_article_number}
{"KSx number":16s}:  {eeprom_data.ksp_number  if eeprom_data.ksp_number else "-"}
{"Options":16s}:  {eeprom_data.kit_opt}

Verbose Kit Options
*******************
{newline.join(kit_options_verbose)}

Extras
******
{"CRC-Checksum":16s}:  0x{eeprom_data.crc8:x}
"""
    print(output)


def decode_base_name_from_raw(eeprom_raw):
    """Returns the base name from raw EEPROM data."""
    eeprom_data = struct_to_eeprom_data(eeprom_raw, {'PHYTEC':{'ep_encoding' : DEFAULT_EP_FORMAT}})
    return eeprom_data.base_name()


def get_som_type_name_by_value(som_value: int) -> str:
    """Returns the som type name for the passed number value"""
    return [k for k, v in SOM.items() if v == som_value][0]


def get_som_type(args) -> int:
    """Returns the som type according to command-line arguments."""
    if args.ksx and args.som:
        som_type = f"{args.som[:3]}-{args.ksx[:3]}"
    elif args.ksx and not args.som:
        som_type = args.ksx[:3]
    else:
        som_type = args.som[:3]

    return SOM.get(som_type, 0xf)
