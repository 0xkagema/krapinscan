from .main import KraPinType, main as _main, parse_certificate


def main() -> None:
    _main()


__all__ = ["KraPinType", "main", "parse_certificate"]
