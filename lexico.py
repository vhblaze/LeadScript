from dataclasses import dataclass
from enum import Enum

from errors import LexicalError


class TipoToken(Enum):
    IDENTIFICADOR = "IDENTIFICADOR"
    NUMERO = "NUMERO"
    STRING = "STRING"
    BOOLEANO = "BOOLEANO"
    NULO = "NULO"

    SE = "SE"
    ENTAO = "ENTAO"
    SENAO = "SENAO"
    FIM = "FIM"
    PARA = "PARA"
    CADA = "CADA"
    EM = "EM"

    ATRIBUICAO = "="
    IGUALDADE = "=="
    DIFERENTE = "!="
    MAIOR = ">"
    MENOR = "<"
    MAIOR_IGUAL = ">="
    MENOR_IGUAL = "<="
    SOMA = "+"
    SUB = "-"
    MULT = "*"
    DIV = "/"
    MOD = "%"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"
    VIRGULA = ","
    DOIS_PONTOS = ":"
    PONTO = "."
    PONTO_VIRGULA = ";"
    NOVA_LINHA = "NOVA_LINHA"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    tipo: TipoToken
    valor: object = None
    linha: int = 1
    coluna: int = 1

    def __repr__(self):
        local = f"{self.linha}:{self.coluna}"
        if self.valor is None:
            return f"Token({self.tipo.name}, @{local})"
        return f"Token({self.tipo.name}, {self.valor!r}, @{local})"


