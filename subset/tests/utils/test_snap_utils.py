import unittest

from s1_ard_pypeline.utils import snap_utils


class TestSnapUtils(unittest.TestCase):
    def test_valid(self):
        example = b'Code Name                                    Version State    ' \
                  b'\r\n-------------------------------------------- ------- ' \
                  b'---------\r\norg.csa.rstb.rstb.op.polarimetric.tools      7.1.3   Enabled  ' \
                  b'\r\norg.esa.s2tbx.s2tbx.s2msi.reader             3.0.7   Enabled  \r\n '

        result = snap_utils._parse_snap_module_output(example)
        self.assertEqual([
            {'name': 'org.csa.rstb.rstb.op.polarimetric.tools',
             'state': 'Enabled',
             'version': '7.1.3'},
            {'name': 'org.esa.s2tbx.s2tbx.s2msi.reader',
             'state': 'Enabled',
             'version': '3.0.7'}
        ], result)

    def test_version_matching_happy(self):
        expected = [
            {
                "name": "foo",
                "version": "1.0.1"
            },
            {
                "name": "bar",
                "version": "2.3.4"
            }
        ]

        actual = [
            {
                "name": "foo",
                "version": "1.0.2"  # version number bigger
            },
            {
                "name": "bar",
                "version": "2.3.4"
            }
        ]
        self.assertTrue(snap_utils.match_module_lists(actual, expected))

    def test_version_matching_not_happy(self):
        expected = [
            {
                "name": "foo",
                "version": "1.0.1"
            },
            {
                "name": "bar",
                "version": "2.3.4"
            }
        ]

        actual = [
            {
                "name": "foo",
                "version": "1.0.0"  # version number smaller
            },
            {
                "name": "bar",
                "version": "2.3.4"
            }
        ]
        self.assertFalse(snap_utils.match_module_lists(actual, expected))


if __name__ == "__main__":
    unittest.main()
