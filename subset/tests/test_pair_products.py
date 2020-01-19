import unittest

from s1_ard_pypeline import pair_products
from s1_ard_pypeline.utils.product_name import S1Product


class TestPairProducts(unittest.TestCase):

    def test_pair_basic(self):
        products = [
            S1Product("S1B_IW_SLC__1SDV_20161127T231340_20161127T231408_003151_0055C4_E29B"),
            S1Product("S1B_IW_SLC__1SDV_20161221T231340_20161221T231407_003501_005FC5_4108"),
            S1Product("S1B_IW_SLC__1SDV_20170114T231338_20170114T231405_003851_006A05_36B2"),
            S1Product("S1B_IW_SLC__1SDV_20170207T231337_20170207T231405_004201_007477_1305"),
        ]

        result = pair_products.pair_products(products)

        product_names = list(map(lambda p: (p[0].product_name, p[1].product_name), result))

        self.assertEqual(
            [
                (
                    'S1B_IW_SLC__1SDV_20161127T231340_20161127T231408_003151_0055C4_E29B',
                    'S1B_IW_SLC__1SDV_20161221T231340_20161221T231407_003501_005FC5_4108'
                ),
                (
                    'S1B_IW_SLC__1SDV_20161221T231340_20161221T231407_003501_005FC5_4108',
                    'S1B_IW_SLC__1SDV_20170114T231338_20170114T231405_003851_006A05_36B2'
                ),
                (
                    'S1B_IW_SLC__1SDV_20170114T231338_20170114T231405_003851_006A05_36B2',
                    'S1B_IW_SLC__1SDV_20170207T231337_20170207T231405_004201_007477_1305'
                )
            ],
            product_names
        )

    def test_pair_overlapping(self):
        products = [
            S1Product("S1B_IW_SLC__1SDV_20181105T231400_20181105T231427_013476_018EF4_EB81"),
            S1Product("S1B_IW_SLC__1SDV_20181024T231354_20181024T231422_013301_018974_D22C"),
            S1Product("S1B_IW_SLC__1SDV_20181024T231422_20181024T231454_013301_018974_DA34"),
        ]

        result = pair_products.pair_products(products)
        product_names = list(map(lambda p: (p[0].product_name, p[1].product_name), result))
        self.assertEqual(
            [
                (
                    'S1B_IW_SLC__1SDV_20181024T231354_20181024T231422_013301_018974_D22C',
                    'S1B_IW_SLC__1SDV_20181105T231400_20181105T231427_013476_018EF4_EB81'
                ),
                (
                    'S1B_IW_SLC__1SDV_20181024T231422_20181024T231454_013301_018974_DA34',
                    'S1B_IW_SLC__1SDV_20181105T231400_20181105T231427_013476_018EF4_EB81'
                )
            ],
            product_names
        )

    def test_same_orbit(self):
        # These two should not pair up because they are from the same orbit.
        products = [
            S1Product("S1B_IW_SLC__1SDV_20180609T104125_20180609T104152_011295_014BCA_99E0"),
            S1Product("S1B_IW_SLC__1SDV_20180609T104150_20180609T104217_011295_014BCA_1FBB")
        ]

        result = pair_products.pair_products(products)

        self.assertEqual([], result)

    def test_mixed(self):
        products = [
            S1Product("S1B_IW_SLC__1SDV_20181129T231359_20181129T231426_013826_019A08_0D86"),
            S1Product("S1B_IW_SLC__1SDV_20181117T231400_20181117T231427_013651_019471_810F"),
            S1Product("S1B_IW_SLC__1SDV_20181105T231400_20181105T231427_013476_018EF4_EB81"),
            S1Product("S1B_IW_SLC__1SDV_20181024T231354_20181024T231422_013301_018974_D22C"),
            S1Product("S1B_IW_SLC__1SDV_20180930T231400_20180930T231427_012951_017EB9_C375")
        ]

        result = pair_products.pair_products(products)

        product_names = list(map(lambda p: (p[0].product_name, p[1].product_name), result))

        self.assertEqual(
            [
                (
                    'S1B_IW_SLC__1SDV_20180930T231400_20180930T231427_012951_017EB9_C375',
                    'S1B_IW_SLC__1SDV_20181024T231354_20181024T231422_013301_018974_D22C'
                ),
                (
                    'S1B_IW_SLC__1SDV_20181024T231354_20181024T231422_013301_018974_D22C',
                    'S1B_IW_SLC__1SDV_20181105T231400_20181105T231427_013476_018EF4_EB81'
                ),
                (
                    'S1B_IW_SLC__1SDV_20181105T231400_20181105T231427_013476_018EF4_EB81',
                    'S1B_IW_SLC__1SDV_20181117T231400_20181117T231427_013651_019471_810F'
                ),
                (
                    'S1B_IW_SLC__1SDV_20181117T231400_20181117T231427_013651_019471_810F',
                    'S1B_IW_SLC__1SDV_20181129T231359_20181129T231426_013826_019A08_0D86'
                )
            ],
            product_names
        )
