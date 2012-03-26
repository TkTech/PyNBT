#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
A tiny library for reading & writing NBT files, used for the game
'Minecraft' by Markus Petersson.
"""
import gzip
import struct

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from .helpers import is_pocket


class BaseTag(object):
    """
    Implements methods common to all NBT tags.
    """
    def __init__(self, name, value):
        self._name = name
        self._value = value

    @property
    def value(self):
        return self._value

    @property
    def name(self):
        return self._name

    @staticmethod
    def read_utf8(rd):
        """
        Reads in a length-prefixed UTF8 string.
        """
        length, = rd('h')
        return rd('%ds' % length)[0]

    @staticmethod
    def write_utf8(wt, value):
        """
        Writes a length-prefixed UTF8 string.
        """
        wt('h%ss' % len(value), len(value), value)

    @classmethod
    def read(cls, rd, has_name=True):
        """
        Read the tag in using the reader `rd`.
        If `has_name` is `False`, skip reading the tag name.
        """
        if not hasattr(cls, 'STRUCT_FMT'):
            raise NotImplementedError()

        name = BaseTag.read_utf8(rd) if has_name else None
        value, = rd(cls.STRUCT_FMT)

        return cls(name, value)

    def write(self, wt):
        if not hasattr(self, 'STRUCT_FMT'):
            raise NotImplementedError()
        if self.name is not None:
            wt('b', _tags.index(self.__class__))
            BaseTag.write_utf8(wt, self.name)

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
            self.name,
            self.value
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
    @classmethod
    def read(cls, rd, has_name=True):
        name = BaseTag.read_utf8(rd) if has_name else None
        length, = rd('i')
        return cls(name, rd('%ss' % length)[0])

    def write(self, wt):
        if self.name is not None:
            wt('b', 7)
            BaseTag.write_utf8(wt, self.name)

        wt('i%ss' % len(self.value), len(self.value), self.value)

    def pretty(self, indent=0, indent_str='  '):
        return '%sTAG_Byte_Array(%r): [%d bytes]' % (
            indent_str * indent,
            self.name,
            len(self.value)
        )


class TAG_String(BaseTag):
    @classmethod
    def read(cls, rd, has_name=True):
        name = BaseTag.read_utf8(rd) if has_name else None
        value = BaseTag.read_utf8(rd)
        return cls(name, value)

    def write(self, wt):
        if self.name is not None:
            wt('b', 8)
            BaseTag.write_utf8(wt, self.name)
        wt('h%ss' % len(self.value), len(self.value), self.value)


class TAG_List(BaseTag):
    """
    Keep in mind that a TAG_List is only capable of storing
    tags of the same type.
    """
    def __init__(self, name, tag_type, value):
        BaseTag.__init__(self, name, value)
        if isinstance(tag_type, int):
            self._type = tag_type
        else:
            self._type = _tags.index(tag_type)

    @classmethod
    def read(cls, rd, has_name=True):
        name = BaseTag.read_utf8(rd) if has_name else None
        tag_type, length = rd('bi')
        real_type = _tags[tag_type]
        return TAG_List(
            name,
            tag_type,
            [real_type.read(rd, has_name=False) for x in xrange(0, length)]
        )

    def write(self, wt):
        if self.name is not None:
            wt('b', 9)
            BaseTag.write_utf8(wt, self.name)

        wt('bi', self._type, len(self.value))
        for item in self.value:
            item.write(wt)

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


class TAG_Compound(BaseTag):
    @classmethod
    def read(cls, rd, has_name=True):
        name = BaseTag.read_utf8(rd) if has_name else None
        final = {}

        while True:
            tag, = rd('b')
            # EndTag
            if tag == 0:
                break

            tmp = _tags[tag].read(rd)
            final[tmp.name] = tmp

        return cls(name, final)

    def write(self, wt):
        if self.name is not None:
            wt('b', 10)
            BaseTag.write_utf8(wt, self.name)

        for v in self.value.itervalues():
            v.write(wt)

        # EndTag
        wt('b', 0)

    def pretty(self, indent=0, indent_str='  '):
        t = []
        t.append('%sTAG_Compound(%r): %d entries' % (
            indent_str * indent,
            self.name,
            len(self.value)
        ))
        t.append('%s{' % (indent_str * indent))
        for v in self.value.itervalues():
            t.append(v.pretty(indent + 1))
        t.append('%s}' % (indent_str * indent))

        return '\n'.join(t)


class TAG_Int_Array(BaseTag):
    @classmethod
    def read(cls, rd, has_name=True):
        name = BaseTag.read_utf8(rd) if has_name else None
        length, = rd('i')
        return cls(name, rd('%si' % length))

    def write(self, wt):
        if self.name is not None:
            wt('b', 11)
            BaseTag.write_utf8(wt, self.name)

        wt('i%si' % len(self.value), len(self.value), self.value)

    def pretty(self, indent=0, indent_str='  '):
        return '%sTAG_Int_Array(%r): [%d bytes]' % (
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
    def __init__(self, io=None, root_name=None, compressed=True,
            little_endian=False, pocket_name=None, value=None):
        """
        Loads or creates a new NBT file. `io` may be either a file-like object
        providing `read()`, or a path to a file.

        If `io` is a path, then `NBTFile()` will attempt to automatically
        detect and handle the pocket minecraft headers, which it cannot
        do otherwise. In this case, you must pass either "entities.dat" or
        "level.dat" to `pocket_name`, or handle the headers yourself.
        """
        self._pocket_type = None
        self._little = (little_endian or self._pocket_type)

        if io is None:
            # We have no pre-existing NBT file.
            if root_name is None:
                raise ValueError(
                    'root_name must not be none if no file is provided!'
                )
            super(NBTFile, self).__init__(root_name, value if value else {})
            return

        if isinstance(io, basestring):
            # We've got a file path.
            self._pocket_type = is_pocket(io, compressed=compressed)

        fin = open(io, 'rb') if isinstance(io, basestring) else io
        src = gzip.GzipFile(fileobj=fin, mode='rb') if compressed else fin

        def read(fmt):
            fmt = '<%s' % fmt if self._little else '>%s' % fmt
            return struct.unpack(fmt, src.read(struct.calcsize(fmt)))

        # Discard the pocket format headers.
        if self._pocket_type == "entities.dat":
            read('12b')
        elif self._pocket_type == "level.dat":
            read('8b')

        # Discard the compound tag.
        read('b')
        tmp = TAG_Compound.read(read)

        self._name = tmp.name
        self._value = tmp.value

        if compressed:
            src.close()

        if isinstance(io, basestring):
            fin.close()

    def save(self, io, compressed=True, little_endian=None,
            force_standard=False):
        """
        Saves the `NBTFile()` to `io` which is either a path or a file-like
        object providing `write()`.

        By default `save()` tries to produce a file as close to the original
        as possible.

        Endianess can be forced by passing `True` or `False` to
        `little_endian`.

        Files loaded as portable minecraft files can be saved as regular NBT
        files by passing `True` to `force_standard`.
        """
        fout = open(io, 'wb') if isinstance(io, basestring) else io
        src = gzip.GzipFile(fileobj=fout, mode='wb') if compressed else fout

        little = self._little if little_endian is None else little_endian

        temporary = StringIO()

        def write(fmt, *args):
            fmt = '<%s' % fmt if little else '>%s' % fmt
            temporary.write(struct.pack(fmt, *args))

        def real_write(fmt, *args):
            fmt = '<%s' % fmt if little else '>%s' % fmt
            src.write(struct.pack(fmt, *args))

        self.write(write)

        buff = temporary.getvalue()
        temporary.close()

        if self._pocket_type and not force_standard:
            if self._pocket_type == "entities.dat":
                real_write('bbbbII',
                    0x45,  # 'E'
                    0x4E,  # 'N'
                    0x54,  # 'T'
                    0x00,  # '\x00'
                    0x01,  # Version
                    len(buff)  # Content length
                )
            elif self._pocket_type == "level.dat":
                real_write('II',
                    0x02,  # Version,
                    len(buff)  # Content length
                )

        src.write(buff)

        if compressed:
            src.close()

        if isinstance(io, basestring):
            fout.close()
