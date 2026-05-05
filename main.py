import asyncio
import sys
from pathlib import Path

from errors import LeadScriptError, RuntimeErrorCustom
from interpreter import Interpreter
from lexico import AnalisadorLexico
from parser_1 import Parser


def resolver_caminho_arquivo(caminho):
    arquivo = Path(caminho).expanduser()
    if not arquivo.is_absolute():
        arquivo = Path.cwd() / arquivo
    return arquivo.resolve(strict=False)


async def executar_codigo_async(codigo, filename="<memoria>"):
    try:
        lexer = AnalisadorLexico(codigo)
        tokens = lexer.analisar()

        parser = Parser(tokens)
        ast = parser.parse()

        interpreter = Interpreter()
        return await interpreter.visit(ast)
    except LeadScriptError as erro:
        raise erro.with_context(filename=filename, source=codigo) from erro


def executar_codigo(codigo, filename="<memoria>"):
    return asyncio.run(executar_codigo_async(codigo, filename=filename))


async def executar_arquivo(caminho):
    arquivo = resolver_caminho_arquivo(caminho)

    if arquivo.suffix.lower() != ".las":
        raise RuntimeErrorCustom(
            "Arquivos LeadScript devem usar a extensao .las.",
            filename=str(arquivo),
        )

    try:
        codigo = arquivo.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeErrorCustom(f"Arquivo '{arquivo}' nao encontrado.") from exc

    return await executar_codigo_async(codigo, filename=arquivo.name)


def main(argv=None):
    argv = argv or sys.argv[1:]

    if len(argv) != 1:
        print("Uso: python main.py arquivo.las")
        return 1

    try:
        asyncio.run(executar_arquivo(argv[0]))
        return 0
    except LeadScriptError as erro:
        print(erro.format())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
