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

### Reading

Reading is simple, and will accept any file-like object providing `read()` or a path to a file. If a path is provided, OpenNBT may open it multiple times to figure out the format. If you provide a file-like object, you need to specify the details yourself.

Simply pretty-printing the file created from the example under writing:

```python
from opennbt import NBTFile

nbt = NBTFile('out.nbt')
print(nbt.pretty())
```

This produces the output:

```
TAG_Compound(''): 2 entries
{
  TAG_Long('long_test'): 104005
  TAG_List('list_test'): 3 entries
  {
    TAG_String(None): 'Timmy'
    TAG_String(None): 'Billy'
    TAG_String(None): 'Sally'
  }
}
```

Every tag exposes a minimum of two fields, `.name` and `.value`. Every type's value maps to a plain Python type, such as a `dict()` for `TAG_Compound` and a list for `TAG_List`. Every tag
also provides complete `__repr__` methods for printing. This makes traversal very simple and familiar to existing Python developers.

```
nbt = NBTFile('out.nbt')
for name, tag in nbt.value.items():
    print name, tag

if 'list_test' in nbt.value:
    for tag in nbt.value['list_test'].value:
        print tag
```