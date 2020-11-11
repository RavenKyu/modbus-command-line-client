import signal
import yaml
import socket
import enum
import struct
import itertools
import datetime
import functools
import pathlib
import operator
import atexit

from tabulate import tabulate
from pymodbus.pdu import ModbusExceptions
from pymodbus.client.sync import ModbusTcpClient as _ModbusClient
from pymodbus.client.sync import ModbusRtuFramer, ModbusSocketFramer
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus import exceptions


###############################################################################
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


###############################################################################
class ModbusClient(_ModbusClient, metaclass=Singleton):
    def __init__(self, host, port, mode):
        if mode == 'tcp':
            framer = ModbusSocketFramer
        elif mode == 'rtu-over-tcp':
            framer = ModbusRtuFramer
        else:
            raise ValueError(f"'{mode}' is not supported.")

        _ModbusClient.__init__(self, host=host, port=port, framer=framer)
        self._verbose = 0

    @property
    def verboses(self):
        yield self._verbose
        self._verbose = 0

    @verboses.setter
    def verboses(self, v: int):
        self._verbose = v

    def _recv(self, size):
        data = _ModbusClient._recv(self, size)
        if self._verbose:
            request_response_messages(
                'recv data', data, f'{self.host}:{self.port}')
        return data

    def _send(self, request):

        if self._verbose:
            request_response_messages('send data', request, get_ip())
        return _ModbusClient._send(self, request)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return


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
        Config.HOME_PATH.mkdir(parents=True, exist_ok=True)
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
            f.write(prompt)

    def new_config_merge(self, config_list: list):
        new_config = dict()
        for conf in config_list:
            new_config.update(conf)
        return {**self['setting'], **new_config}

    def set_default_config(self):
        if 'setting' not in self:
            self['setting'] = dict()
        hosts = {'ip': '127.0.0.1', 'port': 502, 'mode': 'tcp'}
        self['setting'] = self.new_config_merge([hosts])

        self._config_filepath.parent.mkdir(parents=True, exist_ok=True)
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
            traceback.print_exception(exc_type, exc_val, exc_tb)
            return
        self.save()

    def itemgetter(self, *args):
        self.get_config()
        return operator.itemgetter(*args)(self['setting'])


###############################################################################
def set_prompt(ip, port, mode):
    prompt = f'{ip}:{port}:{mode}>'
    config = Config()
    config.set_prompt(prompt)


CONF = Config()
set_prompt(**CONF['setting'])


###############################################################################
def exit_handler():
    client = ModbusClient(*CONF.itemgetter('ip', 'port'))
    if client.is_socket_open():
        client.close()
    print('** Good Bye **')
    exit(0)


atexit.register(exit_handler)


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
def get_sample_template():
    sample = {
        "sample": [
            {
                "note": "64 bit string",
                "data_type": "B64_STRING"
            },
            {
                "note": "32 bit string",
                "data_type": "B32_STRING"
            },
            {
                "note": "16 bit string",
                "data_type": "B16_STRING"
            },
            {
                "note": "8 bit string",
                "data_type": "B8_STRING"
            },
            {
                "note": "8 bit string",
                "data_type": "B8_STRING"
            },
            {
                "note": "64 bit unsigned int",
                "data_type": "B64_UINT"
            },
            {
                "note": "64 bit int",
                "data_type": "B64_INT"
            },
            {
                "note": "32 bit unsigned int",
                "data_type": "B32_UINT"
            },
            {
                "note": "32 bit int",
                "data_type": "B32_INT"
            },
            {
                "note": "16 bit unsigned int",
                "data_type": "B16_UINT"
            },
            {
                "note": "16 bit int",
                "data_type": "B16_INT"
            },
            {
                "note": "8 bit unsigned int",
                "data_type": "B8_UINT"
            },
            {
                "note": "8 bit int",
                "data_type": "B8_INT"
            },
            {
                "note": "64 bit float",
                "data_type": "B64_FLOAT"
            },
            {
                "note": "32 bit float",
                "data_type": "B32_FLOAT"
            },
            {
                "note": "16 bit float",
                "data_type": "B16_FLOAT"
            }
        ]
    }
    return sample


