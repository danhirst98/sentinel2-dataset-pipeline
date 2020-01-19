#!python
import argparse
import logging
import sys

from s1_ard_pypeline import get_config
from s1_ard_pypeline.ard import ard
from s1_ard_pypeline.utils import product_name
from s1_ard_pypeline.utils.product_name import create_result_name

"""
A script to ard the ard coherence process. 

usage: run_coherence.py [-h] -input INPUT -output OUTPUT -first FIRST -last
                        LAST [-clean CLEAN]

Run a S1 ARD process for two images

optional arguments:
  -h, --help      show this help message and exit
  -input INPUT    path to input files
  -output OUTPUT  path to output files
  -first FIRST    the first image name to process (should not include the file
                  extension)
  -last LAST      the last image name to process (should not include the file
                  extension)
  -clean CLEAN    should intermediate files be cleaned up as we process

"""


def parse_args():
    parser = argparse.ArgumentParser(description='Run a S1 Coherence ARD process for two images')
    parser.add_argument("-input", help="path to input files", required=True)
    parser.add_argument("-output", help="path to output files", required=True)
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
    parser.add_argument("-clean", type=bool, default=True, help="should intermediate files be cleaned up as we process")
    parser.add_argument("-gzip", type=bool, default=True, help="should the result file be gzip compressed")

    _args = parser.parse_args()

    if not product_name.validate(_args.first):
        print(f"-first {_args.first} is not a valid product name. Make sure it does not have a file extension")
        parser.print_usage()
        sys.exit(2)

    if not product_name.validate(_args.last):
        print(f"-last {_args.last} is not a valid product name. Make sure it does not have a file extension")
        parser.print_usage()
        sys.exit(2)

    return _args


