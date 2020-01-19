import os
import unittest

from s1_ard_pypeline.utils import product_name


class TestProductName(unittest.TestCase):
    def test_valid(self):
        expected = product_name.S1Product("")
        expected.product_name = "S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052"
        expected.satellite = "S1B"
        expected.SAR_mode = "IW"
        expected.product_type = "SLC__1SDV"
        expected.start_date = "20170502"
        expected.start_time = "231339"
        expected.stop_date = "20170502"
        expected.stop_time = "231407"
        expected.orbit = "005426"
        expected.image = "009835"

        self.assertEqual(
            product_name.S1Product("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052"),
            expected
        )


def test_empty(self):
    expected = product_name.S1Product("")
    expected.product_name = ""
    expected.satellite = ""
    expected.SAR_mode = ""
    expected.product_type = ""
    expected.start_date = ""
    expected.start_time = ""
    expected.stop_date = ""
    expected.stop_time = ""
    expected.orbit = ""
    expected.image = ""

    self.assertEqual(product_name.S1Product(""), expected)


def test_mangled(self):
    expected = product_name.S1Product("")
    expected.product_name = "fgsfdgsdg"
    expected.satellite = "fgs"
    expected.SAR_mode = "dg"
    expected.product_type = "dg"
    expected.start_date = ""
    expected.start_time = ""
    expected.stop_date = ""
    expected.stop_time = ""
    expected.orbit = ""
    expected.image = ""

    res = product_name.S1Product("fgsfdgsdg")
    self.assertEqual(res, expected)


def test_validate_happy(self):
    self.assertTrue(product_name.validate("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052"))


def test_validate_unhappy(self):
    self.assertFalse(
        product_name.validate("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052.zip")
    )
    self.assertFalse(
        product_name.validate("S1B_IW_SLC__1SDV_20170502T23133")
    )


def test_create_result_name(self):
    self.assertEqual(
        f"/foo/bar{os.sep}S1_20170502T231339_test_vh.tif",
        product_name.create_result_name(
            "/foo/bar",
            product_name.S1Product("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052"),
            "vh",
            "test",
            "tif"
        ),
    )


def test_create_s1_swath_dict(self):
    product = product_name.S1Product("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052")

    result = product_name.create_s1_swath_dict("input", 2, 2, "/data1/pipeline", product, "vv", "Orb", "dim")
    self.assertEqual(
        {
            "input2": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw1_vv.dim",
            "input4": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw2_vv.dim",
            "input6": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw3_vv.dim",
        },
        result
    )

    result = product_name.create_s1_swath_dict("input", 1, 2, "/data1/pipeline", product, "vh", "Orb", "dim")
    self.assertEqual(
        {
            "input1": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw1_vh.dim",
            "input3": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw2_vh.dim",
            "input5": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw3_vh.dim",
        },
        result
    )


def test_create_s1_swath_dict_list_of_polarisations(self):
    product = product_name.S1Product("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052")
    result = product_name.create_s1_swath_dict(
        "input",
        1,
        2,  # in this mode it shouldn't make any difference
        "/data1/pipeline",
        product,
        ["vh", "vv"],
        "Orb",
        "dim"
    )
    self.assertEqual(
        {
            "input1": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw1_vh.dim",
            "input2": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw1_vv.dim",
            "input3": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw2_vh.dim",
            "input4": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw2_vv.dim",
            "input5": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw3_vh.dim",
            "input6": f"/data1/pipeline{os.sep}S1_20170502T231339_Orb_iw3_vv.dim",
        },
        result
    )


def test_s1_polarisations(self):
    product_dv = product_name.S1Product("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052")
    product_sv = product_name.S1Product("S1B_IW_SLC__1SSV_20170502T231339_20170502T231407_005426_009835_C052")

    self.assertEqual(['vh', 'vv'], product_dv.polarisations())
    self.assertEqual(['vv'], product_sv.polarisations())


def test_common_polarisations(self):
    product_dv = product_name.S1Product("S1B_IW_SLC__1SDV_20170502T231339_20170502T231407_005426_009835_C052")
    product_sv = product_name.S1Product("S1B_IW_SLC__1SSV_20170502T231339_20170502T231407_005426_009835_C052")

    self.assertEqual(['vv'], product_name.common_polarisations([product_dv, product_sv]))


if __name__ == "__main__":
    unittest.main()