###############################################################################
def get_template(name: str):
    if not name:
        return None

    file = CONF.TEMPLATES_FILE
    if not file.exists():
        CONF.TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(str(file), 'w') as f:
            template = get_sample_template()
            f.write(yaml.dump(template))
    try:
        file = CONF.TEMPLATES_FILE
        with open(str(file), 'r') as f:
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

        # Directives Data Type
        values = argspec.values
        if values and not argspec.template:
            template = [{'note': '-', 'data_type': x} for x in values]
        # Template File
        else:
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
        if response.isError():
            if isinstance(response, exceptions.ModbusIOException):
                # Probably, disconnected to the Modbus Server.
                ip, port = CONF.itemgetter('ip', 'port')
                client = ModbusClient(host=ip, port=port)
                client.close()
                raise ExceptionResponse(response.message)

            else:
                raise ExceptionResponse(ModbusExceptions.decode(
                    int.from_bytes(response.encode(), 'big')))

        data = response.encode()
        return data

    return func


###############################################################################
@error_handle
@print_table
@response_handle
def read_input_registers(argspec):
    ip, port, mode = CONF.itemgetter('ip', 'port', 'mode')
    with ModbusClient(host=ip, port=port, mode=mode) as client:
        client._verbose = argspec.verbose
        response = client.read_input_registers(argspec.address, argspec.count)
    return response


###############################################################################
@error_handle
@print_table
@response_handle
def read_holding_register(argspec):
    ip, port, mode = CONF.itemgetter('ip', 'port', 'mode')
    with ModbusClient(host=ip, port=port, mode=mode) as client:
        client._verbose = argspec.verbose
        response = client.read_holding_registers(argspec.address,
                                                 argspec.count)
    return response


###############################################################################
@error_handle
@print_table
@response_handle
def read_discrete_inputs(argspec):
    ip, port, mode = CONF.itemgetter('ip', 'port', 'mode')
    with ModbusClient(host=ip, port=port, mode=mode) as client:
        client._verbose = argspec.verbose
        response = client.read_discrete_inputs(argspec.address, argspec.count)
    return response


###############################################################################
@error_handle
@print_table
@response_handle
def read_coils(argspec):
    ip, port, mode = CONF.itemgetter('ip', 'port', 'mode')
    with ModbusClient(host=ip, port=port, mode=mode) as client:
        client._verbose = argspec.verbose
        response = client.read_coils(argspec.address, argspec.count)
    return response


###############################################################################
@error_handle
@response_handle
def write_single_coil(argspec):
    ip, port, mode = CONF.itemgetter('ip', 'port', 'mode')
    with ModbusClient(host=ip, port=port, mode=mode) as client:
        client._verbose = argspec.verbose
        response = client.write_coil(argspec.address, argspec.value)
    return response


###############################################################################
@error_handle
@response_handle
def write_multiple_coils(argspec):
    ip, port, mode = CONF.itemgetter('ip', 'port', 'mode')
    with ModbusClient(host=ip, port=port, mode=mode) as client:
        client._verbose = argspec.verbose
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

    ip, port, mode = CONF.itemgetter('ip', 'port', 'mode')
    with ModbusClient(host=ip, port=port, mode=mode) as client:
        client._verbose = argspec.verbose
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

    ip, port, mode = CONF.itemgetter('ip', 'port', 'mode')
    with ModbusClient(host=ip, port=port, mode=mode) as client:
        client._verbose = argspec.verbose
        response = client.write_registers(
            argspec.address, payload, skip_encode=True, unit=argspec.unit_id)
    return response


###############################################################################
def setting(argspec):
    with Config() as config:
        config['setting']['ip'] = argspec.ip
        config['setting']['port'] = argspec.port
        config['setting']['mode'] = argspec.mode
        set_prompt(**config['setting'])
    Singleton._instances = {}


###############################################################################
__all__ = ['setting', 'read_coils', 'read_discrete_inputs',
           'read_holding_register',
           'read_input_registers', 'write_single_coil',
           'write_single_register', 'write_multiple_coils',
           'write_multiple_registers', 'Config', 'set_prompt']
