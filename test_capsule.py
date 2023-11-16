import unittest
import _xxsubinterpreters as interpreters


class TestCapsule(unittest.TestCase):

    def test_capsule(self):
        import zoneinfo

    def test_capsule_in_sub_interpreter(self):
        interp = interpreters.create()
        interpreters.run_string(interp, "import zoneinfo")

    def test_capsule2_in_sub_interpreter(self):
        interp = interpreters.create()
        interpreters.run_string(interp, "from socket import CAPI")
