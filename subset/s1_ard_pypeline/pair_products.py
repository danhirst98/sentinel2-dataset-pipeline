#!python
import argparse
import logging
from datetime import timedelta
from os import path

from s1_ard_pypeline.utils import product_name

"""
This script pairs up a list of S1 products to make a set of inputs for the batch_run tool

This script can also create a split output which will round-robbin output to a set of files.
This can either be a number, or a list of names. Helpful for routing to the correct user. 

usage: pair_products.py [-h] -input INPUT -output OUTPUT [-splits SPLITS]
                        [-splitlist SPLITLIST]

Pair up a list of S1 products ready for processing by batch_run.py

optional arguments:
  -h, --help            show this help message and exit
  -input INPUT          path to input file
  -output OUTPUT        path to output file
  -splits SPLITS        number of parts to split the output file into
  -splitlist SPLITLIST  path to a file of split extensions to use

"""


def parse_args():
    parser = argparse.ArgumentParser(description='Pair up a list of S1 products ready for processing by batch_run.py')
    parser.add_argument("-input", help="path to input file", required=True)
    parser.add_argument("-output", help="path to output file", required=True)
    parser.add_argument("-splits", help="number of parts to split the output file into", required=False, default=1)
    parser.add_argument("-splitlist", help="path to a file of split extensions to use", required=False, default="")

    _args = parser.parse_args()
    return _args


def read_product_list(_file):
    _result = []
    with open(_file, 'r') as f:
        for line in f:
            trimmed = line.strip()
            if line and product_name.validate(trimmed):
                _result.append(product_name.S1Product(trimmed))
    return _result


def pair_products(_products):
    # group up by orbit.
    _by_orbit = {}
    for p in _products:
        _by_orbit.setdefault(p.relative_orbit(), []).append(p)

    _result = []

    # for each orbit
    for k, v in _by_orbit.items():
        sorted_products = sorted(v, key=lambda _p: _p.start_timestamp())

        orbit_start = len(_result)
        for i, pa in enumerate(sorted_products):
            # because the products are sorted the one that overlaps should be soon after
            for pb in sorted_products[i + 1:]:
                # if the images are not between 12 and 24 days apart then we should not process it.
                # Due to orbital mechanics images in the same orbit cant be in between but they might be outside by a
                # few seconds, this gives us a buffer.
                duration = (pb.start_timestamp() - pa.start_timestamp())
                if timedelta(days=12, seconds=-30) > duration or duration > timedelta(days=24):
                    continue

                # the two products overlap
                if pa.start_time <= pb.start_time < pa.stop_time or pb.start_time < pa.stop_time <= pb.stop_time or \
                    pb.start_time <= pa.start_time < pb.stop_time or pa.start_time < pb.stop_time <= pa.stop_time:
                    _result.append((pa, pb))
                    break

        # if we have some how created a loop remove the last entry to break it.
        if len(_result) >= 2 and \
            orbit_start < len(_result) - 1 and \
            _result[orbit_start][0].product_name == _result[-1][1].product_name:
            _result = _result[:-1]

    return _result


def write_results(_pairs, _output, _parts, _split_list):
    """
    Write out the pairs evenly across multiple files.

    If _split_list is defined it will be used instead of the _parts count

    :param _pairs: list of pairs to write out
    :param _output: the file name to write out to. This will have the number or name of the chunk appended before the extension.
    :param _parts: number of parts to split the list into.
    :param _split_list: a path to a file containing a list of part names to split across
    :return: None
    """
    if _split_list:
        loop = load_split_list(_split_list)
    else:
        loop = range(_parts)

    output_files = []
    for i in loop:
        output_files.append(open(create_output_name(_output, i), 'w+'))

    count = 0
    # simple round robbin allocation
    for p in _pairs:
        output_files[count % len(loop)].write(f"{p[0].product_name}, {p[1].product_name}\n")
        count = count + 1

    for f in output_files:
        f.close()


def load_split_list(_split_list):
    _result = []
    with open(_split_list, 'r') as f:
        for line in f:
            _result.append(line.strip())
    return _result


def create_output_name(_output, _number):
    base, ext = path.splitext(_output)
    return f"{base}-{_number}{ext}"


if __name__ == '__main__':
    args = parse_args()
    products = read_product_list(args.input)

    result = pair_products(products)

    write_results(result, args.output, int(args.splits), args.splitlist)
    logging.info(f"paired {len(products)} entries into {len(result)} pairs")
