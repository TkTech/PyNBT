# -*- coding: utf8 -*-
"""
Support for reading Minecraft region files.

This format is simple, albiet with nowhere close to optimal
performance both in speed or size.
"""
import zlib
import struct
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from datetime import date

from .nbt import NBTFile


def chunk_location(l):
    """
    Returns the offset (in bytes) and size (in bytes) of the chuck for
    the given location.
    """
    offset = ((l >> 8) & 0xFF) + ((l >> 16) & 0xFF) + ((l >> 32) & 0xFF)
    size = l & 0xFF

    return (offset * 4096, size * 4096)


class RegionFile(list):
    def __init__(self, io=None):
        if io is None:
            return

        src = open(io, 'rb') if isinstance(io, basestring) else io

        def read(fmt):
            return struct.unpack(fmt, src.read(struct.calcsize(fmt)))

        t = read('>1024i1024i')
        # The first 1024 integers are the location table entries,
        # and the following 1024 entries are the timestamps.
        chunks = zip(t[:1024], t[1024:])

        for location, timestamp in chunks:
            offset, size = chunk_location(location)
            if offset == 0:
                # This chunk hasn't been allocated yet.
                self.append((None, None))
                continue

            src.seek(offset)
            length, compression = read('>ib')

            if compression == 0:
                # Usually seems to be an improperly erased chunk.
                self.append((None, None))
                continue
            elif compression == 1:
                # gzip'd chunk. This never occurs in practice, 
                # but we'll support it anyways.
                buff = StringIO(src.read(length))
                self.append((
                    timestamp,
                    NBTFile(buff, compressed=True)
                ))
            elif compression == 2:
                # zlib'd chunk. This is the compression scheme actually
                # used in practice.
                buff = StringIO(zlib.decompress(src.read(length)))
                self.append((
                    timestamp,
                    NBTFile(buff, compressed=False)
                ))

    def pretty(self):
        """
        Returns a formated representation of this region and the chunks
        found within it.
        """
        t = []
        for timestamp, chunk in self:
            if chunk is None:
                continue
            t.append(chunk.pretty())
        return '\n'.join(t)
