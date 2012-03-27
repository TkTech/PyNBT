import unittest
from opennbt import NBTFile, TAG_String


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

if __name__ == '__main__':
    unittest.main()
