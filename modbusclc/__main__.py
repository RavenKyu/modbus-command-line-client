import os
import argparse
import pathlib
from cliparse import run
from modbusclc import Config, set_prompt


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    cli_file = pathlib.Path(dir_path) / pathlib.Path('cli.py')
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', type=str, default=str(cli_file))
    parser.add_argument('-a', '--address', type=str, )
    parser.add_argument('-p', '--port', type=int)
    args = parser.parse_args()

    with Config() as conf:
        if args.address:
            conf['setting']['ip'] = args.address
        if args.port:
            conf['setting']['port'] = args.port
        set_prompt(**conf['setting'])

    cli = args.cli
    run(cli)


if __name__ == '__main__':
    main()
