#!/usr/bin/env python3
"""Creates a sample onfig file (yaml) from a CSV file describing your samples
"""

#--- standard library imports
#
import sys
import os
import argparse
import logging
import csv
import hashlib
from itertools import groupby

#--- third-party imports
#
import yaml

#--- project specific imports
#
#/


__author__ = "Andreas Wilm"
__email__ = "wilma@gis.a-star.edu.sg"
__copyright__ = "2018 Genome Institute of Singapore"
__license__ = "The MIT License (MIT)"


MANDATORY_FIELDS = ['sample_id', 'fq1']
RECOMMENDED_FIELDS = ['fq2', 'run_id', 'flowcell_id', 'lane_id', 'library_id']


# only dump() and following do not automatically create aliases
yaml.Dumper.ignore_aliases = lambda *args: True


# global logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '[{asctime}] {levelname:8s} {filename} {message}', style='{'))
logger.addHandler(handler)


def key_for_readunit(ru_dict):
    """create a hash key for a read unit dict as used here
    """
    file_keys = ['fq1', 'fq2']
    m = hashlib.md5()
    for k, v in ru_dict.items():
        if k in file_keys:
            v = os.path.basename(v)
        m.update(v.encode())
    return m.hexdigest()[:8]


def parse_readunits_from_csv(csvfilename):
    """parse readunits from csv, one per row and return as list"""
    readunits = []
    with open(csvfilename) as csvfile:
        #dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=args.delimiter)
        #csvfile.seek(0)
        #csvreader = csv.DictReader(csvfile, dialect)
        csvreader = csv.DictReader(csvfile)
        header = csvreader.fieldnames
        logger.debug("parsed field names = %s", header)
        #skipheader = next(csvreader)
        for f in MANDATORY_FIELDS:
            assert f in header, ("Missing mandatory header/field: {}".format(f))
        for _, row in enumerate(csvreader):
            if not row:
                continue
            ru = dict()
            for f in MANDATORY_FIELDS:
                assert row[f], (f"Mandatory field {f} is empty")
                ru[f] = row[f].strip()
            for f in RECOMMENDED_FIELDS:
                if row[f]:
                    ru[f] = row[f].strip()
            for k, v in row.items():
                if k in MANDATORY_FIELDS or k in RECOMMENDED_FIELDS:
                    continue
                ru[k] = v
            logger.debug("parsed readunit %s: %s", key_for_readunit(ru), ru)
            readunits.append(ru)
    return readunits


def main():
    """main function
    """

    parser = argparse.ArgumentParser(description=__doc__)

    # generic args
    parser.add_argument('-i', "--csv", required=True,
                        help="CSV file with header describing your samples. Mandatory fields: {}."
                        " Auxiliary and reserverd: {}. Leave unknown fields empty.".format(
                            ', '.join(MANDATORY_FIELDS), ', '.join(RECOMMENDED_FIELDS)))
    parser.add_argument('-o', "--yaml", required=True,
                        help="Output config (yaml) file")
    parser.add_argument('-d', '--delimiter', default="\t",
                        help="Use this delimiter for CSV (default is <tab>)")
    parser.add_argument('-f', '--force-overwrite', action='store_true',
                        help="Force overwriting of existing file")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Increase verbosity")
    parser.add_argument('-q', '--quiet', action='count', default=0,
                        help="Decrease verbosity")

    args = parser.parse_args()

    # Repeateable -v and -q for setting logging level.
    # See https://www.reddit.com/r/Python/comments/3nctlm/what_python_tools_should_i_be_using_on_every/
    # and https://gist.github.com/andreas-wilm/b6031a84a33e652680d4
    # script -vv -> DEBUG
    # script -v -> INFO
    # script -> WARNING
    # script -q -> ERROR
    # script -qq -> CRITICAL
    # script -qqq -> no logging at all
    logger.setLevel(logging.WARN + 10*args.quiet - 10*args.verbose)

    if len(args.delimiter) != 1:
        logger.fatal("Delimiter needs to be exactly one character")
        sys.exit(1)
    if not os.path.exists(args.csv):
        logger.fatal("Input file %s does not exist", args.csv)
        sys.exit(1)
    if args.yaml != "-" and os.path.exists(args.yaml) and not args.force_overwrite:
        logger.fatal("Cowardly refusing to overwrite existing file %s", args.yaml)
        sys.exit(1)

    readunits = parse_readunits_from_csv(args.csv)

    # group readunits by sample
    samples = dict()
    readunits = sorted(readunits, key=lambda x: x['sample_id'])
    for sample_id, g_readunits in groupby(readunits, key=lambda x: x['sample_id']):
        samples[sample_id] = {'readunits': dict()}
        for ru in g_readunits:
            samples[sample_id]['readunits'][key_for_readunit(ru)] = ru
    logger.info("Parsed %d samples with a total of %d readunits",
                len(samples), len(readunits))
    #logger.debug(f"samples: {samples}")
    if args.yaml == "-":
        fh = sys.stdout
    else:
        fh = open(args.yaml, 'w')
    yaml.dump(dict(samples=samples), fh, default_flow_style=False)
    if fh != sys.stdout:
        fh.close()


if __name__ == "__main__":
    main()
