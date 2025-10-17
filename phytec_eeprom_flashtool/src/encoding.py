"""Module to handle the en- and decoding of the EEPROM data."""
#pylint: disable=import-error
from typing import Dict
from dataclasses import dataclass
from enum import Enum
import struct
import sys

from .common import str_to_revision
from .common import sub_revision_to_str
from .common import crc8_checksum_calc
from .common import hw8_checksum_calc
from .blocks import API_V3_SUB_VERSION
from .blocks import EepromV3BlockInterface
from .blocks import unpack_block

MAX_KIT_OPTS = 17
# 1 uchar for the API version
ENCODING_API_VERSION = "<1B"
# 2 uchars, 2-len pad, 21-len str, 6-len pad, 1 uchar
ENCODING_API1 = "<2B2x21s6xB"
# 6 uchars, 17-len str, 2-len str, 6-len pad, 1 uchar
ENCODING_API2 = "<6B17s2s6xB"
# 1 ushort, 2 uchars, 3 reserved, 1 uchar
ENCODING_API3_DATA_HEADER = "<1H2B3x1B"

# All values in bytes
EEPROM_V1_SIZE = 32
EEPROM_V2_SIZE = 32
EEPROM_V3_DATA_HEADER_SIZE = 8
# Relative address inside the v3 data payload
EEPROM_V3_DATA_PAYLOAD_START = 0

YmlParser = Dict[str, Dict[str, str]]


PFL_MAPPING = {
    0: "PT",
    1: "SP",
    2: "KP",
    3: "KM"
}


class ComponentType(Enum):
    """All supported component types."""
    PCM = 0
    PCL = 1
    KSP = 2
    KSM = 3
    PCM_KSP = 4
    PCM_KSM = 5
    PCL_KSP = 6
    PCL_KSM = 7
    PFL_G_PT = 8
    PFL_G_SP = 9
    PFL_G_KP = 10
    PFL_G_KM = 11
    INVALID = 0xFF

    def is_phycore(self):
        """Returns True if the component is a phyCORE (PCM or PCL)."""
        return ComponentType.PCM.value <= self.value <= ComponentType.PCL.value

    def is_ksp(self):
        """Returns True if the component is KSP or KSM."""
        return ComponentType.KSP.value <= self.value <= ComponentType.KSM.value

    def is_phycore_ksp(self):
        """Returns True if the component is a phyCORE KSP/KSM variant."""
        return ComponentType.PCM_KSP.value <= self.value <= ComponentType.PCL_KSM.value

    def is_phyflex(self):
        """Returns True if the component is a phyFLEX (PFL)."""
        return ComponentType.PFL_G_PT.value <= self.value <= ComponentType.PFL_G_KM.value

    def get_phyflex_prefix(self):
        """Returns the PFL prefix (e.g., 'PT' for PFL-G-PT)."""
        return PFL_MAPPING[self.value - ComponentType.PFL_G_PT.value]


