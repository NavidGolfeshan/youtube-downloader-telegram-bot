import unittest

from selection import parse_track_selection


class ParseTrackSelectionTests(unittest.TestCase):
    def test_all(self):
        self.assertEqual(parse_track_selection("all", 5), [0, 1, 2, 3, 4])

    def test_numbers_and_ranges(self):
        self.assertEqual(
            parse_track_selection("1,3,5-7", 8),
            [0, 2, 4, 5, 6],
        )

    def test_whitespace_and_semicolon(self):
        self.assertEqual(
            parse_track_selection(" 2 ; 4  ", 5),
            [1, 3],
        )

    def test_duplicates_are_removed(self):
        self.assertEqual(parse_track_selection("1,1,2-3", 4), [0, 1, 2])

    def test_out_of_range_fails(self):
        with self.assertRaises(ValueError):
            parse_track_selection("1,6", 5)

    def test_invalid_input_fails(self):
        with self.assertRaises(ValueError):
            parse_track_selection("one,two", 5)


if __name__ == "__main__":
    unittest.main()
