# ModbusCLC (Modbus Command Line Client)

__ModbusCLC__ is simple but useful.

[![asciicast](https://asciinema.org/a/3LWW3pORg7ze92aTy3medeWPS.svg)](https://asciinema.org/a/3LWW3pORg7ze92aTy3medeWPS)

## Concept
* Free
* Showing beautify

## Features
* User defined data template about data types 

## Installation 
```bash
$ pip install modbusclc
```
or
```bash
$ git clone https://github.com/RavenKyu/modbus-command-line-client.git
$ cd modbus-command-line-client
$ python setup.py install
```

### Running 
```bash
$ python -m modbusclc
```

### Running Dummy Modbus Server with docker
If you use docker, you can try it like below. 

#### Build
```bash
$ docker build -f dummy-modbus-server/Dockerfile -t dummy-modbus-server:latest .
``` 
or
```bash
$ docker-compose build dummy-modbus-server
```
#### Running
Dummy-Modbus-Server Start ...
```bash
$ docker run --rm -d -p 502:502 dummy-modbus-server:latest
```
or
```bash
$ docker-compose run --rm dummy-modbus-server
```

### Connect to Dummy Server with ModbusCLC
`ModbusCLC` is set default the address as localhost and port as 502.

```bash
python -m modbusclc
```

---
## Sample
There is a simple sample data you can read with `read holding register`. (version `v0.3.0`)
 
### Things you can do
#### Help
All most each menu can show its help message or usage. 
```bash
(Cmd) help

Documented commands (type help <topic>):
========================================
exit  help  read_holding_register
```

#### Read Holding Register
```bash

(Cmd) read_holding_register -h
usage:  read_holding_register [-h] [-t TEMPLATE] [-a ADDRESS] [-p PORT] [-i UNIT_ID] [-f FIRST_REGISTER] [-c COUNT]

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATE, --template TEMPLATE
                        template name
  -a ADDRESS, --address ADDRESS
                        host address
  -p PORT, --port PORT  port
  -i UNIT_ID, --unit-id UNIT_ID
                        unit id
  -f FIRST_REGISTER, --first-register FIRST_REGISTER
                        first register address
  -c COUNT, --count COUNT
                        number of registers

(Cmd) read_holding_register -alocalhost -p502 -c20 -tsample
2020-10-04 23:39:00 | request  | 192.168.200.124 > 00 00 00 14
2020-10-04 23:39:00 | respose  | localhost:502   > 28 55 6e 69 74 32 33 2d 41 ff ff fc 19 ff ff ff fa 80 00 00 00 43 7e e2 c6 42 0a c3 26 42 7d 7a eb 41 07 0e 38 ff ff 00 07

data type      reg  bytes                value               note
-----------  -----  -------------------  ------------------  -----------------------
64b sting    40001  556e 6974 3233 2d41  Unit23-A            text label
16b uint     40005  ffff                 65535               16 bit unsigned integer
16b int      40006  fc19                 -999                16 bit integer
32b uint     40007  ffff fffa            4294967290          32 bit unsigned integer
32b int      40009  8000 0000            -2147483648         32 bit integer
32b float    40011  437e e2c6            254.88583374023438  32 bit float
32b float    40013  420a c326            34.690574645996094  32 bit float
32b float    40015  427d 7aeb            63.37003707885742   32 bit float
32b float    40017  4107 0e38            8.440971374511719   32 bit float
8b uint      40019  ff                   255                 8 bit unsigned int
8b int       40019  ff                   -1                  8 bit int
8 bits       40020  00                   0000000             8 bits Boolean
8 bits       40020  07                   0000111             8 bits Boolean
(Cmd)
```

## Template
`Template` is very useful function of this program. The file format is yaml.
*Template file name is always `templates.yml`*

This is the sample template for data above. 
```yaml
---
sample:
  - note: text label
    data_type: B64_STRING
  - note: 16 bit unsigned integer
    data_type: B16_UINT
  - note: 16 bit integer
    data_type: B16_INT
  - note: 32 bit unsigned integer
    data_type: B32_UINT
  - note: 32 bit integer
    data_type: B32_INT
  - note: 32 bit float
    data_type: B32_FLOAT
  - note: 32 bit float
    data_type: B32_FLOAT
  - note: 32 bit float
    data_type: B32_FLOAT
  - note: 32 bit float
    data_type: B32_FLOAT
  - note: 8 bit unsigned int
    data_type: B8_UINT
  - note: 8 bit int
    data_type: B8_INT
  - note: 8 bits Boolean
    data_type: BIT8
  - note: 8 bits Boolean
    data_type: BIT8
```


