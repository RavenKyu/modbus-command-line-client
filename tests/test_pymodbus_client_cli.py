import unittest
from tabulate import tabulate
from modbusclc import chunks
from modbusclc import space
from modbusclc import get_data_with_template
from modbusclc import get_default_template
from modbusclc import make_record

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
        expect = [['B64_STRING', 40001, '556e 6974 3233 2d41', 'Unit23-A',
                   'text label'],
                  ['B16_UINT', 40005, 'fefe', 65278, '16 bit unsigned integer'],
                  ['B16_INT', 40006, 'fc19', -999, '16 bit integer'],
                  ['B32_UINT', 40007, 'ffff ffff', 4294967295,
                   '32 bit unsigned integer'],
                  ['B32_INT', 40009, 'ffff ffff', -1, '32 bit integer'],
                  ['B32_FLOAT', 40011, '437e e2c6', 254.88583374023438,
                   '32 bit float'],
                  ['B32_FLOAT', 40013, '420a c326', 34.690574645996094,
                   '32 bit float'],
                  ['B32_FLOAT', 40015, '427d 7aeb', 63.37003707885742,
                   '32 bit float'],
                  ['B32_FLOAT', 40017, '4107 0e38', 8.440971374511719,
                   '32 bit float']]
        data = get_data_with_template(DATA[1:], TEMPLATE)
        self.assertListEqual(data, expect)

    def test0510_get_template_with_no_template(self):
        expect = [['B16_UINT', 40001, '556e', 21870, '-'],
                  ['B16_UINT', 40002, '6974', 26996, '-'],
                  ['B16_UINT', 40003, '3233', 12851, '-'],
                  ['B16_UINT', 40004, '2d41', 11585, '-'],
                  ['B16_UINT', 40005, 'fefe', 65278, '-'],
                  ['B16_UINT', 40006, 'fc19', 64537, '-'],
                  ['B16_UINT', 40007, 'ffff', 65535, '-'],
                  ['B16_UINT', 40008, 'ffff', 65535, '-'],
                  ['B16_UINT', 40009, 'ffff', 65535, '-'],
                  ['B16_UINT', 40010, 'ffff', 65535, '-'],
                  ['B16_UINT', 40011, '437e', 17278, '-'],
                  ['B16_UINT', 40012, 'e2c6', 58054, '-'],
                  ['B16_UINT', 40013, '420a', 16906, '-'],
                  ['B16_UINT', 40014, 'c326', 49958, '-'],
                  ['B16_UINT', 40015, '427d', 17021, '-'],
                  ['B16_UINT', 40016, '7aeb', 31467, '-'],
                  ['B16_UINT', 40017, '4107', 16647, '-'],
                  ['B16_UINT', 40018, '0e38', 3640, '-'],
                  ['B16_UINT', 40019, '0000', 0, '-'],
                  ['B16_UINT', 40020, '0007', 7, '-']]

        data = get_data_with_template(DATA[1:], None)

        self.assertListEqual(data, expect)

    def test600_get_default_template(self):
        data = b'\xfc\x19\xff\xff'
        register_size = 2
        expect = [{'note': '-', 'data_type': 'B16_UINT'},
                  {'note': '-', 'data_type': 'B16_UINT'}]
        result = get_default_template(data, register_size)
        self.assertEqual(expect, result)

    def test700_make_record(self):
        index = 13
        data = [('556e', 1), ('6974', 2), ('3233', 3), ('2d41', 4), ('fefe', 5),
                ('fc19', 6), ('ffff', 7), ('ffff', 8), ('ffff', 9),
                ('ffff', 10), ('437e', 11), ('e2c6', 12), ('420a', 13),
                ('c326', 14), ('427d', 15), ('7aeb', 16), ('4107', 17),
                ('0e38', 18), ('0000', 19), ('0007', 20)]
        template = {'note': '-', 'data_type': 'B16_UINT'}
        first_register = 40000
        register_size = 2
        expect = ['B16_UINT', 40014, 'c326', 49958, '-']
        result = make_record(index, data, template, first_register,
                             register_size)
        self.assertListEqual(expect, result)

    def test_something(self):
        expect = """data type      reg  bytes                value               note
-----------  -----  -------------------  ------------------  -----------------------
B64_STRING   40001  556e 6974 3233 2d41  Unit23-A            text label
B16_UINT     40005  fefe                 65278               16 bit unsigned integer
B16_INT      40006  fc19                 -999                16 bit integer
B32_UINT     40007  ffff ffff            4294967295          32 bit unsigned integer
B32_INT      40009  ffff ffff            -1                  32 bit integer
B32_FLOAT    40011  437e e2c6            254.88583374023438  32 bit float
B32_FLOAT    40013  420a c326            34.690574645996094  32 bit float
B32_FLOAT    40015  427d 7aeb            63.37003707885742   32 bit float
B32_FLOAT    40017  4107 0e38            8.440971374511719   32 bit float"""
        data = get_data_with_template(DATA[1:], TEMPLATE)
        header = ["data type", "reg", "bytes", "value", "note"]
        data.insert(0, header)
        result = tabulate(data, headers="firstrow")
        self.assertEqual(result, expect)


if __name__ == '__main__':
    unittest.main()
