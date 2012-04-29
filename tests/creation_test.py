import unittest
from opennbt import *


class CreationTest(unittest.TestCase):
    def setUp(self):
        self.nbt = NBTFile()

    def test_save(self):
        n = self.nbt
        n['byte'] = TAG_Byte(0)
        n['short'] = TAG_Short(1)
        n['int'] = TAG_Int(2)
        n['float'] = TAG_Float(3.)
        n['double'] = TAG_Double(4.)
        n['string'] = TAG_String('Testing')
        n['int_array'] = TAG_Int_Array([45, 5, 6])
        n['byte_array'] = TAG_Byte_Array('four')
        self.nbt.save('__test__.nbt')

if __name__ == '__main__':
    unittest.main()
