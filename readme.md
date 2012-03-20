# OpenNBT

OpenNBT is a tiny, liberally licenced (MIT) NBT library.
It supports reading and writing compressed, uncompressed, big endian, little endian, or pocket edition (v2) NBT files transparently. It also includes helpers for region files and pocket detection.

## Scripts

The OpenNBT package installs two scripts, `debug-nbt` and `debug-region`. These scripts can be used to pretty-print the NBT contents of plain NBT files and region files.

Example:

```
debug-nbt level.dat
TAG_Compound(''): 1 entries
{
  TAG_Compound('Data'): 18 entries
  {
  ...
  }
}
```

## Using the Library
Using the library in your own programs is simple. By default, OpenNBT will try to save opened NBT files in the same format they were loaded from, however this behaviour is
easily changed.


### Reading

Reading is simple, and will accept any file-like object providing `read()` or a path to a file. If a path is provided, OpenNBT may open it multiple times to figure out the format. If you provide a file-like object, you need to specify the details yourself.

```python
from opennbt import NBTFile

nbt = NBTFile('C:\level.dat')
print(nbt.pretty())
```

### Writing

When writing NBT files with OpenNBT, every tag should be treated as if it was immutable. This is to simplify future changes to both the library and the format.
Developer wise, building NBT files is less convienient, but very explicit. This is done because of the differences in basic types between NBT and python.

```python
from opennbt import NBTFile, TAG_Long, TAG_List, TAG_String

structure = {
    'long_test': TAG_Long('long_test', 104005),
    'list_test': TAG_List('list_test', TAG_String, [
        TAG_String(None, 'Timmy'),
        TAG_String(None, 'Billy'),
        TAG_String(None, 'Sally')
    ])
}

nbt = NBTFile(root_name='', value=structure)
nbt.save('out.nbt')
```