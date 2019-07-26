#!python
"""
Take a list of file pairs and run them through the pipeline validating that they are good inputs.

usage: batch_run.py [-h] -input INPUT -output OUTPUT -targets TARGETS
"""
import argparse
import botocore
import logging
import os
import sys
from os import path
from s1_ard_pypeline import validate_coherence_input, get_config
from s1_ard_pypeline.ard import ard
from s1_ard_pypeline.run_coherence import CoherenceChain
from s1_ard_pypeline.run_intensity import IntensityChain
from s1_ard_pypeline.utils import product_name, s3_utils
from urljoin import urljoin


def parse_args():
    parser = argparse.ArgumentParser(description='Run a S1 ARD process for a list of images')
    parser.add_argument("-input", help="path to input files in s3", required=True)
    parser.add_argument("-output", help="path to output files in s3", required=True)
    parser.add_argument("-targets", help="csv file of products, one pair per line", required=True)

    parser.add_argument("-clean", type=bool, default=False,
                        help="should intermediate files be cleaned up as we process")
    parser.add_argument("-gzip", type=bool, default=True, help="should the result file be gzip compressed")

    _args = parser.parse_args()

    return _args


def split_product_line(_line):
    parts = _line.split(',')
    if len(parts) != 2:
        return "", ""
    return parts[0].strip(), parts[1].strip()


def download_product(_s3_client, _args, _download_dir, _product):
    download_url = urljoin.url_path_join(_args.input, f"{_product.product_name}.zip")
    target_name = product_name.zip_path(_download_dir, _product)
    if path.exists(target_name):
        logging.warning(f"Skipping download of {download_url} because it exists at {_download_dir} already.")
        logging.warning(f"If this is incorrect manually remove file {target_name}")
    else:
        logging.info(f"downloading {_product.product_name} from {download_url}")
        _s3_client.fetch_file(
            download_url,
            target_name,
        )
        logging.info(f"Done downloading {_product.product_name}")


def map_result_path_to_upload(_result_path, _args):
    return urljoin.url_path_join(_args.output, path.basename(_result_path))


def upload_to_s3(_chain_factory, _args, _s3_client):
    for i in _chain_factory.final_outputs():
        logging.info(f"uploading {i} to s3")
        _s3_client.put_file(i, map_result_path_to_upload(i, _args))
        logging.info(f"Done uploading {i} to s3")


def process_section(_chain_factory, _args, _s3_client):
    chain = _chain_factory.build_chain()
    ard.process_chain(chain, _chain_factory.name())
    upload_to_s3(_chain_factory, _args, _s3_client)


if __name__ == '__main__':
    args = parse_args()
    working_dir = get_config("Dirs", "working")
    download_dir = get_config("Dirs", "download")
    output_dir = get_config("Dirs", "outputs")

    # Make sure the required paths exist
    os.makedirs(working_dir, exist_ok=True)
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    s3_client = s3_utils.S3Utils()

    with open(args.targets) as f:
        count = 0
        for line in f:
            first, last = split_product_line(line)
            if not first or not last:
                continue

            if not product_name.validate(first) or not product_name.validate(last):
                logging.error(f"Could not validate {first} or {last} as a product name. Skipping")
                continue

            count = count + 1
            logging.info(f"Processing {first}, {last}")
            first_product = product_name.S1Product(first)
            last_product = product_name.S1Product(last)

            # TODO: make this sort its self out so if first and last are backwards it flips them round.
            try:
                download_product(s3_client, args, download_dir, first_product)
                download_product(s3_client, args, download_dir, last_product)
            except botocore.exceptions.ClientError as e:
                logging.error(f"could not fetch products from s3 {e}")
                continue

            if not validate_coherence_input.validate_input(download_dir, first, last):
                logging.info(f"inputs {first} {last} did not pass validation. Skipping")
                continue

            chains = [
                # Process the coherence work flow
                CoherenceChain(download_dir, output_dir, first_product, last_product, args.gzip, args.clean),
                # Process the intensity work flow for the first file
                IntensityChain(download_dir, output_dir, first_product, args.gzip, args.clean),
                # process the intensity work flow for the last file
                IntensityChain(download_dir, output_dir, last_product, args.gzip, args.clean),
            ]

            for c in chains:
                try:
                    process_section(c, args, s3_client)
                except ard.ProcessError as e:
                    logging.info(f"Processing failed. Aborting. {e}")
                    sys.exit(2)

            # Clean up the decompressed input files and the downloaded files
            if args.clean:
                ard.delete_dir(product_name.unzipped_path(working_dir, first_product))
                ard.delete_dir(product_name.unzipped_path(working_dir, last_product))

                ard.delete_file(product_name.zip_path(working_dir, first_product))
                ard.delete_file(product_name.zip_path(working_dir, last_product))

            logging.info(f"Completed {first}, {last}")

    logging.info(f"Completed {count} entries in {args.targets}")
