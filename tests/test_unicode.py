from io import BytesIO

from pynbt import NBTFile, TAG_String


def test_mutf8():
    """Strings in NBT are MUTF-8, not UTF-8."""
    nbt = NBTFile(name='')

    nbt['mutf_8'] = TAG_String('\u2764')

    with BytesIO() as out:
        nbt.save(out)
        assert out.getvalue() == (
            # Root Compound
            b'\x0A'
            # Length of root name (empty)
            b'\x00\x00'
            # TAG_String
            b'\x08'
            # String's name and its length
            b'\x00\x06mutf_8'
            # String's length.
            b'\x00\x03'
            # String's value.
            b'\xe2\x9d\xa4'
            # TAG_End
            b'\x00'
        )
