import binascii


def crc32(text: str) -> str:
    """Return the CRC32 hash of the given string as a hexadecimal string."""
    data: bytes = text.encode()
    crc: int = binascii.crc32(data)
    crc: str = f"{crc:08x}"
    assert len(crc) == 8
    return crc


hasher = crc32
