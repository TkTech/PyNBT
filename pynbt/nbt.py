#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
A tiny library for reading & writing NBT files, used for the game
'Minecraft' by Markus Petersson.
"""
import gzip
import struct


def _read_utf8(rd):
    length, = rd('h')
    return rd('%ds' % length)[0]


def _write_utf8(wt, value):
    l = len(value)
    wt('h%ss' % l, l, value)


class BaseTag(object):
    def __init__(self, value, name=None):
        self.name = name
        self.value = value

    @classmethod
    def read(cls, rd, has_name=True):
        """
        Read the tag in using the reader `rd`.
        If `has_name` is `False`, skip reading the tag name.
        """
        name = _read_utf8(rd) if has_name else None
        # Handle TAG_Compound as a complex type.
        if cls is TAG_Compound:
            final = {}
            while True:
                tag, = rd('b')
                # EndTag
                if tag == 0:
                    break

                tmp = _tags[tag].read(rd)
                final[tmp.name] = tmp
            return cls(final, name)
        # Handle TAG_List as a complex type.
        elif cls is TAG_List:
            tag_type, length = rd('bi')
            real_type = _tags[tag_type]
            return cls(
                tag_type,
                [real_type.read(rd, has_name=False) for x in range(0, length)],
                name
            )
        # Handle TAG_String as a complex type.
        elif cls is TAG_String:
            value = _read_utf8(rd)
            return cls(value, name)
        # Handle TAG_Byte_Array as a complex type.
        elif cls is TAG_Byte_Array:
            length, = rd('i')
            return cls(rd('%ss' % length)[0], name)
        # Handle TAG_Int_Array as a complex type.
        elif cls is TAG_Int_Array:
            length, = rd('i')
            return cls(rd('%si' % length), name)
        else:
            return cls(rd(cls.STRUCT_FMT)[0], name)

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
    STRUCT_FMT = 'b'


class TAG_Short(BaseTag):
    STRUCT_FMT = 'h'


class TAG_Int(BaseTag):
    STRUCT_FMT = 'i'


class TAG_Long(BaseTag):
    STRUCT_FMT = 'q'


class TAG_Float(BaseTag):
    STRUCT_FMT = 'f'


class TAG_Double(BaseTag):
    STRUCT_FMT = 'd'


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
    def __init__(self, io=None, name='', compressed=True, little_endian=False,
            value=None):
        """
        Loads or creates a new NBT file. `io` may be either a file-like object
        providing `read()`, or a path to a file.
        """
        # No file or path given, so we're creating a new NBTFile.
        if io is None:
            super(NBTFile, self).__init__(value if value else {}, name)
            return

        f = open(io, 'rb') if isinstance(io, basestring) else io
        g = gzip.GzipFile(fileobj=f, mode='rb') if compressed else f

        if little_endian:
            x = lambda f: struct.unpack('<' + f,
                g.read(struct.calcsize('<' + f)))
        else:
            x = lambda f: struct.unpack('>' + f,
                g.read(struct.calcsize('>' + f)))

        # We skip the first byte as it will always be a TAG_Compound
        # if this is a valid NBTFile.
        if x('b')[0] != 0x0A:
            raise IOError('Not a valid NBT file.')

        tmp = TAG_Compound.read(x)
        super(NBTFile, self).__init__(tmp, tmp.name)

        # Close io only if we're the one who opened it.
        if isinstance(io, basestring):
            # This will not close the underlying fileobj.
            if compressed:
                g.close()
            f.close()

    def save(self, io, compressed=True, little_endian=False):
        """
        Saves the `NBTFile()` to `io` which is either a path or a file-like
        object providing `write()`.
        """
        f = open(io, 'wb') if isinstance(io, basestring) else io
        g = gzip.GzipFile(fileobj=f, mode='wb') if compressed else f

        if little_endian:
            w = lambda f, *args: g.write(struct.pack('<' + f, *args))
        else:
            w = lambda f, *args: g.write(struct.pack('>' + f, *args))

        self.write(w)

        # Close io only if we're the one who opened it.
        if isinstance(io, basestring):
            if compressed:
                g.close()
            f.close()
