import logging
import os
import unittest

from s1_ard_pypeline.ard import ard


class TestARDTools(unittest.TestCase):

    def test_graph(self):
        self.assertEqual(f"graphs{os.sep}foo.xml", ard.graph("foo"))
        self.assertEqual(f"graphs{os.sep}foo.xml", ard.graph("foo.xml"))
        self.assertEqual(f"graphs{os.sep}foo.xml", ard.graph("graphs/foo.xml"))
        self.assertEqual(f"graphs{os.sep}foo.xml", ard.graph("graphs\\foo.xml"))

    def test_process_chain_empty(self):
        """
        Make sure that the process works with an empty chain
        """
        process = []
        ard.process_chain(process, "test")

    def test_process_chain_simple(self):
        process = [
            lambda: True
        ]
        ard.process_chain(process, "test")

    def test_process_chain_fail_simple(self):
        process = [
            lambda: self._boom(),
            lambda: self.fail("should not get here"),
        ]
        try:
            ard.process_chain(process, "test")
        except ard.ProcessError:
            pass

    def test_flatten(self):
        data = ['a', ['b', 'c', ['d']], None, [], 'e']
        expected = ['a', 'b', 'c', 'd', 'e']
        result = ard.flatten_list(data)
        self.assertEqual(expected, result)

    def _boom(self):
        raise ard.ProcessError("boom!")

    def test_chain_building(self):
        with self.assertLogs('tests', level='INFO') as test_logger:
            chain = [
                list(map(lambda p: log_output(logging.getLogger('tests'), p[0], p[1]),
                         [(a, b) for a in ['a', 'b', 'c'] for b in ['x', 'y', 'z']]))
            ]
            ard.process_chain(chain, "test")

        self.assertEqual(
            test_logger.output,
            [
                "INFO:tests:('a', 'x')",
                "INFO:tests:('a', 'y')",
                "INFO:tests:('a', 'z')",
                "INFO:tests:('b', 'x')",
                "INFO:tests:('b', 'y')",
                "INFO:tests:('b', 'z')",
                "INFO:tests:('c', 'x')",
                "INFO:tests:('c', 'y')",
                "INFO:tests:('c', 'z')"
            ]
        )


def log_output(log, a, b):
    return lambda: log.info(f"('{a}', '{b}')")


if __name__ == "__main__":
    unittest.main()
