import argparse
import dataclasses
import typing


@dataclasses.dataclass
class Args:
    dry_run: bool = False
    verbose: bool = False


def parse_args(args: typing.Optional[typing.List[str]] = None) -> Args:
    parser = argparse.ArgumentParser(
        description="Prepare podcast episodes for phone", exit_on_error=False
    )

    for field in dataclasses.fields(Args):
        assert field.type is bool, "Only bool args are currently supported"
        default = field.default if field.default is not None else argparse.SUPPRESS
        parser.add_argument(f"--{field.name}", action="store_true", default=default)

    return parser.parse_args(args, namespace=Args())
