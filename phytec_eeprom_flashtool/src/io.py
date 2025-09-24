"""Module to handle all EEPROM or local disk IO operations."""
from pathlib import Path
import sys
import yaml
from .encoding import decode_base_name_from_raw, YmlParser, EepromData
from .encoding import EEPROM_V2_SIZE, EEPROM_V3_DATA_HEADER_SIZE

TOOL_DIR = Path(__file__).resolve().parent
YML_DIR = TOOL_DIR / Path('../configs')
OUTPUT_DIR = Path.cwd() / 'output'
# Files on our targets
PRODUCT_NAME_FILE = Path("/proc/device-tree/phytec,som-product-name").resolve()
PART_NUMBER_FILE = Path("/proc/device-tree/phytec,som-part-number").resolve()


def get_eeprom_bus(yml_parser: YmlParser) -> Path:
    """Returns the EEPROM sysfs bus path to read from or write to the EEPROM device."""
    i2c_bus = yml_parser['PHYTEC']['i2c_bus']
    i2c_dev = yml_parser['PHYTEC']['i2c_dev']
    return Path(f"/sys/class/i2c-dev/i2c-{i2c_bus}/device/{i2c_bus}-{i2c_dev:04X}/eeprom")


def get_maximum_image_size(yml_parser: YmlParser) -> int:
    """Returns the maximum allowed EEPROM image size in Bytes.
    If 'max_iamge_size' is not defined in the config, this function will default to
    32 Bytes for API v1/v2 and 4096 for API v3+.
    """
    api = int(yml_parser['PHYTEC'].get('api', 2))
    return int(yml_parser['PHYTEC'].get('max_image_size', 32 if api <= 2 else 4096))


def check_maximum_image_size(yml_parser: YmlParser, content: bytes, offset: int = 0):
    """Checks if the image size would exceed the maximum allowed image size.
    This function can throw an SystemExit in case the image size is too big.
    """
    image_size = offset + len(content)
    max_image_size = get_maximum_image_size(yml_parser)
    if image_size > max_image_size:
        raise SystemExit(f"Image size ({len(content)}) at offset ({offset}) would exceed the " \
                         f"maximum allowed size ({max_image_size})")


def get_binary_path(args, eeprom_data: EepromData) -> Path:
    """Returns the path to a local binary file."""
    if "file" in args and args.file:
        return Path(args.file).resolve()
    if eeprom_data.som_type.is_phycore():
        # %s-%s.%s_%s%s_%d
        file_name_beginning = f"{args.som}"
    elif eeprom_data.som_type.is_ksp():
        # %s-%s.%s_%s%s_%d
        file_name_beginning = f"{args.ksx}"
    elif eeprom_data.som_type.is_phycore_ksp():
        # %s-%s-%s.%s_%s%s_%d
        file_name_beginning = f"{args.som}-{args.ksx}"
    elif eeprom_data.som_type.is_phyflex():
        # %s-%s-%s.%s_%s%s_%d
        file_name_beginning = f"{args.som}-{args.id}"
    else:
        raise SystemExit(f"Unknown component type 0x{eeprom_data.som_type:x}")

    file_name = f"{file_name_beginning}-{args.kit}.{eeprom_data.bom_rev}_" \
        f"{eeprom_data.pcb_revision}{eeprom_data.pcb_sub_revision}_" \
        f"{eeprom_data.opttree_revision}"
    return OUTPUT_DIR / file_name


def eeprom_read(yml_parser: YmlParser, size: int, offset: int = 0) -> bytes:
    """Read the content from an I2C EEPROM device."""
    eeprom_bus = get_eeprom_bus(yml_parser)
    try:
        with open(eeprom_bus, 'rb') as eeprom_file:
            eeprom_file.seek(offset)
            eeprom_data = eeprom_file.read(size)
    except IOError as err:
        sys.exit(str(err))
    return bytes(eeprom_data)


def eeprom_write(yml_parser: YmlParser, content: bytes, offset: int = 0):
    """Write a bytes object to an I2C EEPROM device."""
    eeprom_bus = get_eeprom_bus(yml_parser)
    check_maximum_image_size(yml_parser, content, offset)
    try:
        with open(eeprom_bus, 'wb') as eeprom_file:
            eeprom_file.seek(offset)
            eeprom_file.write(content)
            eeprom_file.flush()
    except IOError as err:
        sys.exit(str(err))


def binary_read(binary_file: str, size: int, offset: int = 0) -> bytes:
    """Read the content from a local binary file."""
    try:
        with open(Path(binary_file).resolve(), 'rb') as eeprom_file:
            eeprom_file.seek(offset)
            eeprom_data = eeprom_file.read(size)
    except IOError as err:
        sys.exit(str(err))
    return bytes(eeprom_data)


def binary_write(args, eeprom_fake_data: EepromData, content: bytes, offset: int = 0):
    """Write a byte object to a local file on the file-system."""
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir()
    binary_file = get_binary_path(args, eeprom_fake_data)
    check_maximum_image_size(eeprom_fake_data.yml_parser, content, offset)
    try:
        with open(binary_file, 'wb') as eeprom_file:
            eeprom_file.seek(offset)
            eeprom_file.write(content)
    except IOError as err:
        sys.exit(str(err))


def get_product_name():
    """Try to read the product name within the target BSP."""
    if not PRODUCT_NAME_FILE.exists():
        return (False, "")

    with open(PRODUCT_NAME_FILE, 'r', encoding='UTF-8') as f:
        product_name = f.read().rstrip('\x00')

    return (True, str(product_name))


def get_yml_parser(args) -> dict:
    """Open a YML configuration file at the config directory."""
    if not (args.som or args.ksx) and args.file:
        print("Neither -som nor -ksx are given. Trying to detect information automatically!")
        image = binary_read(args.file, EEPROM_V2_SIZE)
        try:
            base_article = decode_base_name_from_raw(image)
        except AssertionError:
            image = binary_read(args.file, EEPROM_V2_SIZE + EEPROM_V3_DATA_HEADER_SIZE)
            base_article = decode_base_name_from_raw(image)
        print(f"Detected base article config: {base_article}.yml")
        args.som = base_article

    yml_path = YML_DIR
    if args.som and not args.ksx:
        yml_file = YML_DIR / f"{args.som}.yml"
    elif not args.som and args.ksx:
        yml_file = YML_DIR / f"{args.ksx}.yml"
    else:
        yml_file = YML_DIR / f"{args.som}.yml"

    try:
        with open(yml_file, 'r', encoding='UTF-8') as config_file:
            return yaml.safe_load(config_file)
    except IOError as err:
        sys.exit(str(err))
    raise SystemExit(f"Unable to open {yml_path}")
