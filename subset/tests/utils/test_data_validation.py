import rasterio
import unittest
from s1_ard_pypeline.utils import data_validation


class TestDataValidation(unittest.TestCase):

    def test_bounding_box_to_wkt(self):
        box = rasterio.coords.BoundingBox(10, -10, -10, 10)
        result = data_validation.bounding_box_to_wkt(box)
        self.assertEqual("POLYGON((10 10, -10 10, -10 -10, 10 -10, 10 10))", result)

    def test_overlap_matching(self):
        box_a = rasterio.coords.BoundingBox(10, -10, -10, 10)
        box_b = rasterio.coords.BoundingBox(5, -5, -5, 5)

        self.assertTrue(data_validation.overlap(box_a, box_b))

    def test_overlap_not_matching(self):
        box_a = rasterio.coords.BoundingBox(10, -10, -10, 10)
        box_b = rasterio.coords.BoundingBox(-11, -11, -22, -22)

        self.assertFalse(data_validation.overlap(box_a, box_b))
