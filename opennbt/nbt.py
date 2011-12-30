#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Copyright (C) 2011 Tyler Kennedy <tk@tkte.ch>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import struct
import gzip


class Tag(object):
    """
    Superclass for all tags.
    """
    def __init__(self, name, value):
        self._name = name
        self._value = value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__,
            self._name,
            self._value
        )

    def pretty(self, indent=0):
        return '%s%s(%r): %r' % (
            ('  ' * indent),
            self.__class__.__name__,
            self.name,
            self.value
        )


class TAG_Byte(Tag):
    pass


class TAG_Short(Tag):
    pass


class TAG_Int(Tag):
    pass


class TAG_Long(Tag):
    pass


class TAG_FLoat(Tag):
    def __init__(self, name, value):
        # Much easier then doing this ourself; not a simple type!
        try:
            struct.pack('>f', value)
        except OverflowError, e:
            raise ValueError(e)
        super(TAG_FLoat, self).__init__(name, value)


class TAG_Double(Tag):
    def __init__(self, name, value):
        # Much easier then doing this ourself; not a simple type!
        try:
            struct.pack('>d', value)
        except OverflowError, e:
            raise ValueError(e)
        super(TAG_Double, self).__init__(name, value)


class TAG_Byte_Array(Tag):
    def __repr__(self):
        return '<TAG_Byte_Array(%r, %d bytes)>' % (self.name, len(self.value))

    def pretty(self, indent=0):
        return '%sTAG_Byte_Array(%r): [%r bytes]' % (
            ('  ' * indent),
            self.name,
            len(self.value)
        )


class TAG_String(Tag):
    pass


class TAG_List(Tag):
    def __init__(self, name, tagtype, values):
        if len(values) > 2147483647:
            raise ValueError('Length of list too large!(>32767)')

        self._type = tagtype
        super(TAG_List, self).__init__(name, values)

    def __repr__(self):
        return '<TAG_List(%r, %r, %d items)>' % (
            self.name,
            self._type.__class__.__name__,
            len(self.value)
        )

    def pretty(self, indent=0):
        t = []
        t.append('%sTAG_List(%r): %d entries' % (
            ('  ' * indent),
            self.name,
            len(self.value)
        ))
        t.append('%s{' % ('  ' * indent))
        for v in self.value:
            t.append(v.pretty(indent + 1))
        t.append('%s}' % ('  ' * indent))
        return '\n'.join(t)


class TAG_Compund(Tag):
    def pretty(self, indent=0):
        t = []
        t.append('%sTAG_Compound(%r): %d entries' % (
            ('  ' * indent),
            self.name,
            len(self.value)
        ))
        t.append('%s{' % ('  ' * indent))
        for v in self.value.itervalues():
            t.append(v.pretty(indent + 1))
        t.append('%s}' % ('  ' * indent))

        return '\n'.join(t)


class NBTFile(TAG_Compund):
    def __init__(self, io=None, root_name=None, compressed=True):
        if io is None:
            # We have no pre-existing NBT file.
            if root_name is None:
                raise ValueError(
                    'root_name must not be None if no file is provided!'
                )
            super(TAG_Compund, self).__init__(root_name, {})
            return

        fin = open(io, 'rb') if isinstance(io, basestring) else io
        src = gzip.GzipFile(fileobj=fin, mode='rb') if compressed else fin

        def read(fmt):
            return struct.unpack(fmt, src.read(struct.calcsize(fmt)))

        # Discard the leading tag prefx, we know it's a compound.
        read('>b')
        tmp = self._read_compound(read)

        self._name = tmp.name
        self._value = tmp.value

        if compressed:
            src.close()

        if isinstance(io, basestring):
            fin.close()

    def _read_utf(self, rd):
        length = rd('>h')[0]
        return rd('>%ss' % length)[0]

    def _read_byte(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        return TAG_Byte(name, rd('>b')[0])

    def _read_short(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        return TAG_Short(name, rd('>h')[0])

    def _read_int(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        return TAG_Int(name, rd('>i')[0])

    def _read_long(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        return TAG_Long(name, rd('>q')[0])

    def _read_float(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        return TAG_FLoat(name, rd('>f')[0])

    def _read_double(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        return TAG_Double(name, rd('>d')[0])

    def _read_bytearray(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        length = rd('>i')[0]
        return TAG_Byte_Array(name, rd('>%ss' % length)[0])

    def _read_string(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        return TAG_String(name, self._read_utf(rd))

    def _read_list(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        type_, length = rd('>bi')
        reader, real_type = self._readers(type_)
        return TAG_List(name, real_type,
            [reader(rd, no_name=True) for x in xrange(0, length)]
        )

    def _readers(self, i):
        return [
            (),
            (self._read_byte, TAG_Byte),
            (self._read_short, TAG_Short),
            (self._read_int, TAG_Int),
            (self._read_long, TAG_Long),
            (self._read_float, TAG_FLoat),
            (self._read_double, TAG_Double),
            (self._read_bytearray, TAG_Byte_Array),
            (self._read_string, TAG_String),
            (self._read_list, TAG_List),
            (self._read_compound, TAG_Compund)
        ][i]

    def _read_compound(self, rd, no_name=False):
        name = None if no_name else self._read_utf(rd)
        final = {}

        while True:
            tag = rd('>b')[0]
            if tag == 0:
                # EndTag
                break

            tmp = self._readers(tag)[0](rd)
            final[tmp.name] = tmp

        return TAG_Compund(name, final)