class CoherenceChain:

    def __init__(self, _input_dir, _output_dir, _first_product, _last_product, _gzip, _clean):
        self.input_dir = _input_dir
        self.working_dir = get_config("Dirs", "working")
        self.output_dir = _output_dir
        self.gzip = _gzip
        self.clean = _clean
        self.product_first = _first_product
        self.product_last = _last_product
        self.products = [self.product_first, self.product_last]

    def name(self):
        return f"Coherence for {self.product_first.product_name} and {self.product_last.product_name}"

    def final_outputs(self):
        polarisations = product_name.create_polarisation_names(
            self.output_dir,
            self.products,
            "Orb_stack_Ifg_Deb_mrg_DInSAR_Flt_TC",
            ".tif",
        )
        if self.gzip:
            return [p + ".gz" for p in polarisations]
        else:
            return polarisations

    def build_chain(self):
        # create the chain of processing steps.

        # Get the ones in both of them as we can only generate coherence for polarisations that are in both images.
        common_polarisations = product_name.common_polarisations(self.products)
        logging.info(f"found {len(common_polarisations)} common polarisations {common_polarisations}")
        # initial chain set up and the first step of the coherence process
        chain = [
            # Unzip the products
            list(map(lambda p: self.unzip(p), self.products)),
            # split the products in to swaths and polarisations
            list(map(
                lambda p: self.stage1(p[0], p[1]),
                [
                    (p, polarisation)
                    for p in self.products
                    for polarisation in common_polarisations
                ]
            )),
            # calculate the coherence between first and last for each of the six swaths and polarisations
            list(map(
                lambda p: self.stage2(p[0], p[1]),
                [
                    (sub_swath, polarisation)
                    for sub_swath in ['iw1', 'iw2', 'iw3']
                    for polarisation in common_polarisations
                ]
            )),
            # Join up the three swaths into a single image for each polarisation
            list(map(lambda polarisation: self.stage3(polarisation), common_polarisations)),
            # Terrain correction, filtering and finalisation of each polarisation
            list(map(lambda polarisation: self.stage4(polarisation), common_polarisations)),
        ]

        return chain

    def _create_dim_name(self, _polarisation, _prefix, _products=None):
        if not _products:
            _products = self.products
        return create_result_name(self.working_dir, _products, _polarisation, _prefix, ".dim")

    def unzip(self, product):
        return lambda: ard.unzip_product(
            product_name.zip_path(self.input_dir, product),
            self.working_dir,
        )

    def stage1(self, product, polarisation):
        """
        Pull a product into three sub swaths for the provided polarisations.

        For dual polarisation (VV+VH) this stage should be called twice for the same image. Once for each polarisation
        :param product: the product to split into swathes
        :param polarisation:  the polarisation to select.
        :return: a lambda that will do the work.
        """
        return lambda: ard.gpt(
            ard.graph("S1_coherence_stage1"),
            {
                **product_name.create_s1_swath_dict(
                    "target", 1, 1,
                    self.working_dir, product, polarisation, "Orb", "dim"
                ),
                "input": product_name.manifest_path(self.working_dir, product),
                "polarisation": polarisation.upper(),
            }
        )

    def stage2(self, _sub_swath, _polarisation):
        result = [
            lambda: ard.gpt(
                ard.graph("S1_coherence_stage2"),
                {
                    "input1": self._create_dim_name(
                        _polarisation,
                        f"Orb_{_sub_swath}",
                        self.product_first,
                    ),
                    "input2": self._create_dim_name(
                        _polarisation,
                        f"Orb_{_sub_swath}",
                        self.product_last,
                    ),
                    "target": self._create_dim_name(
                        _polarisation,
                        f"Orb_stack_Ifg_Deb_{_sub_swath}",
                    )
                }
            )
        ]

        if self.clean:
            result.append(lambda: ard.delete_dim(
                self._create_dim_name(_polarisation, f"Orb_{_sub_swath}", self.products[0])
            ))
            result.append(lambda: ard.delete_dim(
                self._create_dim_name(_polarisation, f"Orb_{_sub_swath}", self.products[1])
            ))

        return result

    def stage3(self, _polarisation):
        result = [lambda: ard.gpt(
            ard.graph("S1_coherence_stage3"),
            {
                **product_name.create_s1_swath_dict(
                    "input", 1, 1,
                    self.working_dir, self.products, _polarisation, "Orb_stack_Ifg_Deb", "dim"
                ),
                "target": self._create_dim_name(_polarisation, "Orb_stack_Ifg_Deb_mrg"),
            }
        )]
        if self.clean:
            result.append(lambda: ard.delete_dim(
                self._create_dim_name(_polarisation, "Orb_stack_Ifg_Deb_iw1")
            ))
            result.append(lambda: ard.delete_dim(
                self._create_dim_name(_polarisation, "Orb_stack_Ifg_Deb_iw2")
            ))
            result.append(lambda: ard.delete_dim(
                self._create_dim_name(_polarisation, "Orb_stack_Ifg_Deb_iw3")
            ))
        return result

    def stage4(self, _polarisation):
        result = [lambda: ard.gpt(
            ard.graph("S1_coherence_stage4"),
            {
                "input": self._create_dim_name(
                    _polarisation,
                    "Orb_stack_Ifg_Deb_mrg"
                ),
                "target": self._create_dim_name(
                    _polarisation,
                    "Orb_stack_Ifg_Deb_mrg_DInSAR_Flt_TC"
                ),
            }
        )]
        if self.clean:
            result.append(lambda: ard.delete_dim(
                self._create_dim_name(_polarisation, "Orb_stack_Ifg_Deb_mrg")
            ))

        # convert the final results to geotif, compress and then we are finally done!
        result.append(lambda: ard.convert_to_tif(
            self._create_dim_name(
                _polarisation,
                "Orb_stack_Ifg_Deb_mrg_DInSAR_Flt_TC",
            ),
            create_result_name(
                self.output_dir,
                self.products,
                _polarisation,
                "Orb_stack_Ifg_Deb_mrg_DInSAR_Flt_TC",
                ".tif"
            )
        ))

        if self.clean:
            result.append(lambda: ard.delete_dim(self._create_dim_name(
                _polarisation,
                "Orb_stack_Ifg_Deb_mrg_DInSAR_Flt_TC",
            )))
        if self.gzip:
            result.append(lambda: ard.gzip_file(
                create_result_name(
                    self.output_dir,
                    self.products,
                    _polarisation,
                    "Orb_stack_Ifg_Deb_mrg_DInSAR_Flt_TC",
                    ".tif"
                ),
                create_result_name(
                    self.output_dir,
                    self.products,
                    _polarisation,
                    "Orb_stack_Ifg_Deb_mrg_DInSAR_Flt_TC",
                    ".tif.gz"
                ),
            ))

            if self.clean:
                result.append(lambda: ard.delete_file(create_result_name(
                    self.output_dir,
                    self.products,
                    _polarisation,
                    "Orb_stack_Ifg_Deb_mrg_DInSAR_Flt_TC",
                    ".tif"
                )))
        return result


if __name__ == "__main__":
    args = parse_args()
    first_product = product_name.S1Product(args.first)
    last_product = product_name.S1Product(args.last)
    coherence = CoherenceChain(args.input, args.output, args.gzip, args.clean, first_product, last_product)
    ard.process_chain(coherence.build_chain(), coherence.name())
