"""
the product_name package contains a few tools to deal with Sentinel product names
"""
from datetime import datetime
from os import path


class S1Product(object):
    """
    S1Product contains details and helper functions for handling S1 product names.
    """

    def __init__(self, name):
        self.product_name = name
        self.satellite = name[0:3]
        self.SAR_mode = name[4:6]
        self.product_type = name[7:16]
        self.start_date = name[17:25]
        self.start_time = name[26:32]
        self.stop_date = name[33:41]
        self.stop_time = name[42:48]
        self.orbit = name[49:55]
        self.image = name[56:62]

    def relative_orbit(self):
        """
        Calculate the relative orbit number from a product

        :return: int of the orbit number. between 0 and 175
        """
        return int(self.orbit) % 175

    def polarisations(self):
        """
        return the polarisations available in this product.

        :return: a list of polarisation codes available in this file.
        """
        if self.product_type.endswith("SV"):
            return ["vv"]
        elif self.product_type.endswith("DV"):
            return ["vh", "vv"]
        elif self.product_type.endswith("SH"):
            return ["hh"]
        elif self.product_type.endswith("DH"):
            return ["hh", "hv"]

    def start_timestamp(self):
        return datetime.strptime(f"{self.start_date}T{self.start_time}", "%Y%m%dT%H%M%S")

    def stop_timestamp(self):
        return datetime.strptime(f"{self.stop_date}T{self.stop_time}", "%Y%m%dT%H%M%S")

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, S1Product):
            return NotImplemented

        return self.product_name == o.product_name and \
               self.SAR_mode == o.SAR_mode and \
               self.product_type == o.product_type and \
               self.start_date == o.start_date and \
               self.start_time == o.start_time and \
               self.stop_date == o.stop_date and \
               self.stop_time == o.stop_time and \
               self.orbit == o.orbit and \
               self.image == o.image


def validate(name):
    """
    Check that an given product name is as expected.

    :param name: the product name to check
    :return: true if the product name is valid.
    """
    # TODO: make this more comprehensive. Validate we have the right parts and so on.
    return not (name.endswith(".zip") or name.endswith(".SAFE") or len(name) != 67 or "SLC" not in name)


def common_polarisations(products):
    """
    given a collection of products return the polarisations that can be found in all of them.
    :param products: a collection of products
    :return: list of polarisations that can be found in all of them
    """

    result_set = set(products[0].polarisations())
    for p in products[1:]:
        result_set = result_set & set(p.polarisations())
    return list(result_set)


def manifest_path(directory, product):
    """
    Return the path to the manifest file of a product.

    :param directory: where the product has been unzipped
    :param product: the name of the product.
    :return: string with the full path to the manifest.safe file.
    """

    return path.join(unzipped_path(directory, product), "manifest.safe")


def zip_path(directory, product):
    """
    Create the path for a product zip in a directory
    :param directory: where the product zip is expected to be
    :param product: the product we are looking for
    :return: string representation of the zip input.
    """
    return _prefix_product_path(directory, product, "zip")


def unzipped_path(directory, product):
    """
    Create the path to the unzipped product folder

    :param directory:  working directory
    :param product: the product we are looking for
    :return: string representation of the path to the unzipped directory.
    """
    return _prefix_product_path(directory, product, "SAFE")


def _prefix_product_path(directory, product, extension):
    return path.join(directory, f"{product.product_name}.{extension}")


def zip_manifest_path(directory, product):
    """
    create a path sutible for gdal or rasterio to access a safe product inside of a zip file.
    :param directory: path to the zip file
    :param product: product information
    :return: a string point to the manifest file inside the product zip file.
    """
    base_path = zip_path(directory, product)
    return f"zip+file://{base_path}!{product.product_name}.SAFE/manifest.safe"


def create_result_name(directory, products, polarisation, process, file_type):
    """
    To make the outputs of several pipelines unified it is helpful to have a single place generating filenames.
    This is that place.

    :param directory: parent directory
    :param products: products that are included in this image
    :param polarisation: polarisation of the result image
    :param process: name of the process used to create this image
    :param file_type: type of output file.
    :return: string representing the required file path.
    """
    if not file_type.startswith("."):
        file_type = "." + file_type

    if isinstance(products, list):
        dates = ""
        for product in products:
            dates = dates + f"{product.start_date}T{product.start_time}_"
    else:
        dates = f"{products.start_date}T{products.start_time}_"

    filename = f"S1_{dates}{process}_{polarisation}{file_type}"

    return path.join(directory, filename)


def create_s1_swath_dict(key_prefix, key_start, key_step, work_dir, product, polarisation, process, file_type):
    """
    Create a dictionary of keys and values for each swatch of a sentinel 1 product.

    :param key_prefix: prefix to put on the front of the key
    :param key_start: number to start the key index from.
    :param key_step: number increment keys index
    :param work_dir: the working directory to find the product in.
    :param product: the product we are working on.
    :param polarisation: the polarisation
    :param process: the file process identifier
    :param file_type: result file type.
    :return: dict of keys to paths for each swath
    """
    if isinstance(polarisation, list):
        return dict(map(
            lambda p: (
                f"{key_prefix}{p[0] + key_start}",
                create_result_name(work_dir, product, p[1][0], f"{process}_iw{p[1][1] + 1}", file_type)
            ),
            enumerate([(x, y) for y in range(0, 3) for x in polarisation])
        ))
    else:
        return dict(map(
            lambda i: (
                f"{key_prefix}{(i * key_step) + key_start}",
                create_result_name(work_dir, product, polarisation, f"{process}_iw{i + 1}", file_type)
            ),
            # Think the number of swaths in a S1 image is fixed enough for this to work.
            # If not make a config value or parameter
            range(0, 3)
        ))


def create_polarisation_names(directory, products, process, file_type):
    """
    Return a tuple of two file names for each of vh and vv polarisations.
    :param directory: parent directory
    :param products: products that are included in this image
    :param process: name of the process used to create this image
    :param file_type: type of output file.
    :return: tuple of file names.
    """
    if isinstance(products, list):
        common = common_polarisations(products)
    else:
        common = products.polarisations()
    return [create_result_name(directory, products, polarisation, process, file_type) for polarisation in common]
