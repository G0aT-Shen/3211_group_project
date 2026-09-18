import unittest

from cli.search_parser import SearchParser
from controller import PIMManager, PIRFactory
from model.exceptions import PIRNotFoundError


class ControllerTests(unittest.TestCase):
    def test_crud_and_monotonic_ids(self):
        manager = PIMManager()
        first = manager.add_pir(PIRFactory.create("text", {"text": "one"}))
        second = manager.add_pir(PIRFactory.create("contact", {"name": "A", "address": "B", "mobile": "1"}))
        self.assertEqual((first.get_id(), second.get_id()), (1, 2))
        manager.edit_pir(1, {"text": "updated"})
        self.assertEqual(manager.get_pir(1).get_text(), "updated")
        manager.delete_pir(1)
        third = manager.add_pir(PIRFactory.create("text", {"text": "three"}))
        self.assertEqual(third.get_id(), 3)

    def test_missing_record_raises(self):
        with self.assertRaises(PIRNotFoundError):
            PIMManager().get_pir(99)

    def test_search(self):
        manager = PIMManager()
        manager.add_pir(PIRFactory.create("text", {"text": "one"}))
        results = manager.search(SearchParser().parse('text contains "ONE"'))
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
