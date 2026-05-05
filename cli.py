import argparse
import asyncio
import sys

from errors import LeadScriptError
from main import executar_arquivo


def criar_parser():
    parser = argparse.ArgumentParser(
        prog="leadscript",
        description="Runner oficial da linguagem LeadScript.",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    rodar = subparsers.add_parser(
        "rodar",
        help="Executa um arquivo .las.",
    )
    rodar.add_argument(
        "arquivo",
        help="Caminho absoluto ou relativo para o script .las.",
    )

    return parser


def main(argv=None):
    parser = criar_parser()
    args = parser.parse_args(argv)

    if args.comando == "rodar":
        try:
            asyncio.run(executar_arquivo(args.arquivo))
            return 0
        except LeadScriptError as erro:
            print(erro.format(), file=sys.stderr)
            return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
