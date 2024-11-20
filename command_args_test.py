import argparse
import unittest

import command_args


class TestCommandsArgs(unittest.TestCase):
    def test_no_args(self) -> None:
        parsed_args = command_args.parse_args()
        self.assertEqual(parsed_args, command_args.Args())

    def test_set_verbose(self) -> None:
        parsed_args = command_args.parse_args(["--verbose"])
        self.assertTrue(parsed_args.verbose)

    def test_set_dry_run(self) -> None:
        parsed_args = command_args.parse_args(["--dry_run"])
        self.assertTrue(parsed_args.dry_run)

    def test_try_set_invalid_parameter(self) -> None:
        with self.assertRaises(argparse.ArgumentError):
            command_args.parse_args(["--fake-flag-name"])


if __name__ == "__main__":
    unittest.main()
