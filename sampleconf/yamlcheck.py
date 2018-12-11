#!/usr/bin/env python3
"""Simple YAML syntax checker
"""

import sys
import argparse

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


__author__ = "Andreas Wilm"
__email__ = "wilma@gis.a-star.edu.sg"
__copyright__ = "2018 Genome Institute of Singapore"
__license__ = "The MIT License (MIT)"


def parse(yamlfile, printdata=True):
    """simply parse yaml file and optionally print its content
    """

    with open(yamlfile) as fh:
        data = load(fh, Loader=Loader)

    if printdata:
        if isinstance(data, dict):
            print("dict:")
            for k, v in data.items():
                print(" ", k, v)
        else:
            print("list:")
            for v in data:
                print(" ", type(v), v)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-p', '--print', action='store_true')
    parser.add_argument('yamlfiles', nargs='*')
    args = parser.parse_args()

    if not args.yamlfiles:
        parser.print_help(sys.stderr)
        sys.exit(1)

    for y in args.yamlfiles:
        parse(y, printdata=args.print)
        print("OK: {}".format(y))
