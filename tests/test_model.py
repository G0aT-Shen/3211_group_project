import unittest
from datetime import datetime

from model import ContactPIR, EventPIR, TaskPIR, TextPIR, ValidationError


class ModelTests(unittest.TestCase):
    """Model construction, validation, and serialization round-trip tests."""

    def test_text_record_fields(self):
        """US2: serialization includes the note ID, type and unchanged content."""
        pir = TextPIR(1, "buy milk")
        self.assertEqual(pir.to_dict(), {"id": 1, "type": "text", "text": "buy milk"})

    def test_task_and_event_dates(self):
        """US3/4: deadline and start getters return the expected datetimes."""
        task = TaskPIR(2, "report", "2026-11-19 20:00")
        event = EventPIR(3, "meeting", "2026-10-12 09:00", "2026-10-12 08:30")
        self.assertEqual(task.get_deadline(), datetime(2026, 11, 19, 20))
        self.assertEqual(event.get_start_time(), datetime(2026, 10, 12, 9))

    def test_contact_fields(self):
        """US5: contact fields preserve mobile numbers as strings."""
        contact = ContactPIR(4, "Zhang San", "Hung Hom", "61234567")
        self.assertEqual(contact.get_mobile(), "61234567")
        self.assertEqual(contact.get_fields()["name"], "Zhang San")

    def test_required_fields_are_validated(self):
        """An empty note must raise the specific ValidationError."""
        with self.assertRaises(ValidationError):
            TextPIR(1, "")


if __name__ == "__main__":
    unittest.main()