#pylint: disable=too-many-instance-attributes
@dataclass
class EepromData:
    """Data class to hold all values of the API v2 EEPROM structure."""
    def __init__(self, yml_parser: YmlParser):
        self.yml_parser = yml_parser
        # API v3 content
        self.blocks: list = []

    api_version: int
    pcb_revision: int
    pcb_sub_revision: str
    opttree_revision: str
    sub_revisions: str
    som_type: ComponentType
    base_article_number: int
    kit_opt: str
    bom_rev: str
    crc8: int
    hw8: int
    ksp_number: int = 0
    option_id: str = ""
    # API v3 content
    v3_sub_version: int = API_V3_SUB_VERSION
    v3_header_crc8: int = 0
    v3_payload_length: int = 0
    v3_block_count: int = 0  # only required to unpack blocks. Use length of blocks.
    v3_next_block_address: int = EEPROM_V3_DATA_PAYLOAD_START

    def is_v1(self) -> bool:
        """Returns a boolean whether the EEPROM data are API v1 or not."""
        return self.api_version == 1

    def is_v3(self) -> bool:
        """Returns a boolean whether the EEPROM data are API v3 or not."""
        return self.api_version == 3

    def base_name(self) -> str:
        """Returns the product base name"""
        base_name = f"{get_som_type_name_by_value(self.som_type).split('-')[0]}-"
        if self.som_type.is_phycore():
            base_name += f"{self.base_article_number:03}"
        elif self.som_type.is_ksp():
            base_name += f"{self.ksp_number << 16 + self.base_article_number:04}"
        elif self.som_type.is_phycore_ksp():
            base_name += f"{self.base_article_number:03}"
        elif self.som_type.is_phyflex():
            base_name += f"{get_som_type_name_by_value(self.som_type).split('-')[1]}-"
            base_name += f"{self.base_article_number:02}"
        else:
            sys.exit(f"Unknown component type 0x{self.som_type:x}!")
        return base_name

    def full_name(self) -> str:
        """Decodes the product full name from ep_data"""
        base_name = self.base_name()
        if self.som_type.is_phycore():
            extended_opt = int(self.yml_parser['PHYTEC'].get('extended_options', 0))
            full_name = f"{base_name}"
            if extended_opt:
                full_name += f"-{self.kit_opt[:-extended_opt]}"
            else:
                full_name += f"-{self.kit_opt}"
        elif self.som_type.is_ksp():
            full_name = base_name
        elif self.som_type.is_phycore_ksp():
            som_type = get_som_type_name_by_value(self.som_type).split('-')
            full_name = f"{base_name}-{som_type[1]}{self.ksp_number:02}"
        elif self.som_type.is_phyflex():
            full_name = f"{base_name}-{self.option_id}"
        else:
            sys.exit(f"Unknown component type 0x{self.som_type:x}!")

        return f"{full_name}.{self.bom_rev}"

    def add_block(self, block: EepromV3BlockInterface):
        """Adds an EEPROM block to the EEPROM data."""
        self.v3_next_block_address += block.length
        self.blocks.append(block)


def get_eeprom_data(args, yml_parser: YmlParser) -> EepromData:
    """Generates an EEPROM data class and fill all information with argparser information."""
    eeprom_data = EepromData(yml_parser)
    eeprom_data.api_version = int(yml_parser['PHYTEC'].get('api', 2))
    eeprom_data.pcb_revision, eeprom_data.pcb_sub_revision = str_to_revision(args.pcb)
    eeprom_data.opttree_revision = str(yml_parser['PHYTEC'].get('optiontree_rev', 0))
    eeprom_data.sub_revisions = eeprom_data.opttree_revision + eeprom_data.pcb_sub_revision
    eeprom_data.pcb_sub_revision = sub_revision_to_str(eeprom_data.pcb_sub_revision)
    eeprom_data.som_type = get_som_type(args)
    if eeprom_data.som_type.is_phycore():
        eeprom_data.base_article_number = int(args.som[4:])
    elif eeprom_data.som_type.is_ksp():
        if int(args.ksx[4:]) <= 255:
            eeprom_data.base_article_number = int(args.ksx[4:])
        else:
            ksp_bytes = f"{args.ksx[4:]:016b}"
            ksp_lower_byte = int(ksp_bytes[8:])
            ksp_higher_byte = int(ksp_bytes[:8])
            eeprom_data.base_article_number = int(ksp_lower_byte)
            eeprom_data.ksp_number = int(ksp_higher_byte)
    elif eeprom_data.som_type.is_phycore_ksp():
        eeprom_data.base_article_number = int(args.som[4:])
        if int(args.ksx[3:]) <= 255:
            eeprom_data.ksp_number = int(args.ksx[3:])
        else:
            sys.exit('KSX-number out of bounce.')
    elif eeprom_data.som_type.is_phyflex():
        eeprom_data.base_article_number = int(args.som[-2:])
        eeprom_data.option_id = args.id
        eeprom_data.ksp_number = int(args.id[2:])
    else:
        sys.exit(f"Unknown component type 0x{eeprom_data.som_type:x}!")
    eeprom_data.bom_rev = args.bom
    eeprom_data.kit_opt = args.kit.replace('-', '')

    return eeprom_data


