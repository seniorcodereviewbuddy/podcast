import unittest

import time_helper


class TestTimeHelper(unittest.TestCase):
    def test_seconds_to_string(self) -> None:
        self.assertEqual(time_helper.seconds_to_string(0), "0s")
        self.assertEqual(time_helper.seconds_to_string(30), "30s")
        self.assertEqual(time_helper.seconds_to_string(60), "1m")
        self.assertEqual(time_helper.seconds_to_string(3600), "1h")
        self.assertEqual(time_helper.seconds_to_string(3600 * 24), "1d")

        self.assertEqual(
            time_helper.seconds_to_string(3600 * 24 * 2 + 3600 * 3 + 60 * 4 + 5),
            "2d3h4m5s",
        )


if __name__ == "__main__":
    unittest.main()
