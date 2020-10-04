import argparse
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer


class CustomDataBlock(ModbusSparseDataBlock):

    def setValues(self, address, value):
        """ Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        """
        super(CustomDataBlock, self).setValues(address, value)

        # whatever you want to do with the written value is done here,
        # however make sure not to do too much work here or it will
        # block the server, espectially if the server is being written
        # to very quickly
        print("wrote {} to {}".format(value, address))


def run_custom_db_server(address, port):
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #
    block = CustomDataBlock([
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

    ])
    store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block,
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