def eeprom_data_to_struct(eeprom_data: EepromData) -> bytes:
    """Pack the EEPROM data into a string."""
    if eeprom_data.is_v1():
        if eeprom_data.som_type.is_ksp():
            # KSP numbers require 4 integer digits but v1 has only one byte allocated.
            # We don't have standalone KSM products.
            sys.exit("This API v1 implementation does not support KSPs anymore!")

        kit_opt_full = f"{eeprom_data.kit_opt}{eeprom_data.bom_rev}"
        kit_opt_full = kit_opt_full + '\0' * (21 - len(kit_opt_full))
        eeprom_struct = struct.pack(
            ENCODING_API1,
            eeprom_data.api_version,
            eeprom_data.pcb_revision,
            bytes(kit_opt_full, 'utf-8'),
            0  # CRC8
        )
        eeprom_data.crc8 = crc8_checksum_calc(eeprom_struct[:-1])
        eeprom_data.hw8 = hw8_checksum_calc(eeprom_struct[:-1])
        eeprom_struct = eeprom_struct[:-1] + struct.pack('B', eeprom_data.hw8)

        return eeprom_struct

    kit_opt_full = eeprom_data.kit_opt + '\0' * (MAX_KIT_OPTS - len(eeprom_data.kit_opt))
    if len(kit_opt_full) > MAX_KIT_OPTS:
        raise AssertionError(f"Number of options exceeds maximum of {MAX_KIT_OPTS}")
    eeprom_struct = struct.pack(
        ENCODING_API2,
        eeprom_data.api_version,
        eeprom_data.pcb_revision,
        int(eeprom_data.sub_revisions, 2),
        eeprom_data.som_type.value,
        eeprom_data.base_article_number,
        eeprom_data.ksp_number,
        bytes(kit_opt_full, 'utf-8'),
        bytes(eeprom_data.bom_rev, 'utf-8'),
        0  # CRC8
    )
    eeprom_data.crc8 = crc8_checksum_calc(eeprom_struct[:-1])
    eeprom_data.hw8 = 0
    eeprom_struct = eeprom_struct[:-1] + struct.pack('B', eeprom_data.crc8)

    if eeprom_data.is_v3():
        eeprom_struct += eeprom_data_to_data_header(eeprom_data)

    return eeprom_struct


def eeprom_data_to_data_header(eeprom_data: EepromData) -> bytes:
    """Pack the EEPROM data in the data header."""
    eeprom_data.v3_payload_length = sum(block.length for block in eeprom_data.blocks)
    eeprom_struct = struct.pack(
        ENCODING_API3_DATA_HEADER[:-2],
        eeprom_data.v3_payload_length,
        len(eeprom_data.blocks),
        eeprom_data.v3_sub_version
    )
    eeprom_data.v3_header_crc8 = crc8_checksum_calc(eeprom_struct)
    eeprom_struct += struct.pack('B', eeprom_data.v3_header_crc8)

    return eeprom_struct


def eeprom_data_to_blocks(eeprom_data: EepromData) -> bytes:
    """Pack all EEPROM blocks."""
    eeprom_blocks = bytes()
    next_block_address = EEPROM_V3_DATA_PAYLOAD_START
    for block in eeprom_data.blocks:
        next_block_address += block.length
        eeprom_blocks += block.pack(next_block_address)
    return eeprom_blocks


def struct_to_eeprom_data(eeprom_struct: bytes, yml_parser: YmlParser) -> EepromData:
    """Unpack the EEPROM struct."""
    api_version = int(struct.unpack(ENCODING_API_VERSION, eeprom_struct[:1])[0])
    if api_version >= 2:
        return struct_to_eeprom_data_v2(eeprom_struct, yml_parser)
    return struct_to_eeprom_data_v1(eeprom_struct, yml_parser)


