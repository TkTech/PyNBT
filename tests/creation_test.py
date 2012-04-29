import unittest
from opennbt import *


class CreationTest(unittest.TestCase):
    def setUp(self):
        self.nbt = NBTFile()

    def test_string_key(self):
        """
        Ensure key names are strings.
        """
        with self.assertRaises(TypeError):
            self.nbt[4] = TAG_String('four')

    def test_is_tag(self):
        """
        Ensure compound values are TAG_* subclasses.
        """
        with self.assertRaises(TypeError):
            self.nbt['4'] = 4

    def test_save(self):
        n = self.nbt
        n['byte'] = TAG_Byte(0)
        n['short'] = TAG_Short(1)
        n['int'] = TAG_Int(2)
        n['float'] = TAG_Float(3.)
        n['double'] = TAG_Double(4.)
        n['string'] = TAG_String('Testing')
        self.nbt.save('__test__.nbt')

if __name__ == '__main__':
    unittest.main()
