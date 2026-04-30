"""
Tests for _pick_label() from app/db.py.
Copied inline to isolate from psycopg2/DB dependencies.

Test plan references: TC-L-01 through TC-L-09
"""
import unittest


# ── Function under test (copied from app/db.py for isolation) ─────────────────

def _pick_label(row, preferred_keys):
    for k in preferred_keys:
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for k, v in row.items():
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPickLabelPreferredKeys(unittest.TestCase):

    def test_TC_L_01_preferred_key_present_and_non_empty(self):
        """TC-L-01: Preferred key exists with a value → returned"""
        row = {"name": "Harold", "username": "harold99"}
        self.assertEqual(_pick_label(row, ["name"]), "Harold")

    def test_TC_L_02_first_preferred_key_wins_over_second(self):
        """TC-L-02: Multiple preferred keys → first non-empty one returned"""
        row = {"name": "Harold", "username": "harold99"}
        self.assertEqual(_pick_label(row, ["name", "username"]), "Harold")

    def test_TC_L_03_first_preferred_empty_falls_to_second(self):
        """TC-L-03: First preferred key is empty string → skips to second"""
        row = {"name": "", "username": "harold99"}
        self.assertEqual(_pick_label(row, ["name", "username"]), "harold99")

    def test_TC_L_04_first_preferred_whitespace_falls_to_second(self):
        """TC-L-04: First preferred key is whitespace only → skips to second"""
        row = {"name": "   ", "username": "harold99"}
        self.assertEqual(_pick_label(row, ["name", "username"]), "harold99")

    def test_TC_L_05_preferred_key_not_in_row_falls_to_fallback(self):
        """TC-L-05: Preferred key not in row → iterates all row values"""
        row = {"username": "harold99"}
        self.assertEqual(_pick_label(row, ["name"]), "harold99")

    def test_TC_L_06_whitespace_is_stripped_from_result(self):
        """TC-L-06: Value with surrounding whitespace → stripped in return"""
        row = {"name": "  Harold  "}
        self.assertEqual(_pick_label(row, ["name"]), "Harold")


class TestPickLabelFallback(unittest.TestCase):

    def test_TC_L_07_no_preferred_keys_finds_first_string_value(self):
        """TC-L-07: Empty preferred_keys list → falls back to any string value"""
        row = {"x": 42, "y": "barbershop"}
        self.assertEqual(_pick_label(row, []), "barbershop")

    def test_TC_L_08_non_string_values_ignored(self):
        """TC-L-08: Row with only non-string values → returns empty string"""
        row = {"id": 1, "count": 5, "flag": True}
        self.assertEqual(_pick_label(row, []), "")

    def test_TC_L_09_entirely_empty_row_returns_empty_string(self):
        """TC-L-09: Empty row dict → returns empty string"""
        self.assertEqual(_pick_label({}, ["name"]), "")


if __name__ == "__main__":
    unittest.main()