def struct_to_eeprom_data_v1(eeprom_struct: bytes, yml_parser: YmlParser) -> EepromData:
    """Unpack the EEPROM struct with API v1. Only the PCM-057 uses v1."""
    unpacked = struct.unpack(ENCODING_API1, eeprom_struct[:EEPROM_V1_SIZE])

    if hw8_checksum_calc(eeprom_struct[:EEPROM_V2_SIZE - 1]) != int(unpacked[3]):
        raise AssertionError("Checksum mismatch in the first 32 bytes!")

    eeprom_data = EepromData(yml_parser)
    eeprom_data.api_version = unpacked[0]
    eeprom_data.pcb_revision = unpacked[1]
    eeprom_data.som_type = ComponentType.PCM
    # Only PCM-057 is using API v1
    eeprom_data.base_article_number = 57
    # No KSP support
    eeprom_data.ksp_number = 0
    if yml_parser is not None:
        #This will not be read when yml_parser is not set
        full_kit_opt = unpacked[2].decode('utf-8')
        eeprom_data.bom_rev = full_kit_opt[len(yml_parser['Kit']):len(yml_parser['Kit'])+2]
        eeprom_data.kit_opt = full_kit_opt[:len(yml_parser['Kit'])]
        eeprom_data.crc8 = crc8_checksum_calc(eeprom_struct[:EEPROM_V2_SIZE - 1])
        eeprom_data.hw8 = int(unpacked[3])

    eeprom_data.pcb_sub_revision = "0"
    eeprom_data.opttree_revision = "0"
    return eeprom_data


def struct_to_eeprom_data_v2(eeprom_struct: bytes, yml_parser: YmlParser) -> EepromData:
    """Unpack the EEPROM struct with API v2 or higher layout."""
    if crc8_checksum_calc(eeprom_struct[:EEPROM_V2_SIZE]):
        raise AssertionError("Checksum mismatch in the first 32 bytes!")

    unpacked = struct.unpack(ENCODING_API2, eeprom_struct[:EEPROM_V2_SIZE])

    eeprom_data = EepromData(yml_parser)
    eeprom_data.api_version = unpacked[0]
    eeprom_data.pcb_revision = unpacked[1]
    eeprom_data.sub_revisions = unpacked[2]
    eeprom_data.som_type = ComponentType(unpacked[3])
    eeprom_data.base_article_number = unpacked[4]
    eeprom_data.ksp_number = unpacked[5]
    if yml_parser is not None:
        # This will not be read when yml_parser is not set
        eeprom_data.bom_rev = unpacked[7].decode('utf-8')
        eeprom_data.crc8 = unpacked[8]
        eeprom_data.hw8 = 0
        eeprom_data.kit_opt = unpacked[6].decode('utf-8')[:len(yml_parser['Kit'])]
    eeprom_data.sub_revisions = format(eeprom_data.sub_revisions, '08b')
    eeprom_data.pcb_sub_revision = eeprom_data.sub_revisions[4:]
    eeprom_data.opttree_revision = format(int(eeprom_data.sub_revisions[:4], 2), '04b')
    eeprom_data.pcb_sub_revision = sub_revision_to_str(eeprom_data.pcb_sub_revision)

    if eeprom_data.som_type.is_phyflex():
        prefix = eeprom_data.som_type.get_phyflex_prefix()
        eeprom_data.option_id = f"{prefix}{eeprom_data.ksp_number:03}"

    if eeprom_data.is_v3():
        eeprom_data = data_header_to_eeprom_data(eeprom_struct, eeprom_data)

    return eeprom_data


def data_header_to_eeprom_data(eeprom_struct: bytes, eeprom_data: EepromData) -> EepromData:
    """Unpack the EEPROM data header."""
    unpacked = struct.unpack(ENCODING_API3_DATA_HEADER,
                             eeprom_struct[-EEPROM_V3_DATA_HEADER_SIZE:])

    if crc8_checksum_calc(eeprom_struct[-EEPROM_V3_DATA_HEADER_SIZE:]):
        raise AssertionError("Data header crc8 mismatch!")

    eeprom_data.v3_payload_length = int(unpacked[0])
    eeprom_data.v3_block_count = int(unpacked[1])
    eeprom_data.v3_sub_version = int(unpacked[2])
    eeprom_data.v3_header_crc8 = int(unpacked[3])

    return eeprom_data


def blocks_to_eeprom_data(eeprom_data: EepromData, eeprom_blocks: bytes) -> EepromData:
    """Unpack all EEPROM blocks."""
    for _ in range(eeprom_data.v3_block_count):
        block_size = unpack_block(eeprom_data, eeprom_blocks)
        eeprom_blocks = eeprom_blocks[block_size:]
    return eeprom_data


