# This file is based on scripts from the main badge-2024-software repo

from machine import I2C
from system.hexpansion.header import HexpansionHeader, write_header
from system.hexpansion.util import (
    detect_eeprom_addr,
    get_hexpansion_block_devices,
    read_hexpansion_header,
)
import vfs
import os
import sys


# Set up i2c
port = 2  # <<-- Customize!!
i2c = I2C(port)

# Detect eeprom address
addr, addr_len = detect_eeprom_addr(i2c)
print(f"Detected eeprom at {hex(addr)}")

header = HexpansionHeader(
    manifest_version="2024",
    fs_offset=64,
    eeprom_page_size=64,
    eeprom_total_size=32768,
    vid=0x4D42,
    pid=0x5EE5,
    unique_id=0,
    friendly_name="Screen",
)

# Write and read back header
write_header(
    port, header, addr=addr, addr_len=addr_len, page_size=header.eeprom_page_size
)
header = read_hexpansion_header(i2c, addr, set_read_addr=True, addr_len=addr_len)
if header is None:
    raise RuntimeError(f"Failed to read back hexpansion header for hexpansion {port}")

# Get block devices
try:
    eep, partition = get_hexpansion_block_devices(i2c, header, addr, addr_len=addr_len)
    vfs.VfsLfs2.mkfs(partition)
except Exception as e:
    raise RuntimeError(f"Failed to get block devices for hexpansion {port}: {e}")

mountpoint = f"/hexpansion"
try:
    vfs.mount(partition, mountpoint)
except Exception as e:
    raise RuntimeError(f"Failed to mount partition for hexpansion {port}: {e}")

print(f"Mounted hexpansion {port} at {mountpoint}")

# Remove any pre-existing files
files = os.listdir(mountpoint)
for f in files:
    os.remove(f"{mountpoint}/{f}")

