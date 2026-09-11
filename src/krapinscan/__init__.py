from .main import KraPinType, main as _main, parse_statement


def main() -> None:
	_main()

__all__ = ["KraPinType", "main", "parse_statement"]
