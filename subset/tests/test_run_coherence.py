import os
import unittest

from s1_ard_pypeline import _config
from s1_ard_pypeline.run_coherence import CoherenceChain
from s1_ard_pypeline.utils import product_name


class TestRunCoherence(unittest.TestCase):

    def test_create_dim_name(self):
        first_product = product_name.S1Product("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052")
        last_product = product_name.S1Product("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052")

        _config.set("Dirs", "working", "/foo/bar")

        coherence_chain = CoherenceChain("test_input", "test_output", first_product, last_product, True, True)

        result = coherence_chain._create_dim_name("vh", "test")

        self.assertEqual(f"/foo/bar{os.sep}S1_20170502T231339_20170502T231339_test_vh.dim", result)
