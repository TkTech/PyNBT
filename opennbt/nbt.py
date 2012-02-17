#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
A tiny library for reading & writing NBT files, used for the game
'Minecraft' by Markus Petersson.
"""
import gzip
import struct


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
        length, = rd('>h')
        return rd('>%ds' % length)[0]

    @staticmethod
    def write_utf8(wt, value):
        """
        Writes a length-prefixed UTF8 string.
        """
        wt('>h%ss' % len(value), len(value), value)

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
            wt('>b', _tags.index(self.__class__))
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
    STRUCT_FMT = '>b'


class TAG_Short(BaseTag):
    STRUCT_FMT = '>h'


class TAG_Int(BaseTag):
    STRUCT_FMT = '>i'


class TAG_Long(BaseTag):
    STRUCT_FMT = '>q'


class TAG_Float(BaseTag):
    STRUCT_FMT = '>f'


class TAG_Double(BaseTag):
    STRUCT_FMT = '>d'


class TAG_Byte_Array(BaseTag):
    @classmethod
    def read(cls, rd, has_name=True):
        name = BaseTag.read_utf8(rd) if has_name else None
        length, = rd('>i')
        return cls(name, rd('>%ss' % length)[0])

    def write(self, wt):
        if self.name is not None:
            wt('>b', 7)
            BaseTag.write_utf8(wt, self.name)

        wt('>i%ss' % len(self.value), len(self.value), self.value)

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
            wt('>b', 8)
            BaseTag.write_utf8(wt, self.name)
        wt('>h%ss' % len(self.value), len(self.value), self.value)


class TAG_List(BaseTag):
    """
    Keep in mind that a TAG_List is only capable of storing
    tags of the same type.
    """
    def __init__(self, name, tag_type, value):
        BaseTag.__init__(name, value)
        self._type = tag_type

    @classmethod
    def read(cls, rd, has_name=True):
        name = BaseTag.read_utf8(rd) if has_name else None
        tag_type, length = rd('>bi')
        real_type = _tags[tag_type]
        return TAG_List(
            name,
            tag_type,
            [real_type.read(rd, has_name=False) for x in xrange(0, length)]
        )

    def write(self, wt):
        if self.name is not None:
            wt('>b', 9)
            BaseTag.write_utf8(wt, self.name)

        wt('>bi', self._type, len(self.value))
        for item in self.value:
            item.write(wt)

    def pretty(self, indent=0, indent_str='  '):
        t = []
        t.append('%sTAG_List(%r): %d entires' % (
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
            tag, = rd('>b')
            # EndTag
            if tag == 0:
                break

            tmp = _tags[tag].read(rd)
            final[tmp.name] = tmp

        return cls(name, final)

    def write(self, wt):
        if self.name is not None:
            wt('>b', 10)
            BaseTag.write_utf8(wt, self.name)

        for v in self.value.itervalues():
            v.write(wt)

        # EndTag
        wt('>b', 0)

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
    TAG_Compound
)


class NBTFile(TAG_Compound):
    def __init__(self, io=None, root_name=None, compressed=True):
        if io is None:
            # We have no pre-existing NBT file.
            if root_name is None:
                raise ValueError(
                    'root_name must not be none if no file is provided!'
                )
            super(NBTFile, self).__init__(root_name, {})
            return

        fin = open(io, 'rb') if isinstance(io, basestring) else io
        src = gzip.GzipFile(fileobj=fin, mode='rb') if compressed else fin

        def read(fmt):
            return struct.unpack(fmt, src.read(struct.calcsize(fmt)))

        # Discard the leading tag prefx, we know it's a compound.
        read('>b')
        tmp = TAG_Compound.read(read)

        self._name = tmp.name
        self._value = tmp.value

        if compressed:
            src.close()

        if isinstance(io, basestring):
            fin.close()

    def save(self, io, compressed=True):
        fout = open(io, 'wb') if isinstance(io, basestring) else io
        src = gzip.GzipFile(fileobj=fout, mode='wb') if compressed else fout

        def write(fmt, *args):
            src.write(struct.pack(fmt, *args))

        self.write(write)

        if compressed:
            src.close()

        if isinstance(io, basestring):
            fout.close()
