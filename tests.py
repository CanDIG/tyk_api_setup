import unittest

from scripts.api_generator import main


class TestJsonGen(unittest.TestCase):

    def testInvalidJson(self):
        with self.assertRaises(TypeError):
            main("testing_data/invalid_json.json")

    def testInvalidNoJson(self):
        with self.assertRaises(TypeError):
            main("scripts/api_generator.py")

    def testNoFiles(self):
        with self.assertRaises(FileNotFoundError):
            main("file.json")

    def testNoApiId(self):
        with self.assertRaises(ValueError):
            main("confs/api_auth.conf.json")


if __name__ == "__main__":
    unittest.main()
