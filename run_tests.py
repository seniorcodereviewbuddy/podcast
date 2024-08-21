import argparse
import os
import sys
import typing
import unittest

DEFAULT_TEST_PATTERN = "*_test.py"


def discover_and_run_tests(start_dir: str, pattern: str, failfast: bool) -> int:
    tests = unittest.defaultTestLoader.discover(start_dir, pattern=pattern)

    runner = unittest.TextTestRunner(failfast=failfast)
    result = runner.run(tests)
    return 0 if result.wasSuccessful() else 1


def main(args: typing.Optional[list[str]]) -> int:
    ROOT_FOLDER = os.path.dirname(__file__)

    parser = argparse.ArgumentParser(
        description="Helper script to run unit tests",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--failfast",
        action="store_true",
        help="Run in failfast mode",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default=DEFAULT_TEST_PATTERN,
        help="Pattern to use to match test files",
    )
    parsed_args = parser.parse_args(args)

    return discover_and_run_tests(
        ROOT_FOLDER, parsed_args.pattern, parsed_args.failfast
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
