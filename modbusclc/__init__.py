import signal
import yaml
import socket
import enum
import argparse
import struct
import itertools
import datetime
import functools
import re
import pathlib
import operator

from tabulate import tabulate
from pymodbus.pdu import ModbusExceptions
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
from pymodbus import exceptions


###############################################################################
class Config(dict):
    HOME_PATH = pathlib.Path.home() / '.config' / 'modbusclc'
    CONFIG_FILE = HOME_PATH / 'config.yml'
    TEMPLATES_FILE = HOME_PATH / 'templates.yml'
    _instance = None

    def __init__(self, config_filepath=None, **kwargs):
        dict.__init__(self, **kwargs)
        if not config_filepath:
            config_filepath = Config.CONFIG_FILE.absolute()
        self._config_filepath = pathlib.Path(config_filepath)
        if not self.get_config():
            raise ValueError('config error')

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = Config()
        return cls._instance

    @staticmethod
    def set_prompt(prompt):
        with open('prompt', 'w') as f:
            print(prompt)
            f.write(prompt)

    def new_config_merge(self, config_list: list):
        new_config = dict()
        for conf in config_list:
            new_config.update(conf)
        return {**self['setting'], **new_config}

    def set_default_config(self):
        if 'setting' not in self:
            self['setting'] = dict()
        hosts = {'ip': '127.0.0.1', 'port': 502}
        self['setting'] = self.new_config_merge([hosts])

        self._config_filepath.parent.mkdir(exist_ok=True)
        self._config_filepath.touch()
        with self._config_filepath.open('w') as f:
            f.write(yaml.dump(self['setting']))
        return self._config_filepath.absolute()

    def get_config(self):
        # if not exist, saving a new config file with the default setting
        if not self._config_filepath.exists():
            self.set_default_config()
        with self._config_filepath.open('r') as f:
            self['setting'] = yaml.safe_load(f)
        return self

    def save(self):
        with self._config_filepath.open('w') as f:
            f.write(yaml.dump(self['setting']))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb:
            import traceback
            traceback.print_exception(exc_type,exc_val, exc_tb)
            return
        self.save()

    def itemgetter(self, *args):
        self.get_config()
        return operator.itemgetter(*args)(self['setting'])


CONF = Config()


###############################################################################
def signal_handler(sig, frame):
    pass


signal.signal(signal.SIGINT, signal_handler)


###############################################################################
class ExceptionResponse(Exception):
    pass


###############################################################################
class DataType(enum.Enum):
    BIT1_BOOLEAN = {'name': '1b boolean', 'length': 1, 'format': '?'}
    BIT8 = {'name': '8 bits bool', 'length': 1, 'format': '>B'}

    B8_UINT = {'name': '8b uint', 'length': 1, 'format': '>B'}
    B8_INT = {'name': '8b int', 'length': 1, 'format': '>b'}
    B16_UINT = {'name': '16b uint', 'length': 2, 'format': '>H'}
    B16_INT = {'name': '16b int', 'length': 2, 'format': '>h'}
    B32_UINT = {'name': '32b uint', 'length': 4, 'format': '>I'}
    B32_INT = {'name': '32b int', 'length': 4, 'format': '>i'}
    B64_UINT = {'name': '64b uint', 'length': 8, 'format': '>Q'}
    B64_INT = {'name': '64b int', 'length': 8, 'format': '>q'}

    B16_FLOAT = {'name': '16b float', 'length': 2, 'format': '>e'}
    B32_FLOAT = {'name': '32b float', 'length': 4, 'format': '>f'}
    B64_FLOAT = {'name': '64b float', 'length': 8, 'format': '>d'}

    B8_STRING = {'name': '8b sting', 'length': 1, 'format': '>c'}
    B16_STRING = {'name': '16b sting', 'length': 2, 'format': '>cc'}
    B32_STRING = {'name': '32b sting', 'length': 4, 'format': '>cccc'}
    B64_STRING = {'name': '64b sting', 'length': 8, 'format': '>cccccccc'}


