#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Implements reading & writing for the Minecraft Named Binary Tag (NBT) format,
created by Markus Petersson.

.. moduleauthor:: Tyler Kennedy <tk@tkte.ch>
"""

__authors__ = ('Tyler Kennedy <tk@tkte.ch>', )

import gzip
from struct import unpack, pack


def _write_utf8(wt, value):
    l = len(value)
    wt('h%ss' % l, l, value)


class BaseTag(object):
    def __init__(self, value, name=None):
        self.name = name
        self.value = value

    @staticmethod
    def _read_utf8(read):
        """Reads a length-prefixed UTF-8 string."""
        name_length = read('H', 2)[0]
        return read(
            '{}s'.format(name_length),
            name_length
        )[0].decode('utf-8')

    @classmethod
    def read(cls, read, has_name=True):
        """
        Read the tag in using the reader `rd`.
        If `has_name` is `False`, skip reading the tag name.
        """
        name = cls._read_utf8(read) if has_name else None

        if cls is TAG_Compound:
            # A TAG_Compound is almost identical to Python's native dict()
            # object, or a Java HashMap.
            final = {}
            while True:
                # Find the type of each tag in a compound in turn.
                tag = read('b', 1)[0]
                if tag == 0:
                    # A tag of 0 means we've reached TAG_End, used to terminate
                    # a TAG_Compound.
                    break
                # We read in each tag in turn, using its name as the key in
                # the dict (Since a compound cannot have repeating names,
                # this works fine).
                tmp = _tags[tag].read(read)
                final[tmp.name] = tmp
            return cls(final, name=name)
        elif cls is TAG_List:
            # A TAG_List is a very simple homogeneous array, similar to
            # Python's native list() object, but restricted to a single type.
            tag_type, length = read('bi', 5)
            tag_read = _tags[tag_type].read
            return cls(
                tag_type,
                [tag_read(read, has_name=False) for x in range(0, length)],
                name=name
            )
        elif cls is TAG_String:
            # A simple length-prefixed UTF-8 string.
            value = cls._read_utf8(read)
            return cls(value, name=name)
        elif cls is TAG_Byte_Array:
            # A simple array of (signed) bytes.
            length = read('i', 4)[0]
            return cls(read('{}b'.format(length), length), name=name)
        elif cls is TAG_Int_Array:
            # A simple array of (signed) 4-byte integers.
            length = read('i', 4)[0]
            return cls(read('{}i'.format(length), length * 4), name=name)
        elif cls is TAG_Byte:
            # A single (signed) byte.
            return cls(read('b', 1)[0], name=name)
        elif cls is TAG_Short:
            # A single (signed) short.
            return cls(read('h', 2)[0], name=name)
        elif cls is TAG_Int:
            # A signed (signed) 4-byte int.
            return cls(read('i', 4)[0], name=name)
        elif cls is TAG_Long:
            # A single (signed) 8-byte long.
            return cls(read('q', 8)[0], name=name)
        elif cls is TAG_Float:
            # A single single-precision floating point value.
            return cls(read('f', 4)[0], name=name)
        elif cls is TAG_Double:
            # A single double-precision floating point value.
            return cls(read('d', 8)[0], name=name)

    def write(self, wt):
        """
        Write the tag to disk using the writer `wt`.
        If the tag's `name` is None, no name will be written.
        """
        if self.name is not None:
            if isinstance(self, NBTFile):
                wt('b', 0x0A)
            else:
                wt('b', _tags.index(self.__class__))
            _write_utf8(wt, self.name)

        if isinstance(self, TAG_List):
            wt('bi', self._type, len(self.value))
            for item in self.value:
                if not isinstance(item, _tags[self._type]):
                    item = _tags[self._type](item)
                item.write(wt)
        elif isinstance(self, TAG_Compound):
            for v in self.value.itervalues():
                v.write(wt)
            wt('b', 0)
        elif isinstance(self, TAG_String):
            l = len(self.value)
            wt('h%ss' % l, l, self.value)
        elif isinstance(self, TAG_Int_Array):
            l = len(self.value)
            wt('i%si' % l, l, *self.value)
        elif isinstance(self, TAG_Byte_Array):
            l = len(self.value)
            wt('i%ss' % l, l, self.value)
        else:
            wt(self.STRUCT_FMT, self.value)

    def pretty(self, indent=0, indent_str='  '):
        """
        Pretty-print a tag in the same general style as Markus's example
        output.
        """
        return '%s%s(%r): %r' % (
            indent_str * indent,
            self.__class__.__name__,
            self.name,
            self.value
        )

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__,
            self.value,
            self.name
        )


class TAG_Byte(BaseTag):
    pass


class TAG_Short(BaseTag):
    pass


class TAG_Int(BaseTag):
    pass


class TAG_Long(BaseTag):
    pass


class TAG_Float(BaseTag):
    pass


class TAG_Double(BaseTag):
    pass


class TAG_Byte_Array(BaseTag):
    def pretty(self, indent=0, indent_str='  '):
        return '%sTAG_Byte_Array(%r): [%d bytes]' % (
            indent_str * indent,
            self.name,
            len(self.value)
        )


class TAG_String(BaseTag):
    pass


class TAG_List(BaseTag, list):
    """
    Keep in mind that a TAG_List is only capable of storing
    tags of the same type.
    """
    def __init__(self, tag_type, value, name=None):
        self.name = name
        self.value = self
        self.extend(value)
        if isinstance(tag_type, int):
            self._type = tag_type
        else:
            self._type = _tags.index(tag_type)

    def pretty(self, indent=0, indent_str='  '):
        t = []
        t.append('%sTAG_List(%r): %d entries' % (
            indent_str * indent,
            self.name,
            len(self.value)
        ))
        t.append('%s{' % (indent_str * indent))
        for v in self.value:
            t.append(v.pretty(indent + 1))
        t.append('%s}' % (indent_str * indent))
        return '\n'.join(t)

    def __repr__(self):
        return '%s(%r entries, %r)' % (
            self.__class__.__name__,
            len(self),
            self.name
        )


class TAG_Compound(BaseTag, dict):
    def __init__(self, value, name=None):
        self.name = name
        self.value = self
        self.update(value)

    def pretty(self, indent=0, indent_str='  '):
        t = []
        t.append('%sTAG_Compound(%r): %d entries' % (
            indent_str * indent,
            self.name,
            len(self.value)
        ))
        t.append('%s{' % (indent_str * indent))
        for v in self.itervalues():
            t.append(v.pretty(indent + 1))
        t.append('%s}' % (indent_str * indent))

        return '\n'.join(t)

    def __repr__(self):
        return '%s(%r entries, %r)' % (
            self.__class__.__name__,
            len(self),
            self.name
        )

    def __setitem__(self, key, value):
        """
        Sets the TAG_*'s name if it isn't already set to that of the key
        it's being assigned to. This results in cleaner code, as the name
        does not need to be specified twice.
        """
        if value.name is None:
            value.name = key
        super(TAG_Compound, self).__setitem__(key, value)

    def update(self, *args, **kwargs):
        """See `__setitem__`."""
        super(TAG_Compound, self).update(*args, **kwargs)
        for key, item in self.items():
            if item.name is None:
                item.name = key


class TAG_Int_Array(BaseTag):
    def pretty(self, indent=0, indent_str='  '):
        return '%sTAG_Int_Array(%r): [%d integers]' % (
            indent_str * indent,
            self.name,
            len(self.value)
        )

_tags = (
    None,
    TAG_Byte,
    TAG_Short,
    TAG_Int,
    TAG_Long,
    TAG_Float,
    TAG_Double,
    TAG_Byte_Array,
    TAG_String,
    TAG_List,
    TAG_Compound,
    TAG_Int_Array
)


class NBTFile(TAG_Compound):
    class Compression(object):
        # NONE is simply for the sake of completeness.
        NONE = 10
        # Use Gzip compression when reading or writing.
        GZIP = 20

    def __init__(self, io=None, name=None, value=None, compression=None,
        little_endian=False):
        """
        Loads or creates a new NBT file. `io` may be either a file-like object
        providing `read()`, or a path to a file.
        """
        # No file or path given, so we're creating a new NBTFile.
        if io is None:
            super(NBTFile, self).__init__(value if value else {}, name)
            return

        if compression is None or compression == NBTFile.Compression.NONE:
            final_io = io
        elif compression == NBTFile.Compression.GZIP:
            final_io = gzip.GzipFile(fileobj=io, mode='rb')
        else:
            raise ValueError('Unrecognized compression scheme.')

        if little_endian:
            read = lambda fmt, size: unpack('<' + fmt, final_io.read(size))
        else:
            read = lambda fmt, size: unpack('>' + fmt, final_io.read(size))

        # All valid NBT files will begin with 0x0A, which is a TAG_Compound.
        if read('b', 1)[0] != 0x0A:
            raise IOError('NBTFile does not begin with 0x0A.')

        tmp = TAG_Compound.read(read)
        super(NBTFile, self).__init__(tmp, tmp.name)

    def save(self, io, compressed=True, little_endian=False):
        """
        Saves the `NBTFile()` to `io` which is either a path or a file-like
        object providing `write()`.
        """
        f = open(io, 'wb') if isinstance(io, basestring) else io
        g = gzip.GzipFile(fileobj=f, mode='wb') if compressed else f

        if little_endian:
            w = lambda fmt, *args: g.write(pack('<' + fmt, *args))
        else:
            w = lambda fmt, *args: g.write(pack('>' + fmt, *args))

        self.write(w)

        # Close io only if we're the one who opened it.
        if isinstance(io, basestring):
            if compressed:
                g.close()
            f.close()
