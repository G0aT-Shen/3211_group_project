import unittest

from cli.search_parser import SearchParser
from controller import PIMManager, PIRFactory
from model.exceptions import PIRNotFoundError


class ControllerTests(unittest.TestCase):
    def test_crud_and_monotonic_ids(self):
        """US6/9: deleting one record preserves the others and never reissues its ID."""
        manager = PIMManager()
        first = manager.add_pir(PIRFactory.create("text", {"text": "one"}))
        second = manager.add_pir(PIRFactory.create("contact", {"name": "A", "address": "B", "mobile": "1"}))
        self.assertEqual((first.get_id(), second.get_id()), (1, 2))
        manager.edit_pir(1, {"text": "updated"})
        self.assertEqual(manager.get_pir(1).get_text(), "updated")
        manager.delete_pir(1)
        self.assertEqual(manager.to_dict(), {
            'schema_version': 1, 'next_id': 3,
            'pirs': [{'id': 2, 'type': 'contact', 'name': 'A', 'address': 'B', 'mobile': '1'}],
        })
        with self.assertRaises(PIRNotFoundError):
            manager.get_pir(1)
        third = manager.add_pir(PIRFactory.create("text", {"text": "three"}))
        self.assertEqual(third.get_id(), 3)

    def test_missing_record_raises(self):
        """A missing lookup or deletion fails without changing existing records or IDs."""
        manager = PIMManager()
        manager.add_pir(PIRFactory.create('text', {'text': 'keep me'}))
        expected = {'schema_version': 1, 'next_id': 2,
                    'pirs': [{'id': 1, 'type': 'text', 'text': 'keep me'}]}
        for operation in (manager.get_pir, manager.delete_pir):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(PIRNotFoundError):
                    operation(99)
                self.assertEqual(manager.to_dict(), expected)

    def test_list_and_search_sort_shuffled_initial_ids(self):
        """A loaded collection's insertion order must not change list/search ID ordering."""
        manager = PIMManager([
            PIRFactory.create('text', {'text': 'match third'}, 9),
            PIRFactory.create('contact', {'name': 'Alice', 'address': 'HK', 'mobile': '01'}, 4),
            PIRFactory.create('text', {'text': 'match first'}, 2),
            PIRFactory.create('text', {'text': 'match second'}, 7),
        ])
        self.assertEqual([pir.get_id() for pir in manager.list_all()], [2, 4, 7, 9])
        matches = manager.search(SearchParser().parse('text contains match'))
        self.assertEqual([pir.get_id() for pir in matches], [2, 7, 9])

    def test_search(self):
        """US7: case-insensitive text search selects the matching record."""
        manager = PIMManager()
        manager.add_pir(PIRFactory.create("text", {"text": "one"}))
        results = manager.search(SearchParser().parse('text contains "ONE"'))
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