###############################################################################
def regex_type_0or1(arg_value, pat=re.compile(r"^[0|1| ]*$")):
    if not pat.match(arg_value):
        raise argparse.ArgumentTypeError('The values must be 0 or 1.')
    return arg_value


###############################################################################
class ActionMultipleTypeValues(argparse.Action):
    def __init__(
            self, option_strings, dest, const,
            nargs=None,
            default=None,
            type=None,
            required=False,
            help=None,
            metavar=None):
        super(ActionMultipleTypeValues, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            const=const,
            default=default,
            type=type,
            required=required,
            help=help,
            metavar=metavar)

    @staticmethod
    def _copy_items(items):
        if items is None:
            return []
        if type(items) is list:
            return items[:]
        import copy
        return copy.copy(items)

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        items = ActionMultipleTypeValues._copy_items(items)
        if 'add_bits' == self.const:
            values = list(map(int, values.replace(' ', '')))
            values.reverse()

        items.append((self.const, values))
        setattr(namespace, self.dest, items)


###############################################################################
def get_template(name):
    if not name:
        return None
    try:
        with open('templates.yml', 'r') as f:
            return yaml.safe_load(f)[name]
    except FileNotFoundError:
        print('\n** Error: Template file templates.yml should be '
              'in the directory where modbusclc executed.')
        return None
    except KeyError:
        print(f'\n** Error: {name} is not in the template. Please Check it ..')
        return None
    except Exception:
        import traceback
        traceback.print_exc()
        return None


###############################################################################
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


###############################################################################
def chunks(lst, size_list: (list, tuple), register_size=2):
    """

    :param lst: b'\xfc\x19\xff\xff\xff\xfe'
    :param size_list: (2, 2, 1, 1)
    :param register_size: 2 (16bit)
    :return: [('fc19', 1), ('ffff', 2), ('ff', 3), ('fe', 3)]

    """
    index = 0
    register = 0
    for i in size_list:
        hex_value = lst[index:index + i].hex()
        yield hex_value, int(register)
        register += i / register_size
        index += i


###############################################################################
def chunks_bits(lst, size_list: (list, tuple)):
    address = 0
    value = int.from_bytes(lst, 'little')
    for i, _ in enumerate(size_list):
        yield (value >> i) & 1, address
        address += 1


###############################################################################
def space(string, length):
    """

    :param string: '556e697432332d41'
    :param length: 4
    :return: 556e 6974 3233 2d41
    """
    return ' '.join(
        string[i:i + length] for i in range(0, len(string), length))


###############################################################################
def make_record(index, data, template, first_register):
    record = list()
    data_type = getattr(DataType, template['data_type'])
    fmt = data_type.value['format']

    record.append(data_type.name)
    record.append(first_register + int(data[index][1]))
    if data_type is data_type.BIT1_BOOLEAN:
        record.append(data[index][0])
        d = bool(data[index][0])
    else:
        record.append(space(data[index][0], 4))
        d = struct.unpack(fmt, bytes.fromhex(data[index][0]))

    if data_type in (
            DataType.B8_STRING, DataType.B16_STRING, DataType.B32_STRING,
            DataType.B64_STRING):
        d = b''.join(d).decode('utf-8')
    elif data_type in (DataType.BIT8,):
        d = f'{d[0]:07b}'
    elif data_type in (DataType.BIT1_BOOLEAN,):
        pass
    else:
        d = d[0]
    record.append(d)
    record.append(template['note'])
    return record


###############################################################################
def get_default_template(data_type: DataType, count):
    if data_type is data_type.BIT1_BOOLEAN:
        data_size = count
    else:
        data_size = int(count / data_type.value['length'])
    template = itertools.repeat(
        {'note': '-', 'data_type': data_type.name, },
        data_size)
    template = list(template)
    return template


