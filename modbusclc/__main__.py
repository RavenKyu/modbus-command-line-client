import os
import argparse
import pathlib
from cliparse import run

dir_path = os.path.dirname(os.path.realpath(__file__))

cli_file = pathlib.Path(dir_path) / pathlib.Path('cli.py')
parser = argparse.ArgumentParser()
parser.add_argument('--cli', type=str, default=str(cli_file))
cli = parser.parse_args().cli
run(cli)