def print_eeprom_data(eeprom_data: EepromData):
    """ Print out the eeprom data. """
    pcb_rev = str(eeprom_data.pcb_revision)
    if eeprom_data.pcb_sub_revision != "0":
        pcb_rev += eeprom_data.pcb_sub_revision

    if len(eeprom_data.kit_opt) != len(eeprom_data.yml_parser['Kit']):
        opt_error = f"Passed kit options {eeprom_data.kit_opt} mismatch number of options for " \
            f"this product: {len(eeprom_data.yml_parser['Kit'])}"
        raise ValueError(opt_error)

    newline = '\n'
    kit_options_verbose = []
    kit_opt_length = 17
    for index, kit_opt in eeprom_data.yml_parser['Kit'].items():
        if (len(kit_opt) + 1) > kit_opt_length:
            kit_opt_length = len(kit_opt) + 1
    for index, kit_opt in eeprom_data.yml_parser['Kit'].items():
        option = eeprom_data.kit_opt[int(index)]
        if option == '\x00':
            option = "0"
        kit_options_verbose.append(f"{kit_opt.ljust(kit_opt_length)}:  " \
                                   f"{eeprom_data.yml_parser[kit_opt][option]}")

    kit_opt_string = eeprom_data.kit_opt.replace('\x00','#')
    extended_options = int(eeprom_data.yml_parser['PHYTEC'].get('extended_options', 0))
    opts = kit_opt_string[:-extended_options] if extended_options else kit_opt_string
    ext_opts = kit_opt_string[-extended_options:] if extended_options else "-"

    output = f"""EEPROM Content
##############

Decoded Information
*******************
{"Full name":17s}:  {eeprom_data.full_name()}
{"PCB revision":17s}:  {pcb_rev}

Raw Information
***************
{"API version":17s}:  {eeprom_data.api_version}
{"SOM PCB rev.":17s}:  {eeprom_data.pcb_revision}-{eeprom_data.pcb_sub_revision}
{"Optiontree rev.":17s}:  {int(eeprom_data.opttree_revision, 2)}
{"SOM type":17s}:  {get_som_type_name_by_value(eeprom_data.som_type)}

Base Article Number
===================
{"Product number":17s}:  {eeprom_data.base_article_number}
{"KSx number":17s}:  {eeprom_data.ksp_number  if eeprom_data.ksp_number else "-"}
{"Options":17s}:  {opts}
{"Extended Options":17s}:  {ext_opts}

Verbose Kit Options
*******************
{newline.join(kit_options_verbose)}

Extras
******
{"CRC-Checksum":17s}:  0x{eeprom_data.crc8:x}
"""
    print(output)
    if eeprom_data.api_version <= 2:
        return
    output_v3 = f"""
API v3 Content
##############
{"API sub version":17s}:  {eeprom_data.v3_sub_version}
{"Number of blocks":17s}:  {len(eeprom_data.blocks)}
{"CRC-Checksum":17s}:  0x{eeprom_data.v3_header_crc8:x}
"""
    print(output_v3)
    for block in eeprom_data.blocks:
        print(f"""{block!r}
""")


def decode_base_name_from_raw(eeprom_raw):
    """Returns the base name from raw EEPROM data."""
    eeprom_data = struct_to_eeprom_data(eeprom_raw, None)
    return eeprom_data.base_name()


def get_som_type_name_by_value(som_value: ComponentType) -> str:
    """Returns the som type name for the passed number value"""
    return ComponentType(som_value).name.replace('_', '-')


def get_som_type(args) -> ComponentType:
    """Returns the som type according to command-line arguments."""
    if args.som.startswith('PFL-'):
        som_type = f"{args.som[:-3]}-{args.id[:2]}"
    else:
        if args.ksx and args.som:
            som_type = f"{args.som[:3]}-{args.ksx[:3]}"
        elif args.ksx and not args.som:
            som_type = args.ksx[:3]
        else:
            som_type = args.som[:3]

    if som_type.replace('-', '_') not in ComponentType.__members__:
        return ComponentType.INVALID

    return ComponentType[som_type.replace('-', '_')]
