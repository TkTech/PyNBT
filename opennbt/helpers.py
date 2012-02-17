import gzip
import struct

def is_pocket(io, compressed=True):
    """
    Returns `False` if the given file `io` is not an (Android) Minecraft
    NBT file.
    """
    fin = open(io, 'rb') if isinstance(io, basestring) else io
    src = gzip.GzipFile(fileobj=fin, mode='rb') if compressed else fin

    def read(fmt):
        return struct.unpack(fmt, src.read(struct.calcsize(fmt)))

    lead = read('<4b')

    if isinstance(io, basestring):
        fin.close()

    # The entities.dat header, "ENT\x00".
    if lead == (0x45, 0x4E, 0x54, 0x00):
        # 4 byte magic,
        # 4 byte version?
        # 4 byte file length, minus header.
        return "entities.dat"
    elif lead[0] != 0x0A:
        # 4 byte version?
        # 4 byte file length, minus header.
        return "level.dat"

    return False
