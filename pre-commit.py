# -*- coding: utf-8 -*-

import argparse
import os
import subprocess
import sys
import typing

import encoding_helper
import run_tests

ROOT_FOLDER = os.path.dirname(__file__)


def run_process(args: list[str]) -> subprocess.CompletedProcess[str]:
    # Send the output through print directly here, otherwise there were odd flushing races with the other prints.
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding=encoding_helper.DESIRED_ENCODING,
    )
    if result.stdout:
        print(result.stdout, flush=True)
    return result


def main(args: typing.Optional[list[str]]) -> int:
    encoding_helper.enforce_desired_stdout_encoding()

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
