========
Examples
========
You can get started fast, here you go.


-------------------
Modbus Dummy Server
-------------------
The dummy modbus server for these examples included in the repository.

.. code-block:: bash

    # cloning the source code from the repository
    $ git clone https://github.com/RavenKyu/modbus-command-line-client.git

    # using docker if you want. the directory you are should be at the root of the repository.
    $ docker build -t dummy-modbus-server:latest -f ./dummy-modbus-server/Dockerfile .
    $ docker run --rm dummy-modbus-server:latest
    # or
    # docker-compose would be easier.
    $ docker-compose up -d dummy-modbus-server

-----------------
Running ModbusCLC
-----------------

.. code-block:: bash

    # if you installed
    $ modbusclc
    # else, you better to make a virtualenv, activate it and install dependencies according to requirements.txt
    # and then,
    $ python -m modbusclc
    # also, you can use docker container after build it.
    $ docker build -t modbusclc:latest .
    $ docker run -it --rm modbusclc:latest

---------------
Setting Address
---------------

.. code-block:: bash

    # setting the device address you connect to.
    localhost:502> setting --ip 192.168.10.5 --port 502
    192.168.10.5:502>

-----------------
Read Coils (0x01)
-----------------
.. code-block:: bash

    # Without using the address option, the address starts from 1.
    localhost:502> read_coils -c 8
      no  data type       address    data  value    note
    ----  ------------  ---------  ------  -------  ------
       0  BIT1_BOOLEAN          1       0  False    -
       1  BIT1_BOOLEAN          2       0  False    -
       2  BIT1_BOOLEAN          3       0  False    -
       3  BIT1_BOOLEAN          4       0  False    -
       4  BIT1_BOOLEAN          5       0  False    -
       5  BIT1_BOOLEAN          6       0  False    -
       6  BIT1_BOOLEAN          7       0  False    -
       7  BIT1_BOOLEAN          8       0  False    -
    localhost:502>

--------------------------
Read Discrete Input (0x02)
--------------------------
.. code-block:: bash

    # Without using the address option, the address starts from 10001.
    localhost:502> read_discrete_inputs -c 8
      no  data type       address    data  value    note
    ----  ------------  ---------  ------  -------  ------
       0  BIT1_BOOLEAN      10001       0  False    -
       1  BIT1_BOOLEAN      10002       0  False    -
       2  BIT1_BOOLEAN      10003       0  False    -
       3  BIT1_BOOLEAN      10004       0  False    -
       4  BIT1_BOOLEAN      10005       0  False    -
       5  BIT1_BOOLEAN      10006       0  False    -
       6  BIT1_BOOLEAN      10007       0  False    -
       7  BIT1_BOOLEAN      10008       0  False    -
    localhost:502>


----------------------------
Read Holding Register (0x03)
----------------------------

.. code-block:: bash

    # Without using the address option, the address starts from 40001.
    localhost:502> read_holding_register -c10
      no  data type      address  data      value  note
    ----  -----------  ---------  ------  -------  ------
       0  B16_UINT         40001  7765      30565  -
       1  B16_UINT         40002  6c63      27747  -
       2  B16_UINT         40003  6f6d      28525  -
       3  B16_UINT         40004  6521      25889  -
       4  B16_UINT         40005  4142      16706  -
    localhost:502>

----------------------------
Read Input Register (0x04)
----------------------------

.. code-block:: bash

    # Without using the address option, the address starts from 30001.
    localhost:502> read_input_register -a30003 -c10
      no  data type      address  data      value  note
    ----  -----------  ---------  ------  -------  ------
       0  B16_UINT         30003  6f6d      28525  -
       1  B16_UINT         30004  6521      25889  -
       2  B16_UINT         30005  4142      16706  -
       3  B16_UINT         30006  4344      17220  -
       4  B16_UINT         30007  4546      17734  -
    localhost:502>

----------------------------
Write Single Coil (0x05)
----------------------------

.. code-block:: bash

    # before writing value
    localhost:502> read_coils -a1 -c8
      no  data type       address    data  value    note
    ----  ------------  ---------  ------  -------  ------
       0  BIT1_BOOLEAN          1       0  False    -
       1  BIT1_BOOLEAN          2       0  False    -
       2  BIT1_BOOLEAN          3       0  False    -
       3  BIT1_BOOLEAN          4       0  False    -
       4  BIT1_BOOLEAN          5       0  False    -
       5  BIT1_BOOLEAN          6       0  False    -
       6  BIT1_BOOLEAN          7       0  False    -
       7  BIT1_BOOLEAN          8       0  False    -

    # write 1 at the 3rd of coils
    localhost:502> write_single_coil 3 1

    localhost:502> read_coils -a1 -c8
      no  data type       address    data  value    note
    ----  ------------  ---------  ------  -------  ------
       0  BIT1_BOOLEAN          1       0  False    -
       1  BIT1_BOOLEAN          2       0  False    -
       2  BIT1_BOOLEAN          3       1  True     -
       3  BIT1_BOOLEAN          4       0  False    -
       4  BIT1_BOOLEAN          5       0  False    -
       5  BIT1_BOOLEAN          6       0  False    -
       6  BIT1_BOOLEAN          7       0  False    -
       7  BIT1_BOOLEAN          8       0  False    -
    localhost:502>

