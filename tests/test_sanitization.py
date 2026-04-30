import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.input_sanitization import sanitize_input


class TestSanitizeInputNullAndType(unittest.TestCase):

    def test_none_input_returns_error(self):
        result = sanitize_input(None)
        self.assertEqual(result, "Input must not be empty.")

    def test_integer_input_returns_error(self):
        result = sanitize_input(42)
        self.assertEqual(result, "Input must be a string.")

    def test_list_input_returns_error(self):
        result = sanitize_input(["hello"])
        self.assertEqual(result, "Input must be a string.")

    def test_bool_input_returns_error(self):
        result = sanitize_input(True)
        self.assertEqual(result, "Input must be a string.")


class TestSanitizeInputEmpty(unittest.TestCase):

    def test_empty_string_returns_error(self):
        result = sanitize_input("")
        self.assertEqual(result, "Input must not be empty.")

    def test_whitespace_only_returns_error(self):
        result = sanitize_input("   ")
        self.assertEqual(result, "Input must not be empty.")

    def test_tab_only_returns_error(self):
        result = sanitize_input("\t")
        self.assertEqual(result, "Input must not be empty.")

    def test_newline_only_returns_error(self):
        result = sanitize_input("\n")
        self.assertEqual(result, "Input must not be empty.")


class TestSanitizeInputClean(unittest.TestCase):

    def test_normal_text_passes(self):
        result = sanitize_input("Great haircut, very professional")
        self.assertIsNone(result)

    def test_single_word_passes(self):
        result = sanitize_input("hello")
        self.assertIsNone(result)

    def test_text_with_leading_trailing_whitespace_passes(self):
        result = sanitize_input("  clean input  ")
        self.assertIsNone(result)

    def test_numbers_in_string_pass(self):
        result = sanitize_input("Room 5, arrived at 10:30")
        self.assertIsNone(result)

    def test_punctuation_passes(self):
        result = sanitize_input("Brilliant! 10/10 would recommend.")
        self.assertIsNone(result)


class TestSanitizeInputProfanity(unittest.TestCase):

    def test_profanity_alone_returns_error(self):
        result = sanitize_input("fuck")
        self.assertEqual(result, "Input contains inappropriate language.")

    def test_profanity_in_sentence_returns_error(self):
        result = sanitize_input("this is shit service")
        self.assertEqual(result, "Input contains inappropriate language.")

    def test_profanity_uppercase_returns_error(self):
        result = sanitize_input("FUCK this place")
        self.assertEqual(result, "Input contains inappropriate language.")

    def test_profanity_mixed_case_returns_error(self):
        result = sanitize_input("What a Damn mess")
        self.assertEqual(result, "Input contains inappropriate language.")

    def test_profanity_as_substring_passes(self):
        # "assassin" contains "ass" but is not a whole-word match
        result = sanitize_input("The assassin character was great")
        self.assertIsNone(result)

    def test_profanity_as_substring_classic_passes(self):
        # "Scunthorpe problem" — "cunt" inside a word should not match
        result = sanitize_input("Scunthorpe is a lovely town")
        self.assertIsNone(result)

    def test_multiple_profanities_returns_error(self):
        result = sanitize_input("fuck this shit")
        self.assertEqual(result, "Input contains inappropriate language.")

    def test_bollocks_returns_error(self):
        result = sanitize_input("absolute bollocks")
        self.assertEqual(result, "Input contains inappropriate language.")

    def test_wanker_returns_error(self):
        result = sanitize_input("what a wanker")
        self.assertEqual(result, "Input contains inappropriate language.")


if __name__ == "__main__":
    unittest.main()