class AnalisadorLexico:
    """Lexer da LeadScript.

    O lexer produz tokens de uma DSL de automacao, preservando a primeira fase
    classica do pipeline de compiladores: texto -> tokens.
    """

    PALAVRAS_CHAVE = {
        "se": TipoToken.SE,
        "entao": TipoToken.ENTAO,
        "senao": TipoToken.SENAO,
        "fim": TipoToken.FIM,
        "para": TipoToken.PARA,
        "cada": TipoToken.CADA,
        "em": TipoToken.EM,
        "e": TipoToken.AND,
        "ou": TipoToken.OR,
        "nao": TipoToken.NOT,
    }

    BOOLEANOS = {
        "verdadeiro": True,
        "falso": False,
    }

    SIMPLES = {
        "+": TipoToken.SOMA,
        "-": TipoToken.SUB,
        "*": TipoToken.MULT,
        "/": TipoToken.DIV,
        "%": TipoToken.MOD,
        "(": TipoToken.LPAREN,
        ")": TipoToken.RPAREN,
        "[": TipoToken.LBRACKET,
        "]": TipoToken.RBRACKET,
        "{": TipoToken.LBRACE,
        "}": TipoToken.RBRACE,
        ",": TipoToken.VIRGULA,
        ":": TipoToken.DOIS_PONTOS,
        ".": TipoToken.PONTO,
        ";": TipoToken.PONTO_VIRGULA,
    }

    def __init__(self, codigo_fonte):
        self.codigo = codigo_fonte
        self.posicao = 0
        self.linha = 1
        self.coluna = 1
        self.tokens = []

    def _caractere_atual(self):
        if self.posicao >= len(self.codigo):
            return None
        return self.codigo[self.posicao]

    def _proximo(self):
        if self.posicao + 1 >= len(self.codigo):
            return None
        return self.codigo[self.posicao + 1]

    def _avancar(self):
        char = self._caractere_atual()
        self.posicao += 1

        if char == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1

    def _adicionar(self, tipo, valor=None, linha=None, coluna=None):
        self.tokens.append(
            Token(tipo, valor, linha or self.linha, coluna or self.coluna)
        )

    def analisar(self):
        while self._caractere_atual() is not None:
            char = self._caractere_atual()

            if char in " \t\r":
                self._avancar()
                continue

            if char == "\n":
                self._adicionar(TipoToken.NOVA_LINHA)
                self._avancar()
                continue

            if char == "#":
                self._ignorar_comentario()
                continue

            if char == "~" and self._proximo() == "~":
                self._avancar()
                self._avancar()
                self._ignorar_comentario()
                continue

            if char == "/" and self._proximo() == "/":
                self._avancar()
                self._avancar()
                self._ignorar_comentario()
                continue

            if char.isdigit():
                self._ler_numero()
                continue

            if char == '"' or char == "'":
                self._ler_string()
                continue

            if char.isalpha() or char == "_":
                self._ler_identificador()
                continue

            self._ler_operador_ou_simbolo()

        self._adicionar(TipoToken.EOF)
        return self.tokens

    def _ignorar_comentario(self):
        while self._caractere_atual() not in (None, "\n"):
            self._avancar()

    def _ler_numero(self):
        linha, coluna = self.linha, self.coluna
        texto = ""
        pontos = 0

        while True:
            char = self._caractere_atual()
            if char is None:
                break

            if char == ".":
                if pontos == 1 or not (self._proximo() and self._proximo().isdigit()):
                    break
                pontos += 1
                texto += char
                self._avancar()
                continue

            if not char.isdigit():
                break

            texto += char
            self._avancar()

        valor = float(texto) if pontos else int(texto)
        self._adicionar(TipoToken.NUMERO, valor, linha, coluna)

    def _ler_string(self):
        aspas = self._caractere_atual()
        linha, coluna = self.linha, self.coluna
        self._avancar()
        texto = ""

        escapes = {
            "n": "\n",
            "t": "\t",
            "r": "\r",
            '"': '"',
            "'": "'",
            "\\": "\\",
        }

        while self._caractere_atual() is not None and self._caractere_atual() != aspas:
            char = self._caractere_atual()

            if char == "\n":
                raise LexicalError("String nao finalizada.", linha, coluna)

            if char == "\\":
                self._avancar()
                escape = self._caractere_atual()
                if escape is None:
                    raise LexicalError("Escape incompleto na string.", self.linha, self.coluna)
                texto += escapes.get(escape, escape)
                self._avancar()
                continue

            texto += char
            self._avancar()

        if self._caractere_atual() != aspas:
            raise LexicalError("String nao finalizada.", linha, coluna)

        self._avancar()
        self._adicionar(TipoToken.STRING, texto, linha, coluna)

    def _ler_identificador(self):
        linha, coluna = self.linha, self.coluna
        texto = ""

        while self._caractere_atual() and (
            self._caractere_atual().isalnum() or self._caractere_atual() == "_"
        ):
            texto += self._caractere_atual()
            self._avancar()

        if texto in self.BOOLEANOS:
            self._adicionar(TipoToken.BOOLEANO, self.BOOLEANOS[texto], linha, coluna)
            return

        if texto == "nulo":
            self._adicionar(TipoToken.NULO, None, linha, coluna)
            return

        tipo = self.PALAVRAS_CHAVE.get(texto, TipoToken.IDENTIFICADOR)
        self._adicionar(tipo, texto, linha, coluna)

    def _ler_operador_ou_simbolo(self):
        linha, coluna = self.linha, self.coluna
        char = self._caractere_atual()
        proximo = self._proximo()

        compostos = {
            "==": TipoToken.IGUALDADE,
            "!=": TipoToken.DIFERENTE,
            ">=": TipoToken.MAIOR_IGUAL,
            "<=": TipoToken.MENOR_IGUAL,
            "&&": TipoToken.AND,
            "||": TipoToken.OR,
        }

        par = f"{char}{proximo or ''}"
        if par in compostos:
            self._adicionar(compostos[par], par, linha, coluna)
            self._avancar()
            self._avancar()
            return

        if char == "=":
            self._adicionar(TipoToken.ATRIBUICAO, char, linha, coluna)
        elif char == ">":
            self._adicionar(TipoToken.MAIOR, char, linha, coluna)
        elif char == "<":
            self._adicionar(TipoToken.MENOR, char, linha, coluna)
        elif char == "!":
            self._adicionar(TipoToken.NOT, char, linha, coluna)
        elif char in self.SIMPLES:
            self._adicionar(self.SIMPLES[char], char, linha, coluna)
        else:
            raise LexicalError(f"Caractere invalido '{char}'.", linha, coluna)

        self._avancar()
