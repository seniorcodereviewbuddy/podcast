# -*- coding: utf-8 -*-

import argparse
import io
import os
import subprocess
import sys
import typing

import run_tests

ROOT_FOLDER = os.path.dirname(__file__)

EXPECTED_ENCODING = "utf-8"


def RunProcess(args: list[str]) -> subprocess.CompletedProcess[str]:
    # Send the output through print directly here, otherwise there were odd flushing races with the other prints.
    encoding = "utf-8"
    result = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding=encoding
    )
    if result.stdout:
        print(result.stdout, flush=True)
    return result


def main(args: typing.Optional[list[str]]) -> int:
    if sys.stdout.encoding != EXPECTED_ENCODING:
        if sys.version_info < (3, 7) or not isinstance(sys.stdout, io.TextIOWrapper):
            print(
                "Script is run with incorrect stdout encoding and python version is too old to allow it to be automatically fixed."
            )
            print(
                f"Please either run this script with stdout encoding as {EXPECTED_ENCODING}, or increase python version to 3.7 or later."
            )
            return 1

        print(
            f"WARNING! This script will output utf-8 so it expects stdout to be in {EXPECTED_ENCODING} encoding."
        )
        print(f"WARNING! Reconfiguring stdout encoding to be {EXPECTED_ENCODING}")
        sys.stdout.reconfigure(encoding=EXPECTED_ENCODING)

    parser = argparse.ArgumentParser(
        description="Prepare repo for submitting a change by running cleanups and checks"
    )
    parser.parse_args(args)

    test_result = run_tests.discover_and_run_tests(
        start_dir=ROOT_FOLDER, pattern=run_tests.DEFAULT_TEST_PATTERN, failfast=True
    )
    if test_result != 0:
        return test_result

    print("All checks passed successfully", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
