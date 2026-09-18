import json
import tempfile
import unittest
from pathlib import Path

from controller import PIMManager, PIRFactory
from storage import Storage


class StorageTests(unittest.TestCase):
    def test_save_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.pim"
            manager = PIMManager()
            manager.add_pir(PIRFactory.create("text", {"text": "persist me"}))
            Storage.save(path, manager)
            loaded = Storage.load(path)
            self.assertEqual(loaded.get_pir(1).get_text(), "persist me")
            self.assertEqual(json.loads(path.read_text())["schema_version"], 1)

    def test_corrupt_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.pim"
            path.write_text("not json")
            with self.assertRaises(Exception):
                Storage.load(path)


if __name__ == "__main__":
    unittest.main()
