import yaml
import socket
import enum
import argparse
import struct
import itertools
import datetime
import functools
from tabulate import tabulate
from pymodbus.pdu import ModbusExceptions
from pymodbus.client.sync import ModbusTcpClient as ModbusClient


################################################################################
class ExceptionResponse(Exception):
    pass


################################################################################
def get_template(name):
    if not name:
        return None
    try:
        with open('templates.yml', 'r') as f:
            return yaml.safe_load(f)[name]
    except FileNotFoundError as e:
        print(f'\n** Error: Template file templates.yml should be '
              f'in the directory where modbusclc executed.')
        return None
    except KeyError as e:
        print(f'\n** Error: {name} is not in the template. Please Check it ..')
        return None
    except Exception as e:
        import traceback
        traceback.print_exc()
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
def make_record(index, data, template, first_register, register_size=2):
    record = list()
    dt = DataType[template['data_type'].upper()]
    dt_v = dt.value

    fmt = dt_v['format']

    record.append(dt.name)
    record.append(first_register + int(data[index][1]))
    record.append(space(data[index][0], register_size * 2))
    d = struct.unpack(fmt, bytes.fromhex(data[index][0]))
    if dt in (DataType.B8_STRING, DataType.B16_STRING, DataType.B32_STRING,
              DataType.B64_STRING):
        d = b''.join(d).decode('utf-8')
    elif dt in (DataType.BIT8,):
        d = f'{d[0]:07b}'
    else:
        d = d[0]
    record.append(d)
    record.append(template['note'])
    return record


def get_default_template(data, register_size):
    data_size = int(len(data) / register_size)
    data_type = 'B16_UINT'
    dt = DataType[data_type.upper()]
    template = itertools.repeat(
        {'note': '-', 'data_type': dt.name, },
        data_size)
    template = list(template)
    return template


################################################################################
def get_data_with_template(data: bytes, template, register_size=2,
                           start_register=40000):
    if not template:
        template = get_default_template(data, register_size)
    n = [DataType[x['data_type']].value['length'] for x in template]
    data = list(chunks(data, n))

    result = list()
    for i, t in enumerate(template):
        try:
            record = make_record(i, data, t, start_register, register_size)
            result.append(record)
        except struct.error:
            note = 'item exists but no data'
            record = f'{t["data_type"]}|' + (f'{"-":10s}|' * 3) + note
            result.append(record.split('|'))
            continue
    return result


################################################################################
class DataType(enum.Enum):
    B8_UINT = {'name': '8b uint', 'length': 1, 'format': '>B'}
    B8_INT = {'name': '8b int', 'length': 1, 'format': '>b'}
    BIT8 = {'name': '8 bits bool', 'length': 1, 'format': '>B'}

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
def request_response_messages(command, data: bytes, address=''):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{now} | {command:8s} | {address:15s} > {data.hex(" ")}')


################################################################################
def error_handle(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ExceptionResponse as e:
            print('** Error: ', e)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return

    return func


################################################################################
def print_table(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        argspec = args[0]
        start_address = {1: 0, 3: 40000}[argspec.function_code]
        template = get_template(argspec.template)
        data = f(*args, **kwargs)
        data = get_data_with_template(data[1:], template,
                                      start_register=start_address)
        header = ["no", "data type", "reg", "bytes", "value", "note"]
        data.insert(0, header)
        print(tabulate(data, headers="firstrow", showindex="always"))
    return func


################################################################################
def response_handle(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        response = f(*args, **kwargs)
        data = response.encode()
        if 1 == len(data):
            raise ExceptionResponse(
                ModbusExceptions.decode(int.from_bytes(data, 'big')))
        return data
    return func


################################################################################
@error_handle
@print_table
@response_handle
def read_holding_register(argspec):
    with ModbusClient(host=argspec.host, port=argspec.port) as client:
        response = client.read_holding_registers(argspec.address, argspec.count)
    return response


################################################################################
@error_handle
@print_table
@response_handle
def read_coils(argspec):
    with ModbusClient(host=argspec.host, port=argspec.port) as client:
        response = client.read_coils(argspec.address, argspec.count)
    return response

################################################################################
def argument_parser():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-t', '--template', type=str,
                               help='template name', )
    parent_parser.add_argument('-a', '--host', default='localhost',
                               help='host address')
    parent_parser.add_argument('-p', '--port', type=int, default=502,
                               help='port')

    essential_options_parser = argparse.ArgumentParser(add_help=False)
    essential_options_parser.add_argument(
        '-i', '--unit-id', type=int, default=0, help='unit id')
    essential_options_parser.add_argument(
        '-f', '--address', type=int, default=0,
        help='address')

    parser = argparse.ArgumentParser(
        prog='',
        description='description',
        epilog='end of description', )

    sub_parser = parser.add_subparsers(dest='sub_parser')

    ############################################################################
    # Read Coils 0x01
    read_coils_parser = sub_parser.add_parser(
        'read_coils', help='Read Coil(s)',
        parents=[parent_parser, essential_options_parser])
    read_coils_parser.add_argument(
        '-c', '--count', type=int, default=2, help='number of coils')
    read_coils_parser.set_defaults(
        func=read_coils, function_code=0x01)

    ############################################################################
    # Read Holding Registers 0x03
    read_holding_register_parser = sub_parser.add_parser(
        'read_holding_register', help='Setting Command',
        parents=[parent_parser, essential_options_parser])
    read_holding_register_parser.add_argument(
        '-c', '--count', type=int, default=2, help='number of registers')
    read_holding_register_parser.set_defaults(
        func=read_holding_register, function_code=0x03)

    exit_parser = sub_parser.add_parser('exit', help='Setting Command')
    exit_parser.set_defaults(func=lambda x: exit(0))

    return parser
