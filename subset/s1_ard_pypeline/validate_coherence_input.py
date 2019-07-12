#!python
import argparse
import logging
import sys

import rasterio
from s1_ard_pypeline.utils import product_name, data_validation

"""
This script checks that the products to be fed into a coherence ard run are valid.

usage: validate_coherence_input.py [-h] -input INPUT -first FIRST -last LAST

Validate a geographic image

arguments:
  -h, --help    show this help message and exit
  -input INPUT  path to input files
  -first FIRST  the first image name to process (should not include the file
                extension)
  -last LAST    the last image name to process (should not include the file
                extension)
"""


def parse_args():
    parser = argparse.ArgumentParser(description='Validate the input images to the coherence process')

    parser.add_argument("-input", help="path to input files", required=True)
    parser.add_argument(
        "-first",
        help="the first image name to process (should not include the file extension)",
        required=True
    )
    parser.add_argument(
        "-last",
        help="the last image name to process (should not include the file extension)",
        required=True
    )

    _args = parser.parse_args()

    if not product_name.validate(_args.first):
        print(f"-first {_args.first} is not a valid S1 product name. Make sure it does not have a file extension")
        parser.print_usage()
        sys.exit(2)

    if not product_name.validate(_args.last):
        print(f"-last {_args.last} is not a valid S1 product name. Make sure it does not have a file extension")
        parser.print_usage()
        sys.exit(2)

    return _args


def ground_control_points_to_bounds(ground_control_points):
    """
    Work out the bounding box of an set of ground control points.

    :param ground_control_points: list of ground control points
    :return: bounding box of the area covered by the
    """
    min_x = ground_control_points[0].x
    min_y = ground_control_points[0].y
    max_x = ground_control_points[-1].x
    max_y = ground_control_points[-1].y

    return rasterio.coords.BoundingBox(min_x, min_y, max_x, max_y)


def validate_single_file(src, _product):
    """
    Check a single S1 input file
    :param src: rasterio readable file
    :param _product: a product dictionary
    :return: True if the data is ok. False otherwise.
    """

    ok = True
    if not (src.gcps and src.gcps[0]):
        logging.error(f"Ground control points seem to be missing.")
        ok = False
    polarisations = _product.polarisations()
    if src.count != len(polarisations):
        logging.error(f"Unexpected number of bands. Expected {len(polarisations)} found {src.count}")
        ok = False

    count = 0
    total_bounds = None
    for sub_data in src.subdatasets:
        if sub_data.lower()[-2:] in polarisations:
            count = count + 1
            src = rasterio.open(sub_data)
            if not data_validation.check_data(src):
                ok = False

            bounds = ground_control_points_to_bounds(src.gcps[0])
            total_bounds = data_validation.combine_bounds(total_bounds, bounds)
    if count != (3 * len(polarisations)):
        logging.error(
            f"Unexpected number of swaths and polarisations. Expected {(3 * len(polarisations))} found {count}"
        )
        ok = False

    return ok, total_bounds


def validate_input(path, first, last):
    """
    This checks that an input image is in the expected format and contains some data.

    This will perform all the checks even if the first check fails. This is so the user is told all the things that
    are wrong with the images.

    :param path: path to the folder containing the input zip files
    :param first: name of the first product
    :param last: name of the last product
    :return: True if the products points to valid input products.
    """
    product_first = product_name.S1Product(first)
    product_last = product_name.S1Product(last)

    path_first = product_name.zip_manifest_path(path, product_first)
    path_last = product_name.zip_manifest_path(path, product_last)
    ok = True

    # Check they are the same satellite
    if product_first.satellite != product_last.satellite:
        logging.error("The two images are from different satellites.")
        ok = False

    # Check the product dates
    if 24 > (product_last.start_timestamp() - product_first.start_timestamp()).days < 12:
        logging.error("The two images are less than 12 days apart or more than 24 days apart.")
        ok = False

    # Check orbit numbers are from the same relative orbit
    if product_first.relative_orbit() != product_last.relative_orbit():
        logging.error("The two images are from different relative orbits.")
        ok = False

    # set custom logging here to info because gdal and rasterio are very chatty at debug level
    with rasterio.Env():
        src_first = rasterio.open(path_first)
        src_last = rasterio.open(path_last)
        ok_first, bounds_first = validate_single_file(src_first, product_first)
        if not ok_first:
            logging.error("First image was invalid.")
            ok = False

        ok_last, bounds_last = validate_single_file(src_last, product_last)
        if not ok_last:
            logging.error("Last image was invalid.")
            ok = False

        # Now check that the images overlap.
        # Sum up the bounds from the sub images to get the actual bounds.
        if not data_validation.overlap(bounds_first, bounds_last):
            logging.error(f"Images do not overlap.")
            logging.error(f"first wkt: {data_validation.bounding_box_to_wkt(bounds_first)}")
            logging.error(f"last wkt: {data_validation.bounding_box_to_wkt(bounds_last)}")
            ok = False
        else:
            # TODO: validate that they overlap by at least 50%
            pass
    return ok


if __name__ == '__main__':

    args = parse_args()

    if not validate_input(args.input, args.first, args.last):
        logging.error("Problems found with input images")
        sys.exit(2)
    else:
        logging.info("No problems found with input images")
