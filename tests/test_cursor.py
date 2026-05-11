"""
Tests for _parse_cursor() and _make_next_cursor() from app/api.py.
These functions are copied inline to isolate them from Flask/DB dependencies.

Test plan references: TC-C-01 through TC-C-12
"""
import unittest
from datetime import datetime

# ── Functions under test (copied from app/api.py for isolation) ──────────────

def _parse_cursor(cursor_value: str):
    """
    Expects cursor like: "2026-03-04T16:32:36.123456Z|123"
    Returns (datetime, int) or None
    """
    if not cursor_value:
        return None
    try:
        created_at_s, photo_id_s = cursor_value.split("|", 1)
        created_at_s = created_at_s.replace("Z", "")
        dt = datetime.fromisoformat(created_at_s)
        return (dt, int(photo_id_s))
    except Exception:
        return None


def _make_next_cursor(items):
    """
    items are dicts containing created_at (datetime) + photo_id (int).
    Returns cursor string or None.
    """
    if not items:
        return None
    last = items[-1]
    created_at = last.get("created_at")
    photo_id = last.get("photo_id")
    if not created_at or photo_id is None:
        return None
    return f"{created_at.isoformat()}Z|{int(photo_id)}"


# ── _parse_cursor tests ───────────────────────────────────────────────────────

class TestParseCursorNullAndEmpty(unittest.TestCase):

    def test_TC_C_01_none_returns_none(self):
        """TC-C-01: None input → None (no cursor = first page)"""
        self.assertIsNone(_parse_cursor(None))

    def test_TC_C_02_empty_string_returns_none(self):
        """TC-C-02: Empty string → None"""
        self.assertIsNone(_parse_cursor(""))

    def test_TC_C_03_whitespace_only_returns_none(self):
        """TC-C-03: Whitespace-only string → None (split fails)"""
        self.assertIsNone(_parse_cursor("   "))


class TestParseCursorValidFormats(unittest.TestCase):

    def test_TC_C_04_valid_cursor_with_Z(self):
        """TC-C-04: Standard ISO format with Z suffix → parsed correctly"""
        result = _parse_cursor("2026-03-04T16:32:36.123456Z|123")
        self.assertIsNotNone(result)
        dt, photo_id = result
        self.assertEqual(dt, datetime(2026, 3, 4, 16, 32, 36, 123456))
        self.assertEqual(photo_id, 123)

    def test_TC_C_05_valid_cursor_without_Z(self):
        """TC-C-05: ISO format without Z → still parsed (Z is optional)"""
        result = _parse_cursor("2026-03-04T16:32:36.123456|456")
        self.assertIsNotNone(result)
        dt, photo_id = result
        self.assertEqual(dt, datetime(2026, 3, 4, 16, 32, 36, 123456))
        self.assertEqual(photo_id, 456)

    def test_TC_C_06_photo_id_zero_is_valid(self):
        """TC-C-06: photo_id = 0 is a valid integer → returned correctly"""
        result = _parse_cursor("2026-03-04T16:32:36Z|0")
        self.assertIsNotNone(result)
        self.assertEqual(result[1], 0)

    def test_TC_C_07_large_photo_id(self):
        """TC-C-07: Large photo_id integer → parsed correctly"""
        result = _parse_cursor("2026-01-01T00:00:00Z|9999999")
        self.assertIsNotNone(result)
        self.assertEqual(result[1], 9999999)


class TestParseCursorInvalidFormats(unittest.TestCase):

    def test_TC_C_08_missing_pipe_returns_none(self):
        """TC-C-08: No pipe separator → split fails → None"""
        self.assertIsNone(_parse_cursor("2026-03-04T16:32:36.123456Z123"))

    def test_TC_C_09_bad_date_returns_none(self):
        """TC-C-09: Non-ISO date string → fromisoformat raises → None"""
        self.assertIsNone(_parse_cursor("notadate|123"))

    def test_TC_C_10_non_integer_photo_id_returns_none(self):
        """TC-C-10: photo_id is not an integer → int() raises → None"""
        self.assertIsNone(_parse_cursor("2026-03-04T16:32:36Z|abc"))

    def test_TC_C_11_float_photo_id_returns_none(self):
        """TC-C-11: Float photo_id → int('12.5') raises → None"""
        self.assertIsNone(_parse_cursor("2026-03-04T16:32:36Z|12.5"))


# ── _make_next_cursor tests ───────────────────────────────────────────────────

class TestMakeNextCursor(unittest.TestCase):

    def test_TC_C_12_empty_list_returns_none(self):
        """TC-C-12: Empty items list → no last item → None"""
        self.assertIsNone(_make_next_cursor([]))

    def test_TC_C_13_missing_created_at_returns_none(self):
        """TC-C-13: Item with no created_at key → None"""
        self.assertIsNone(_make_next_cursor([{"photo_id": 5}]))

    def test_TC_C_14_missing_photo_id_returns_none(self):
        """TC-C-14: Item with no photo_id key → None"""
        dt = datetime(2026, 3, 4, 16, 32, 36, 123456)
        self.assertIsNone(_make_next_cursor([{"created_at": dt}]))

    def test_TC_C_15_valid_item_produces_cursor_string(self):
        """TC-C-15: Valid item → returns 'ISO_DATEz|photo_id' string"""
        dt = datetime(2026, 3, 4, 16, 32, 36, 123456)
        result = _make_next_cursor([{"created_at": dt, "photo_id": 99}])
        self.assertEqual(result, "2026-03-04T16:32:36.123456Z|99")

    def test_TC_C_16_uses_last_item_in_list(self):
        """TC-C-16: Multiple items → cursor derived from last item only"""
        dt1 = datetime(2026, 1, 1, 0, 0, 0)
        dt2 = datetime(2026, 6, 15, 12, 0, 0)
        items = [
            {"created_at": dt1, "photo_id": 1},
            {"created_at": dt2, "photo_id": 2},
        ]
        result = _make_next_cursor(items)
        self.assertIn("2026-06-15", result)
        self.assertTrue(result.endswith("|2"))

    def test_TC_C_17_photo_id_zero_included(self):
        """TC-C-17: photo_id = 0 is falsy but not None → cursor still produced"""
        dt = datetime(2026, 3, 4, 16, 32, 36)
        result = _make_next_cursor([{"created_at": dt, "photo_id": 0}])
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("|0"))

    def test_TC_C_18_roundtrip_parse_after_make(self):
        """TC-C-18: Cursor made by _make_next_cursor can be parsed by _parse_cursor"""
        dt = datetime(2026, 3, 4, 16, 32, 36, 123456)
        cursor_str = _make_next_cursor([{"created_at": dt, "photo_id": 42}])
        parsed = _parse_cursor(cursor_str)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed[1], 42)


if __name__ == "__main__":
    unittest.main()