----------------------------
Write Single Register (0x06)
----------------------------

.. code-block:: bash

    # before writing value
    localhost:502> read_holding_register -c4
      no  data type      address  data      value  note
    ----  -----------  ---------  ------  -------  ------
       0  B16_UINT         40001  7765      30565  -
       1  B16_UINT         40002  6c63      27747  -

    # write a integer -999(0xfc19) at the register 40002
    localhost:502> write_single_register 40002 --b16int -999

    localhost:502> read_holding_register -c4
      no  data type      address  data      value  note
    ----  -----------  ---------  ------  -------  ------
       0  B16_UINT         40001  7765      30565  -
       1  B16_UINT         40002  fc19      64537  -
    localhost:502>

* Writing-Single-Register is allowed to write just for one register value only.
* The values out of range in the data type is not able to write.

+-------------------------+------------+-----------------+-----------------------------------------------------+
| Data Type               | Directives | Examples        | Description                                         |
+-------------------------+------------+-----------------+-----------------------------------------------------+
| String                  | --string   | --string AB     | You can put strings as much as 2 bytes              |
+-------------------------+------------+-----------------+-----------------------------------------------------+
| 16 Bit Signed Integer   | --b16int   | --b16int -999   | It allows only within 2 bytes much signed integer   |
+-------------------------+------------+-----------------+-----------------------------------------------------+
| 16 Bit Unsigned Integer | --b16uint  | --b16uint 65535 | It allows only within 2 bytes much unsigned integer |
+-------------------------+------------+-----------------+-----------------------------------------------------+
| 16 Bit Float            | --b16float | --16float 3.14  |                                                     |
+-------------------------+------------+-----------------+-----------------------------------------------------+

----------------------------
Write Multiple Coils (0x0F)
----------------------------

.. code-block:: bash

    # before writing values
    localhost:502> read_coils -c8
      no  data type       address    data  value    note
    ----  ------------  ---------  ------  -------  ------
       0  BIT1_BOOLEAN          1       0  False    -
       1  BIT1_BOOLEAN          2       0  False    -
       2  BIT1_BOOLEAN          3       1  True     -
       3  BIT1_BOOLEAN          4       0  False    -
       4  BIT1_BOOLEAN          5       0  False    -
       5  BIT1_BOOLEAN          6       0  False    -
       6  BIT1_BOOLEAN          7       0  False    -
       7  BIT1_BOOLEAN          8       0  False    -

    # writing the binaries from the start address to as many as the length of the value
    localhost:502> write_multiple_coils 1 01101100

    localhost:502> read_coils -c8
      no  data type       address    data  value    note
    ----  ------------  ---------  ------  -------  ------
       0  BIT1_BOOLEAN          1       0  False    -
       1  BIT1_BOOLEAN          2       1  True     -
       2  BIT1_BOOLEAN          3       1  True     -
       3  BIT1_BOOLEAN          4       0  False    -
       4  BIT1_BOOLEAN          5       1  True     -
       5  BIT1_BOOLEAN          6       1  True     -
       6  BIT1_BOOLEAN          7       0  False    -
       7  BIT1_BOOLEAN          8       0  False    -
    localhost:502>

-------------------------------
Write Multiple Registers (0x10)
-------------------------------

.. code-block:: bash

    # before writing values
    localhost:502> read_holding_register -c6
      no  data type      address  data      value  note
    ----  -----------  ---------  ------  -------  ------
       0  B16_UINT         40001  7765      30565  -
       1  B16_UINT         40002  fc19      64537  -
       2  B16_UINT         40003  6f6d      28525  -

    localhost:502> write_multiple_registers 40001 --b32uint 123456789 --string AB

    localhost:502> read_holding_register -c6
      no  data type      address  data      value  note
    ----  -----------  ---------  ------  -------  ------
       0  B16_UINT         40001  075b       1883  -
       1  B16_UINT         40002  cd15      52501  -
       2  B16_UINT         40003  4142      16706  -
    localhost:502>

+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| Data Type               | Directives | Examples                                                    | Description                                         |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| String                  | --string   | --string AB                                                 | You can put strings as much as 2 bytes              |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| bits                    | --bits     | --bits 1110 => 00001110 or 1111000010101010 or "1111 00 11" |                                                     |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 8 Bit Signed Integer    | --b8int    | --b8int -128                                                | It allows only within 1 bytes much signed integer   |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 8 Bit Unsigned Integer  | --b8uint   | --b8uint 255                                                | It allows only within 1 bytes much unsigned integer |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 16 Bit Signed Integer   | --b16int   | --b16int -999                                               | It allows only within 2 bytes much signed integer   |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 16 Bit Unsigned Integer | --b16uint  | --b16uint 65535                                             | It allows only within 2 bytes much unsigned integer |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 32 Bit Signed Integer   | --b32int   | --b32int -2147483648                                        | It allows only within 4 bytes much signed integer   |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 32 Bit Unsigned Integer | --b32uint  |                                                             | It allows only within 4 bytes much unsigned integer |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 16 Bit Float            | --b16float | --16float 3.14                                              |                                                     |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 32 Bit Float            | --b32float | --32float 3.14                                              |                                                     |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+
| 64 Bit Float            | --b64float | --64float 3.14                                              |                                                     |
+-------------------------+------------+-------------------------------------------------------------+-----------------------------------------------------+



