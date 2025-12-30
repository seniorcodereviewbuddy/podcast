# -*- coding: utf-8 -*-

import io
import sys

DESIRED_ENCODING = "utf-8"


def enforce_desired_stdout_encoding() -> None:
    """
    Enforces that stdout uses UTF-8 encoding.

    Raises:
        RuntimeError: If encoding cannot be reconfigured (Python < 3.7 or incompatible stdout).
    """
    if sys.stdout.encoding != DESIRED_ENCODING:
        if sys.version_info < (3, 7) or not isinstance(sys.stdout, io.TextIOWrapper):
            raise RuntimeError(
                f"Script is run with incorrect stdout encoding ({sys.stdout.encoding}) and python version is too old to allow it to be automatically fixed. "
                f"Please either run this script with stdout encoding as {DESIRED_ENCODING}, or increase python version to 3.7 or later."
            )

        print(
            f"WARNING! This script will output {DESIRED_ENCODING} so it expects stdout to be in {DESIRED_ENCODING} encoding."
        )
        print(f"WARNING! Reconfiguring stdout encoding to be {DESIRED_ENCODING}")
        sys.stdout.reconfigure(encoding=DESIRED_ENCODING)
