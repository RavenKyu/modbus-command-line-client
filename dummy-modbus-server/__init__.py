import argparse
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

register_data = [
    0x556e, 0x6974, 0x3233, 0x2d41,  # 64bit chr Unit23-A
    0xffff,  # 16bit UINT 65535
    0xfc19,  # 16ibt INT -32768
    0xffff, 0xfffa,  # 32bit UINT 4294967290
    0x8000, 0x0000,  # 32bit INT -2147483648
    0x437e, 0xe2c6,  # 32bit Float 254.88583
    0x420a, 0xc326,  # 32bit Float 34.69057
    0x427d, 0x7aeb,  # 32bit Float 63.37004
    0x4107, 0x0e38,  # 32bit Float 8.440971
    0xffff,  # 8bit UINT 0, 8bit int
    0x0007,  # 8bits 0000 0000 0x07,  # 8bits 0000 0111
]


def run_custom_db_server(address, port):
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #
    coil_block = ModbusSequentialDataBlock(1, [0] * 256)
    discrete_input_block = ModbusSequentialDataBlock(10001, [0] * 256)
    input_register_block = ModbusSequentialDataBlock(30001, register_data)
    holding_register_block = ModbusSequentialDataBlock(40001, register_data)
    store = ModbusSlaveContext(di=discrete_input_block, co=coil_block,
                               hr=holding_register_block,
                               ir=input_register_block,
                               zero_mode=True)
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #

    identity = ModbusDeviceIdentification()
    identity.VendorName = 'pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/bashwork/pymodbus/'
    identity.ProductName = 'pymodbus Server'
    identity.ModelName = 'pymodbus Server'
    identity.MajorMinorRevision = '2.3.0'

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #

    # p = Process(target=device_writer, args=(queue,))
    # p.start()
    StartTcpServer(context, identity=identity, address=(address, port))


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', type=str, default='0.0.0.0')
    parser.add_argument('-p', '--port', type=int, default=502)
    return parser
