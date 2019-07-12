#!python
import argparse
import sys

from s1_ard_pypeline import get_config
from s1_ard_pypeline.ard import ard
from s1_ard_pypeline.utils import product_name


def parse_args():
    parser = argparse.ArgumentParser(description='Run a S1 Intensity ARD process for two images')
    parser.add_argument("-input", help="path to input files", required=True)
    parser.add_argument("-output", help="path to output files", required=True)
    parser.add_argument(
        "-product",
        help="the image name to process (should not include the file extension)",
        required=True
    )
    parser.add_argument("-clean", type=bool, default=True, help="should intermediate files be cleaned up as we process")
    parser.add_argument("-gzip", type=bool, default=True, help="should the result file be gzip compressed")

    _args = parser.parse_args()

    if not product_name.validate(_args.product):
        print(f"-product {_args.product} is not a valid product name. Make sure it does not have a file extension")
        parser.print_usage()
        sys.exit(2)

    return _args


class IntensityChain:

    def __init__(self, _input_dir, _output_dir, _product, _gzip, _clean):
        self.input_dir = _input_dir
        self.working_dir = get_config("Dirs", "working")
        self.output_dir = _output_dir
        self.product = _product
        self.gzip = _gzip
        self.clean = _clean

    def name(self):
        return f"Intensity for {self.product.product_name}"

    def final_outputs(self):
        if self.gzip:
            return self._output(".tif.gz")
        else:
            return self._output(".tif")

    def build_chain(self):
        # create the chain of processing steps.

        stage1_output = product_name.create_result_name(self.working_dir, self.product, "", "Orb_Cal_Deb_ML", ".dim")

        stage2_output_vh, stage2_output_vv = self._output(".dim")
        tif_vh, tif_vv = self._output(".tif")
        gzip_vh, gzip_vv = self._output(".tif.gz")

        # initial chain set up and the first step of the intensity process
        chain = [
            # Unzip the product
            lambda: ard.unzip_product(product_name.zip_path(self.input_dir, self.product), self.working_dir),
            # Run orbit corrections and debursting
            lambda: ard.gpt(
                ard.graph("S1_intensity_stage1"),
                {
                    "input": product_name.manifest_path(self.working_dir, self.product),
                    "target": stage1_output,
                }
            ),
            # Run speckle filtering, terrain corrections and db conversion
            lambda: ard.gpt(
                ard.graph("S1_intensity_stage2"),
                {
                    "input": stage1_output,
                    "target1": stage2_output_vh,
                    "target2": stage2_output_vv,
                }
            ),
            # Clean up the stage 1 outputs if requested to
            lambda: ard.delete_dim(stage1_output) if self.clean else None,
            # Convert results to tif
            lambda: ard.convert_to_tif(stage2_output_vh, tif_vh),
            lambda: ard.convert_to_tif(stage2_output_vv, tif_vv),
            # Clean up the stage2 dim files if requested
            lambda: ard.delete_dim(stage2_output_vh) if self.clean else None,
            lambda: ard.delete_dim(stage2_output_vv) if self.clean else None,
            # Gzip the results if requested
            lambda: ard.gzip_file(tif_vh, gzip_vh) if self.gzip else None,
            lambda: ard.gzip_file(tif_vv, gzip_vv) if self.gzip else None,
            # Clean up the tif files that have been compressed if requested.
            lambda: ard.delete_file(tif_vh) if self.gzip and self.clean else None,
            lambda: ard.delete_file(tif_vv) if self.gzip and self.clean else None,
        ]

        return chain

    def _output(self, extension):
        return product_name.create_polarisation_names(
            self.output_dir,
            self.product,
            "Orb_Cal_Deb_ML_Spk_TC_dB",
            extension
        )


if __name__ == "__main__":
    args = parse_args()
    product = product_name.S1Product(args.product)
    intensity = IntensityChain(args.input, args.output, product, args.gzip, args.clean)
    process = intensity.build_chain()
    ard.process_chain(process, intensity.name())
