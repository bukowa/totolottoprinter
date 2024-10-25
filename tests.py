import os
import pathlib

os.environ["LOTTO_API"] = "test"
import checkprint
import unittest
from checkprint import save_lastprinted_file, read_lastprinted_file

test_file = "my_test_file.json"
checkprint.LAST_PRINTED_FILE = test_file


class TestFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        filename = "testfile.json"
        checkprint.last_printed_path = pathlib.Path(filename)
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        os.environ["LOTTO_API"] = "test"

    def test_last_printed_file_ops(self):
        """
        Make sure we can work on the file.
        """
        ...
        data = read_lastprinted_file()
        assert len(data) == 0
        data["foo"] = "bar"
        save_lastprinted_file(data)
        data = read_lastprinted_file()
        assert data["foo"] == "bar"
