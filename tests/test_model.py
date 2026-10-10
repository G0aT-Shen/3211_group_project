import unittest
from datetime import datetime

from model import (ContactPIR, EventPIR, PIR, PIMManager, TaskPIR, TextPIR,
                   ValidationError)
from model.pir import format_datetime


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

    def test_record_dictionaries_cannot_bypass_validation_or_change_ids(self):
        """NFR-02: returned records expose no dictionary that can mutate live data."""
        records = [TextPIR(text="original"),
                   TaskPIR(description="report", deadline="2026-11-19 20:00"),
                   EventPIR(description="meeting", start_time="2026-10-12 09:00",
                            alarm="2026-10-12 08:30"),
                   ContactPIR(name="Alice", address="Hung Hom", mobile="01234567")]
        manager = PIMManager()
        for record in records:
            stored = manager.add_pir(record)
            before = stored.to_dict()
            with self.subTest(kind=stored.get_type()):
                with self.assertRaises(AttributeError):
                    stored.__dict__.update(_id=99)
                with self.assertRaises(TypeError):
                    vars(stored).update({key: "" for key in stored.get_fields()})
                self.assertEqual(stored.to_dict(), before)
                self.assertEqual(PIR.from_dict(before).to_dict(), before)

        updates = [(1, "text", "updated", "get_text"),
                   (2, "description", "updated task", "get_description"),
                   (3, "description", "updated event", "get_description"),
                   (4, "mobile", "+852 00123", "get_mobile")]
        for record_id, field, value, getter in updates:
            with self.subTest(record_id=record_id):
                original = manager.get_pir(record_id)
                replacement = manager.edit_pir(record_id, {field: value})
                self.assertEqual(replacement.get_id(), record_id)
                self.assertEqual(replacement.get_type(), original.get_type())
                self.assertEqual(getattr(replacement, getter)(), value)
                self.assertIsNot(replacement, original)
                self.assertNotEqual(getattr(original, getter)(), value)
        self.assertEqual(PIMManager.from_dict(manager.to_dict()).to_dict(), manager.to_dict())

    def test_timestamp_display_keeps_four_digit_years_at_calendar_boundaries(self):
        """DR-01/NFR-01: timestamp display has the same padding on every platform."""
        for value, expected in [(datetime(1, 1, 1), "0001-01-01 00:00"),
                                (datetime(999, 12, 31, 9, 5), "0999-12-31 09:05"),
                                (datetime(9999, 12, 31, 23, 59), "9999-12-31 23:59")]:
            with self.subTest(value=value):
                self.assertEqual(format_datetime(value), expected)
                task = TaskPIR(1, "boundary", value)
                event = EventPIR(2, "boundary", value, value)
                self.assertIn(expected, str(task))
                self.assertEqual(str(event).count(expected), 2)
                self.assertEqual(PIR.from_dict(task.to_dict()).get_deadline(), value)
                self.assertEqual(PIR.from_dict(event.to_dict()).get_alarm(), value)


if __name__ == "__main__":
    unittest.main()