###############################################################################
def get_data_with_template(data: bytes, template,
                           data_type: DataType = DataType.B16_UINT,
                           start_register=0, count=1):
    if not template:
        template = get_default_template(data_type, count)
    n = [DataType[x['data_type']].value['length'] for x in template]

    if data_type is data_type.BIT1_BOOLEAN:
        data = list(chunks_bits(data, n))
    else:
        data = list(chunks(data, n))

    result = list()
    for i, t in enumerate(template):
        try:
            record = make_record(i, data, t, start_register)
            result.append(record)
        except struct.error:
            note = 'item exists but no data'
            record = f'{t["data_type"]}|' + (f'{"-":10s}|' * 3) + note
            result.append(record.split('|'))
            continue
    return result


###############################################################################
def request_response_messages(command, data: bytes, address=''):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{now} | {command:8s} | {address:15s} > {data.hex(" ")}')


###############################################################################
def error_handle(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except exceptions.ConnectionException as e:
            print('** Error: ', e)
        except ExceptionResponse as e:
            print('** Error: ', e)
        except Exception:
            import traceback
            traceback.print_exc()
            return

    return func


###############################################################################
def print_table(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        data = f(*args, **kwargs)
        argspec = args[0]
        if argspec.function_code in (0x01, 0x02):
            data_type = DataType.BIT1_BOOLEAN
        else:
            data_type = DataType.B16_UINT

        template = get_template(argspec.template)
        start_address = argspec.address
        data = get_data_with_template(
            data[1:], template,
            start_register=start_address, data_type=data_type,
            count=argspec.count)

        header = ["no", "data type", "address", "data", "value", "note"]
        data.insert(0, header)
        print(tabulate(data, headers="firstrow", showindex="always"))

    return func


###############################################################################
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


###############################################################################
@error_handle
@print_table
@response_handle
def read_input_registers(argspec):
    ip, port = CONF.itemgetter('ip', 'port')
    with ModbusClient(host=ip, port=port) as client:
        response = client.read_input_registers(argspec.address, argspec.count)
    return response


###############################################################################
@error_handle
@print_table
@response_handle
def read_holding_register(argspec):
    ip, port = CONF.itemgetter('ip', 'port')
    with ModbusClient(host=ip, port=port) as client:
        response = client.read_holding_registers(argspec.address,
                                                 argspec.count)
    return response


###############################################################################
@error_handle
@print_table
@response_handle
def read_discrete_inputs(argspec):
    ip, port = CONF.itemgetter('ip', 'port')
    with ModbusClient(host=ip, port=port) as client:
        response = client.read_discrete_inputs(argspec.address, argspec.count)
    return response


###############################################################################
@error_handle
@print_table
@response_handle
def read_coils(argspec):
    ip, port = CONF.itemgetter('ip', 'port')
    with ModbusClient(host=ip, port=port) as client:
        response = client.read_coils(argspec.address, argspec.count)
    return response


###############################################################################
@error_handle
@response_handle
def write_single_coil(argspec):
    ip, port = CONF.itemgetter('ip', 'port')
    with ModbusClient(host=ip, port=port) as client:
        response = client.write_coil(argspec.address, argspec.value)
    return response


###############################################################################
@error_handle
@response_handle
def write_multiple_coils(argspec):
    ip, port = CONF.itemgetter('ip', 'port')
    with ModbusClient(host=ip, port=port) as client:
        response = client.write_coils(
            argspec.address, list(map(int, argspec.values)))
    return response


###############################################################################
@error_handle
@response_handle
def write_single_register(argspec):
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
    for func, value in argspec.values[:1]:
        getattr(builder, func)(value)
    payload = builder.build()

    ip, port = CONF.itemgetter('ip', 'port')
    with ModbusClient(host=ip, port=port) as client:
        response = client.write_register(
            argspec.address, payload[0], skip_encode=True,
            unit=argspec.unit_id)
    return response


###############################################################################
@error_handle
@response_handle
def write_multiple_registers(argspec):
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
    for func, value in argspec.values:
        getattr(builder, func)(value)
    payload = builder.build()

    ip, port = CONF.itemgetter('ip', 'port')
    with ModbusClient(host=ip, port=port) as client:
        response = client.write_registers(
            argspec.address, payload, skip_encode=True, unit=argspec.unit_id)
    return response


###############################################################################
def setting(argspec):
    with Config() as config:
        config['setting']['ip'] = argspec.ip
        config['setting']['port'] = argspec.port
        prompt = '{ip}:{port}>'.format(**config['setting'])
        config.set_prompt(prompt)


###############################################################################
def argument_parser():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-t', '--template', type=str,
                               help='template name', )

    ###########################################################################
    essential_options_parser = argparse.ArgumentParser(add_help=False)
    essential_options_parser.add_argument(
        '-i', '--unit-id', type=int, default=0, help='unit id')

    ###########################################################################
    single_register_data_type_parser = argparse.ArgumentParser(add_help=False)
    single_register_data_type_parser.add_argument(
        '--string', dest='values', action=ActionMultipleTypeValues,
        const='add_string', help='string ex) hello_world or "hello world"')
    single_register_data_type_parser.add_argument(
        '--b16int', dest='values', type=int, action=ActionMultipleTypeValues,
        const='add_16bit_int')
    single_register_data_type_parser.add_argument(
        '--b16uint', dest='values', type=int, action=ActionMultipleTypeValues,
        const='add_16bit_uint')
    single_register_data_type_parser.add_argument(
        '--b16float', dest='values', type=float,
        action=ActionMultipleTypeValues,
        const='add_16bit_float', help='')

    ###########################################################################
    multiple_register_data_type_parser = argparse.ArgumentParser(
        add_help=False)
    multiple_register_data_type_parser.add_argument(
        '--string', dest='values', action=ActionMultipleTypeValues,
        const='add_string', help='string ex) hello_world or "hello world"')
    multiple_register_data_type_parser.add_argument(
        '--bits', dest='values', type=regex_type_0or1,
        action=ActionMultipleTypeValues, const='add_bits',
        help='bits ex) 1110 => 00001110 or 1111000010101010 or "1111 00 11"')
    multiple_register_data_type_parser.add_argument(
        '--b8int', dest='values', type=int, action=ActionMultipleTypeValues,
        const='add_8bit_int')
    multiple_register_data_type_parser.add_argument(
        '--b8uint', dest='values', type=int, action=ActionMultipleTypeValues,
        const='add_8bit_uint')
    multiple_register_data_type_parser.add_argument(
        '--b32int', dest='values', type=int, action=ActionMultipleTypeValues,
        const='add_32bit_int', help='')
    multiple_register_data_type_parser.add_argument(
        '--b32uint', dest='values', type=int, action=ActionMultipleTypeValues,
        const='add_32bit_uint', help='')
    multiple_register_data_type_parser.add_argument(
        '--b64int', dest='values', type=int, action=ActionMultipleTypeValues,
        const='add_64bit_int', help='')
    multiple_register_data_type_parser.add_argument(
        '--b64uint', dest='values', type=int, action=ActionMultipleTypeValues,
        const='add_64bit_uint', help='')
    multiple_register_data_type_parser.add_argument(
        '--b32float', dest='values', type=float,
        action=ActionMultipleTypeValues,
        const='add_32bit_float', help='')
    multiple_register_data_type_parser.add_argument(
        '--b64float', dest='values', type=float,
        action=ActionMultipleTypeValues,
        const='add_64bit_float', help='')

    ###########################################################################
    parser = argparse.ArgumentParser(
        prog='',
        description='description',
        epilog='end of description', )

    sub_parser = parser.add_subparsers(dest='sub_parser')

    ###########################################################################
    setting_parser = sub_parser.add_parser('setting', help='setting')
    setting_parser.add_argument(
        '--ip', default='localhost', help='host address')
    setting_parser.add_argument(
        '--port', type=int, default=502, help='port')
    setting_parser.set_defaults(func=setting)

    ###########################################################################
    exit_parser = sub_parser.add_parser('exit', help='Setting Command')
    exit_parser.set_defaults(func=lambda x: exit(0))

    ###########################################################################
    # Read Coils 0x01
    read_coils_parser = sub_parser.add_parser(
        'read_coils', help='Read Coil(s)',
        parents=[parent_parser, essential_options_parser],
        conflict_handler='resolve')
    read_coils_parser.add_argument(
        '-a', '--address', type=int, default=1, help='address'),
    read_coils_parser.add_argument(
        '-c', '--count', type=int, default=1, help='number of coils')
    read_coils_parser.set_defaults(
        func=read_coils, function_code=0x01)

    ###########################################################################
    # Read Discrete Inputs 0x02
    read_discrete_inputs_parser = sub_parser.add_parser(
        'read_discrete_inputs', help='Read Discrete Inputs',
        parents=[parent_parser, essential_options_parser],
        conflict_handler='resolve')
    read_discrete_inputs_parser.add_argument(
        '-a', '--address', type=int, default=10001, help='address'),
    read_discrete_inputs_parser.add_argument(
        '-c', '--count', type=int, default=1, help='number of coils')
    read_discrete_inputs_parser.set_defaults(
        func=read_discrete_inputs, function_code=0x02)

    ###########################################################################
    # Read Holding Registers 0x03
    read_holding_register_parser = sub_parser.add_parser(
        'read_holding_register', help='Setting Command',
        conflict_handler='resolve',
        parents=[parent_parser, essential_options_parser])
    read_holding_register_parser.add_argument(
        '-a', '--address', type=int, default=40001, help='address'),
    read_holding_register_parser.add_argument(
        '-c', '--count', type=int, default=2, help='number of registers')
    read_holding_register_parser.set_defaults(
        func=read_holding_register, function_code=0x03)

    ###########################################################################
    # Read Input Registers 0x04
    read_input_register_parser = sub_parser.add_parser(
        'read_input_register', help='Setting Command',
        conflict_handler='resolve',
        parents=[parent_parser, essential_options_parser])
    read_input_register_parser.add_argument(
        '-a', '--address', type=int, default=30001, help='address'),
    read_input_register_parser.add_argument(
        '-c', '--count', type=int, default=2, help='number of registers')
    read_input_register_parser.set_defaults(
        func=read_input_registers, function_code=0x04)

    ###########################################################################
    # Writing Single Coil 0x05
    write_single_coil_parser = sub_parser.add_parser(
        'write_single_coil', help='write single Coil',
        parents=[parent_parser, essential_options_parser],
        conflict_handler='resolve')
    write_single_coil_parser.add_argument(
        'address', type=int, help='address where the value stores')
    write_single_coil_parser.add_argument(
        'value', type=int, choices=[0, 1],
        help='1/0 boolean.')
    write_single_coil_parser.set_defaults(
        func=write_single_coil, function_code=0x05)

    ###########################################################################
    # Writing Single Register 0x06
    write_single_registers_parser = sub_parser.add_parser(
        'write_single_register', help='writing single register',
        parents=[parent_parser, essential_options_parser,
                 single_register_data_type_parser],
        conflict_handler='resolve')
    write_single_registers_parser.add_argument(
        'address', type=int, help='address where the value stores')
    write_single_registers_parser.set_defaults(
        func=write_single_register, function_code=0x06)

    ###########################################################################
    # Writing Multiple Coils 0x0f
    write_single_coil_parser = sub_parser.add_parser(
        'write_multiple_coils', help='writing multiple coils',
        parents=[parent_parser, essential_options_parser],
        conflict_handler='resolve')
    write_single_coil_parser.add_argument(
        'address', type=int, help='address where the value stores')
    write_single_coil_parser.add_argument(
        'values', type=regex_type_0or1, help='1/0 boolean. ex) 01101100')
    write_single_coil_parser.set_defaults(
        func=write_multiple_coils, function_code=0x0f)

    ###########################################################################
    # Writing Multiple Register 0x10
    write_multiple_registers_parser = sub_parser.add_parser(
        'write_multiple_registers', help='writing multiple registers',
        parents=[parent_parser, essential_options_parser,
                 multiple_register_data_type_parser,
                 single_register_data_type_parser],
        conflict_handler='resolve')
    write_multiple_registers_parser.add_argument(
        'address', type=int, help='address where the value stores')
    write_multiple_registers_parser.set_defaults(
        func=write_multiple_registers, function_code=0x10)

    return parser
