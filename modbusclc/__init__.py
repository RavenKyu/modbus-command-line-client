import yaml
import socket
import enum
import argparse
import struct
import itertools
import datetime
from tabulate import tabulate
from pymodbus.pdu import ModbusRequest, ModbusResponse, ModbusExceptions
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.compat import int2byte


################################################################################
def get_template(name):
    if not name:
        return None
    try:
        with open('templates.yml', 'r') as f:
            return yaml.safe_load(f)[name]
    except Exception as e:
        print(e)
        return None


################################################################################
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


################################################################################
def chunks(lst, size_list: (list, tuple), register_size=2):
    """

    :param lst: b'\xfc\x19\xff\xff\xff\xfe'
    :param size_list: (2, 2, 1, 1)
    :param register_size: 2 (16bit)
    :return: [('fc19', 1), ('ffff', 2), ('ff', 3), ('fe', 3)]

    """
    index = 0
    register = 1
    for i in size_list:
        hex_value = lst[index:index + i].hex()
        yield hex_value, int(register)
        register += i / register_size
        index += i


################################################################################
def space(string, length):
    """

    :param string: '556e697432332d41'
    :param length: 4
    :return: 556e 6974 3233 2d41
    """
    return ' '.join(string[i:i + length] for i in range(0, len(string), length))


################################################################################
def get_data_with_template(data: bytes, template, register_size=2,
                           first_register=40000):
    if not template:
        data_size = int(len(data) / register_size)
        template = itertools.repeat(
            {'note': '16 bit unsigned integer', 'data_type': 'B16_UINT', },
            data_size)
        template = list(template)

    n = [DataType[x['data_type']].value['length'] for x in template]
    data = list(chunks(data, n))

    result = list()
    for i, t in enumerate(template):
        record = list()
        dt = DataType[t['data_type'].upper()]
        dt_v = dt.value

        fmt = dt_v['format']

        record.append(dt_v['name'])
        record.append(first_register + int(data[i][1]))
        record.append(space(data[i][0], register_size * 2))
        d = struct.unpack(fmt, bytes.fromhex(data[i][0]))
        if dt in (DataType.B8_STRING, DataType.B16_STRING, DataType.B32_STRING,
                  DataType.B64_STRING):
            d = b''.join(d)
        elif dt in (DataType.BIT8, ):
            d = f'{d[0]:07b}'
        else:
            d = d[0]
        record.append(d)
        record.append(t['note'])
        result.append(record)
    return result


################################################################################
class DataType(enum.Enum):
    B8_UINT = {'name': '8b uint', 'length': 1, 'format': '>B'}
    B8_INT = {'name': '8b int', 'length': 1, 'format': '>b'}
    BIT8 = {'name': '8 bits', 'length': 1, 'format': '>B'}

    B16_UINT = {'name': '16b uint', 'length': 2, 'format': '>H'}
    B16_INT = {'name': '16b int', 'length': 2, 'format': '>h'}
    B32_UINT = {'name': '32b uint', 'length': 4, 'format': '>I'}
    B32_INT = {'name': '32b int', 'length': 4, 'format': '>i'}

    B16_FLOAT = {'name': '16b float', 'length': 2, 'format': '>e'}
    B32_FLOAT = {'name': '32b float', 'length': 4, 'format': '>f'}
    B64_FLOAT = {'name': '64b float', 'length': 8, 'format': '>d'}

    B8_STRING = {'name': '8b sting', 'length': 1, 'format': '>c'}
    B16_STRING = {'name': '16b sting', 'length': 2, 'format': '>cc'}
    B32_STRING = {'name': '32b sting', 'length': 4, 'format': '>cccc'}
    B64_STRING = {'name': '64b sting', 'length': 8, 'format': '>cccccccc'}


################################################################################
class CustomModbusResponse(ModbusResponse):
    function_code = 0x03
    _rtu_byte_count_pos = 2

    def __init__(self, values=None, **kwargs):
        ModbusResponse.__init__(self, **kwargs)
        self.values = values or ''

    def encode(self):
        """ Encodes response pdu

        :returns: The encoded packet message
        """
        result = int2byte(len(self.values) * 2)
        for register in self.values:
            result += struct.pack('>H', register)
        return result

    def decode(self, data):
        """ Decodes response pdu

        :param data: The packet data to decode
        """
        self.values = data
        return data


################################################################################
class CustomModbusRequest(ModbusRequest):
    function_code = 0x3
    _rtu_frame_size = 8

    def __init__(self, address=None, count=2, **kwargs):
        ModbusRequest.__init__(self, **kwargs)
        self.address = address
        self.count = count

    def encode(self):
        return struct.pack('>HH', self.address, self.count)

    def decode(self, data):
        self.address, self.count = struct.unpack('>h', data)

    def execute(self, context):
        if not (1 <= self.count <= 0x7d0):
            return self.doException(ModbusExceptions.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(ModbusExceptions.IllegalAddress)
        values = context.getValues(self.function_code, self.address,
                                   self.count)
        return CustomModbusResponse(values)


################################################################################
def request_response_messages(command, data: bytes, address=''):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{now} | {command:8s} | {address:15s} > {data.hex(" ")}')


################################################################################
def modbus_request(argspec):
    template = get_template(argspec.template)
    with ModbusClient(host=argspec.address, port=argspec.port) as client:
        CustomModbusResponse.function_code = argspec.function_code
        CustomModbusRequest.function_code = argspec.function_code

        client.register(CustomModbusResponse)
        request = CustomModbusRequest(
            argspec.first_register, unit=argspec.unit_id,
            count=argspec.count)

        request_response_messages('request', request.encode(), get_ip())
        result = client.execute(request)
        if not result:
            return None

        request_response_messages('respose', result.values,
                                  f'{argspec.address}:{argspec.port}')

    print()
    if argspec.function_code == 0x03:
        first_register = 40000
    else:
        first_register = 0
    data = get_data_with_template(result.values[1:], template,
                                  first_register=first_register)
    header = ["data type", "reg", "bytes", "value", "note"]
    data.insert(0, header)
    print(tabulate(data, headers="firstrow"))


################################################################################
def argument_parser():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-t', '--template', type=str,
                               help='template name', )
    parent_parser.add_argument('-a', '--address', default='localhost',
                               help='host address')
    parent_parser.add_argument('-p', '--port', type=int, default=502,
                               help='port')

    parser = argparse.ArgumentParser(
        prog='',
        description='description',
        epilog='end of description', )

    sub_parser = parser.add_subparsers(dest='sub_parser')

    read_holding_register_parser = sub_parser.add_parser(
        'read_holding_register', help='Setting Command',
        parents=[parent_parser])
    read_holding_register_parser.add_argument(
        '-i', '--unit-id', type=int, default=0, help='unit id')
    read_holding_register_parser.add_argument(
        '-f', '--first-register', type=int, default=0,
        help='first register address')
    read_holding_register_parser.add_argument(
        '-c', '--count', type=int, default=2, help='number of registers')
    read_holding_register_parser.set_defaults(
        func=modbus_request, function_code=0x03)

    exit_parser = sub_parser.add_parser('exit', help='Setting Command')
    exit_parser.set_defaults(func=lambda x: exit(0))

    return parser
