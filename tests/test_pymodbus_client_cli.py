import unittest
from tabulate import tabulate
from modbusclc import chunks
from modbusclc import space
from modbusclc import get_data_with_template


DATA = "28 55 6e 69 74 32 33 2d 41 fe fe fc 19 ff ff ff ff ff ff ff ff 43 7e e2 c6 42 0a c3 26 42 7d 7a eb 41 07 0e 38 00 00 00 07"
DATA = bytes.fromhex(DATA)

TEMPLATE = [
    {'note': 'text label', 'data_type': 'B64_STRING', },
    {'note': '16 bit unsigned integer', 'data_type': 'B16_UINT', },
    {'note': '16 bit integer', 'data_type': 'B16_INT', },
    {'note': '32 bit unsigned integer', 'data_type': 'B32_UINT', },
    {'note': '32 bit integer', 'data_type': 'B32_INT', },
    {'note': '32 bit float', 'data_type': 'B32_FLOAT', },
    {'note': '32 bit float', 'data_type': 'B32_FLOAT', },
    {'note': '32 bit float', 'data_type': 'B32_FLOAT', },
    {'note': '32 bit float', 'data_type': 'B32_FLOAT', },
]


class MyTestCase(unittest.TestCase):
    def test0200_chunks(self):
        data = bytes.fromhex('556e697432332d41fefefc19feff')
        result = chunks(data, (8, 2, 2, 1, 1))
        print(list(result))

    def test0300_space(self):
        data = '556e697432332d41'
        result = space(data, 4)
        print(result)

    def test0400_get_string_data_from_bytes(self):
        pass

    def test0400_get_template(self):
        expect = [
            ['64b sting', 40001, '556e 6974 3233 2d41', b'Unit23-A', 'text label'],
            ['16b uint', 40005, 'fefe', 65278, '16 bit unsigned integer'],
            ['16b int', 40006, 'fc19', -999, '16 bit integer'],
            ['32b uint', 40007, 'ffff ffff', 4294967295,
             '32 bit unsigned integer'],
            ['32b int', 40009, 'ffff ffff', -1, '32 bit integer'],
            ['32b float', 40011, '437e e2c6', 254.88583374023438, '32 bit float'],
            ['32b float', 40013, '420a c326', 34.690574645996094, '32 bit float'],
            ['32b float', 40015, '427d 7aeb', 63.37003707885742, '32 bit float'],
            ['32b float', 40017, '4107 0e38', 8.440971374511719, '32 bit float']]

        data = get_data_with_template(DATA[1:], TEMPLATE)
        self.assertListEqual(data, expect)

    def test0510_get_template_with_no_template(self):
        expect = [['16b uint', 40001, '556e', 21870, '16 bit unsigned integer'],
                  ['16b uint', 40002, '6974', 26996, '16 bit unsigned integer'],
                  ['16b uint', 40003, '3233', 12851, '16 bit unsigned integer'],
                  ['16b uint', 40004, '2d41', 11585, '16 bit unsigned integer'],
                  ['16b uint', 40005, 'fefe', 65278, '16 bit unsigned integer'],
                  ['16b uint', 40006, 'fc19', 64537, '16 bit unsigned integer'],
                  ['16b uint', 40007, 'ffff', 65535, '16 bit unsigned integer'],
                  ['16b uint', 40008, 'ffff', 65535, '16 bit unsigned integer'],
                  ['16b uint', 40009, 'ffff', 65535, '16 bit unsigned integer'],
                  ['16b uint', 40010, 'ffff', 65535, '16 bit unsigned integer'],
                  ['16b uint', 40011, '437e', 17278, '16 bit unsigned integer'],
                  ['16b uint', 40012, 'e2c6', 58054, '16 bit unsigned integer'],
                  ['16b uint', 40013, '420a', 16906, '16 bit unsigned integer'],
                  ['16b uint', 40014, 'c326', 49958, '16 bit unsigned integer'],
                  ['16b uint', 40015, '427d', 17021, '16 bit unsigned integer'],
                  ['16b uint', 40016, '7aeb', 31467, '16 bit unsigned integer'],
                  ['16b uint', 40017, '4107', 16647, '16 bit unsigned integer'],
                  ['16b uint', 40018, '0e38', 3640, '16 bit unsigned integer'],
                  ['16b uint', 40019, '0000', 0, '16 bit unsigned integer'],
                  ['16b uint', 40020, '0007', 7, '16 bit unsigned integer']]

        data = get_data_with_template(DATA[1:], None)
        self.assertListEqual(data, expect)

    def test_something(self):
        expect = """data type      reg  bytes                value               note
-----------  -----  -------------------  ------------------  -----------------------
64b sting    40001  556e 6974 3233 2d41  Unit23-A            text label
16b uint     40005  fefe                 65278               16 bit unsigned integer
16b int      40006  fc19                 -999                16 bit integer
32b uint     40007  ffff ffff            4294967295          32 bit unsigned integer
32b int      40009  ffff ffff            -1                  32 bit integer
32b float    40011  437e e2c6            254.88583374023438  32 bit float
32b float    40013  420a c326            34.690574645996094  32 bit float
32b float    40015  427d 7aeb            63.37003707885742   32 bit float
32b float    40017  4107 0e38            8.440971374511719   32 bit float"""
        data = get_data_with_template(DATA[1:], TEMPLATE)
        header = ["data type", "reg", "bytes", "value", "note"]
        data.insert(0, header)
        result = tabulate(data, headers="firstrow")
        self.assertEqual(result, expect)



if __name__ == '__main__':
    unittest.main()
