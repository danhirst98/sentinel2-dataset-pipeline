#!python
import argparse
import logging
import sys

import numpy as np
import rasterio
from s1_ard_pypeline.utils import data_validation

"""
This checks that a geographic image result from the run tools is reasonably sensible. 

The file must contain some data.
The file must not be at the origin of the coordinate system.
The file must not contain a single value.
The number of bands must match the expected number of bands.

usage: validate_result.py [-h] -input INPUT [-bands BANDS]
"""


def parse_args():
    parser = argparse.ArgumentParser(description='Validate a geographic image')
    parser.add_argument("-input", help="path to input file", required=True)
    # TODO: should this be an argument? All the results we generate have one band.
    # Think leaving as a default will allow future use easier.
    parser.add_argument("-bands", type=int, help="the number of expected bands", default=1)
    return parser.parse_args()


def validate_image(path):
    """
    Checks an image to make sure that it is sensible.

    Note: This does not check that the actual data is correct apart from not being all one value.

    :param path: location on disk of the image to check
    :return: true if the image is mostly sensible.
    """
    problems = False
    # Rasterio env is required to make sure that the gdal bindings are setup correctly.
    with rasterio.Env():
        try:
            dataset = rasterio.open(path)
        except Exception as e:
            logging.error("Could not open dataset", e)
            return False

        # Check the bands have sort of sensible values
        if dataset.count != args.bands:
            logging.error(f"There is not the required number of bands. Expected {args.bands} found {dataset.count}")
            problems = True

        if not data_validation.check_data(dataset):
            problems = True

        # Validate coordinate box doesn't cover the origin.
        # Also make sure that it has valid coordinates.
        if dataset.transform:
            top_left = dataset.transform * (0, 0)
            bottom_right = dataset.transform * (dataset.width, dataset.height)
            if np.sign(bottom_right[0]) != np.sign(top_left[0]) and np.sign(bottom_right[1]) != np.sign(top_left[1]):
                logging.error(f"Data set appears to be over the origin of the coordinate space.")
                problems = True
        else:
            logging.error(f"Dataset transform is missing.")
            problems = True
    return not problems  # return true if the image is valid


if __name__ == '__main__':

    args = parse_args()
    if not validate_image(args.input):
        logging.error("Found problems with the data.")
        sys.exit(2)
    else:
        logging.info("No problems found.")
