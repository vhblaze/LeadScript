class LeadScriptError(Exception):
    error_name = "Erro LeadScript"

    def __init__(
        self,
        message,
        line=None,
        column=None,
        filename=None,
        source=None,
    ):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename
        self.source = source

    def with_context(self, filename=None, source=None):
        if filename is not None:
            self.filename = filename
        if source is not None:
            self.source = source
        return self

    def format(self):
        location = self._format_location()
        source_excerpt = self._format_source_excerpt()

        if source_excerpt:
            return f"{location}\n{source_excerpt}\n    {self.message}"
        return f"{location}\n    {self.message}"

    def _format_location(self):
        filename = f" no arquivo '{self.filename}'" if self.filename else ""
        if self.line is not None and self.column is not None:
            return (
                f"{self.error_name}{filename} na linha {self.line}, "
                f"coluna {self.column}:"
            )
        if self.line is not None:
            return f"{self.error_name}{filename} na linha {self.line}:"
        return f"{self.error_name}{filename}:"

    def _format_source_excerpt(self):
        if not self.source or self.line is None:
            return ""

        linhas = self.source.splitlines()
        if self.line < 1 or self.line > len(linhas):
            return ""

        linha_codigo = linhas[self.line - 1].rstrip("\n")
        coluna = max((self.column or 1) - 1, 0)
        ponteiro = " " * coluna + "^"
        return f"    {linha_codigo}\n    {ponteiro}"

    def __str__(self):
        return self.format()


class LeadScriptLexicalError(LeadScriptError):
    error_name = "Erro Lexico"


class LeadScriptSyntaxError(LeadScriptError):
    error_name = "Erro de Sintaxe"


class LeadScriptRuntimeError(LeadScriptError):
    error_name = "Erro de Execucao"


# Aliases mantidos para compatibilidade com imports antigos do projeto.
LexicalError = LeadScriptLexicalError
SyntaxErrorCustom = LeadScriptSyntaxError
RuntimeErrorCustom = LeadScriptRuntimeError
