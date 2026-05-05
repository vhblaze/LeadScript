from ast_nodes import (
    BinaryOpNode,
    BlockNode,
    BooleanNode,
    DictNode,
    ExpressionStatementNode,
    ForNode,
    FunctionCallNode,
    IfNode,
    IndexAccessNode,
    ListNode,
    NullNode,
    NumberNode,
    PropertyAccessNode,
    StringNode,
    UnaryOpNode,
    VarAccessNode,
    VarAssignNode,
)
from errors import SyntaxErrorCustom
from lexico import TipoToken


class Parser:
    """Parser de descida recursiva da LeadScript.

    O parser transforma tokens em AST preservando linha/coluna em cada no.
    Isso permite diagnosticos de producao sem abandonar a arquitetura classica
    Lexer -> Parser -> AST -> Interpreter.
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):
        statements = self._parse_block_until({TipoToken.EOF})
        self._expect(TipoToken.EOF)
        return BlockNode(statements, line=1, column=1)

    def _current(self):
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def _peek(self, offset=1):
        index = self.pos + offset
        if index >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[index]

    def _advance(self):
        token = self._current()
        self.pos += 1
        return token

    def _match(self, *tipos):
        if self._current().tipo in tipos:
            return self._advance()
        return None

    def _syntax_error(self, message, token=None):
        token = token or self._current()
        raise SyntaxErrorCustom(message, token.linha, token.coluna)

    def _expect(self, tipo, message=None):
        token = self._current()
        if token.tipo == tipo:
            return self._advance()

        if message is None:
            message = f"Esperado '{tipo.value}', encontrado '{token.valor or token.tipo.value}'."
        self._syntax_error(message, token)

    def _skip_separators(self):
        while self._current().tipo in (TipoToken.NOVA_LINHA, TipoToken.PONTO_VIRGULA):
            self._advance()

    def _finish_statement(self):
        if self._current().tipo in (
            TipoToken.NOVA_LINHA,
            TipoToken.PONTO_VIRGULA,
            TipoToken.EOF,
            TipoToken.SENAO,
            TipoToken.FIM,
        ):
            self._skip_separators()
            return

        token = self._current()
        self._syntax_error(
            f"Fim de comando esperado antes de '{token.valor or token.tipo.value}'.",
            token,
        )

    def _parse_block_until(self, stop_tokens, missing_message=None):
        statements = []

        while self._current().tipo not in stop_tokens:
            self._skip_separators()
            if self._current().tipo in stop_tokens:
                break
            if self._current().tipo == TipoToken.EOF and TipoToken.EOF not in stop_tokens:
                self._syntax_error(missing_message or "Bloco nao finalizado com 'fim'.")
            statements.append(self._parse_statement())

        return statements

    def _parse_statement(self):
        token = self._current()

        if token.tipo == TipoToken.SE:
            return self._parse_if()

        if token.tipo == TipoToken.PARA:
            return self._parse_for()

        if token.tipo == TipoToken.SENAO:
            self._syntax_error("'senao' sem 'se' correspondente.", token)

        if token.tipo == TipoToken.FIM:
            self._syntax_error("'fim' sem bloco correspondente.", token)

        if (
            token.tipo == TipoToken.IDENTIFICADOR
            and self._peek().tipo == TipoToken.ATRIBUICAO
        ):
            stmt = self._parse_assignment()
        else:
            expr = self._parse_expression()
            stmt = ExpressionStatementNode(
                expr,
                line=getattr(expr, "line", token.linha),
                column=getattr(expr, "column", token.coluna),
            )

        self._finish_statement()
        return stmt

    def _parse_assignment(self):
        name_token = self._expect(TipoToken.IDENTIFICADOR)
        self._expect(TipoToken.ATRIBUICAO)
        value = self._parse_expression()
        return VarAssignNode(
            name_token.valor,
            value,
            line=name_token.linha,
            column=name_token.coluna,
        )

    def _parse_if(self):
        se_token = self._expect(TipoToken.SE)
        condition = self._parse_expression()
        self._expect(
            TipoToken.ENTAO,
            "Esperado 'entao:' apos a condicao.",
        )
        self._expect(
            TipoToken.DOIS_PONTOS,
            "Esperado ':' depois de 'entao'.",
        )
        self._skip_separators()

        then_block = BlockNode(
            self._parse_block_until(
                {TipoToken.SENAO, TipoToken.FIM},
                "Bloco 'se' nao finalizado. Esperado 'fim'.",
            ),
            line=se_token.linha,
            column=se_token.coluna,
        )

        else_block = None
        if self._match(TipoToken.SENAO):
            self._expect(
                TipoToken.DOIS_PONTOS,
                "Esperado ':' depois de 'senao'.",
            )
            self._skip_separators()
            else_block = BlockNode(
                self._parse_block_until(
                    {TipoToken.FIM},
                    "Bloco 'senao' nao finalizado. Esperado 'fim'.",
                ),
                line=se_token.linha,
                column=se_token.coluna,
            )

        self._expect(TipoToken.FIM, "Esperado 'fim' para fechar o bloco 'se'.")
        self._finish_statement()
        return IfNode(
            condition,
            then_block,
            else_block,
            line=se_token.linha,
            column=se_token.coluna,
        )

    def _parse_for(self):
        para_token = self._expect(TipoToken.PARA)
        self._expect(TipoToken.CADA, "Esperado 'cada' depois de 'para'.")
        var_token = self._expect(TipoToken.IDENTIFICADOR, "Esperado variavel de iteracao.")
        self._expect(TipoToken.EM, "Esperado 'em' depois da variavel de iteracao.")
        iterable = self._parse_expression()
        self._expect(TipoToken.ENTAO, "Esperado 'entao:' depois do iteravel.")
        self._expect(TipoToken.DOIS_PONTOS, "Esperado ':' depois de 'entao'.")
        self._skip_separators()

        body = BlockNode(
            self._parse_block_until(
                {TipoToken.FIM},
                "Bloco 'para cada' nao finalizado. Esperado 'fim'.",
            ),
            line=para_token.linha,
            column=para_token.coluna,
        )
        self._expect(TipoToken.FIM, "Esperado 'fim' para fechar o bloco 'para cada'.")
        self._finish_statement()
        return ForNode(
            var_token.valor,
            iterable,
            body,
            line=para_token.linha,
            column=para_token.coluna,
        )

    def _parse_expression(self):
        return self._parse_or()

    def _parse_or(self):
        node = self._parse_and()

        while self._current().tipo == TipoToken.OR:
            op = self._advance()
            right = self._parse_and()
            node = BinaryOpNode(node, op, right, line=op.linha, column=op.coluna)

        return node

    def _parse_and(self):
        node = self._parse_equality()

        while self._current().tipo == TipoToken.AND:
            op = self._advance()
            right = self._parse_equality()
            node = BinaryOpNode(node, op, right, line=op.linha, column=op.coluna)

        return node

    def _parse_equality(self):
        node = self._parse_comparison()

        while self._current().tipo in (TipoToken.IGUALDADE, TipoToken.DIFERENTE):
            op = self._advance()
            right = self._parse_comparison()
            node = BinaryOpNode(node, op, right, line=op.linha, column=op.coluna)

        return node

    def _parse_comparison(self):
        node = self._parse_term()

        while self._current().tipo in (
            TipoToken.MAIOR,
            TipoToken.MENOR,
            TipoToken.MAIOR_IGUAL,
            TipoToken.MENOR_IGUAL,
        ):
            op = self._advance()
            right = self._parse_term()
            node = BinaryOpNode(node, op, right, line=op.linha, column=op.coluna)

        return node

    def _parse_term(self):
        node = self._parse_factor()

        while self._current().tipo in (TipoToken.SOMA, TipoToken.SUB):
            op = self._advance()
            right = self._parse_factor()
            node = BinaryOpNode(node, op, right, line=op.linha, column=op.coluna)

        return node

    def _parse_factor(self):
        node = self._parse_unary()

        while self._current().tipo in (TipoToken.MULT, TipoToken.DIV, TipoToken.MOD):
            op = self._advance()
            right = self._parse_unary()
            node = BinaryOpNode(node, op, right, line=op.linha, column=op.coluna)

        return node

    def _parse_unary(self):
        if self._current().tipo in (TipoToken.NOT, TipoToken.SUB):
            op = self._advance()
            return UnaryOpNode(op, self._parse_unary(), line=op.linha, column=op.coluna)

        return self._parse_postfix()

    def _parse_postfix(self):
        node = self._parse_primary()

        while True:
            if self._current().tipo == TipoToken.LPAREN:
                paren_token = self._advance()
                args = []
                self._skip_separators()
                if self._current().tipo != TipoToken.RPAREN:
                    args.append(self._parse_expression())
                    self._skip_separators()
                    while self._match(TipoToken.VIRGULA):
                        self._skip_separators()
                        args.append(self._parse_expression())
                        self._skip_separators()

                self._expect(TipoToken.RPAREN, "Esperado ')' para fechar chamada de funcao.")
                node = FunctionCallNode(node, args, line=paren_token.linha, column=paren_token.coluna)
                continue

            if self._current().tipo == TipoToken.LBRACKET:
                bracket_token = self._advance()
                index = self._parse_expression()
                self._expect(TipoToken.RBRACKET, "Esperado ']' para fechar acesso por indice.")
                node = IndexAccessNode(node, index, line=bracket_token.linha, column=bracket_token.coluna)
                continue

            if self._current().tipo == TipoToken.PONTO:
                dot_token = self._advance()
                property_name = self._expect(
                    TipoToken.IDENTIFICADOR,
                    "Esperado nome de propriedade depois de '.'.",
                ).valor
                node = PropertyAccessNode(
                    node,
                    property_name,
                    line=dot_token.linha,
                    column=dot_token.coluna,
                )
                continue

            break

        return node

    def _parse_primary(self):
        token = self._current()

        if token.tipo == TipoToken.NUMERO:
            self._advance()
            return NumberNode(token.valor, line=token.linha, column=token.coluna)

        if token.tipo == TipoToken.STRING:
            self._advance()
            return StringNode(token.valor, line=token.linha, column=token.coluna)

        if token.tipo == TipoToken.BOOLEANO:
            self._advance()
            return BooleanNode(token.valor, line=token.linha, column=token.coluna)

        if token.tipo == TipoToken.NULO:
            self._advance()
            return NullNode(line=token.linha, column=token.coluna)

        if token.tipo == TipoToken.IDENTIFICADOR:
            self._advance()
            return VarAccessNode(token.valor, line=token.linha, column=token.coluna)

        if token.tipo == TipoToken.LPAREN:
            self._advance()
            node = self._parse_expression()
            self._expect(TipoToken.RPAREN, "Esperado ')' para fechar expressao.")
            return node

        if token.tipo == TipoToken.LBRACKET:
            return self._parse_list()

        if token.tipo == TipoToken.LBRACE:
            return self._parse_dict()

        self._syntax_error(
            f"Expressao inesperada '{token.valor or token.tipo.value}'.",
            token,
        )

    def _parse_list(self):
        start_token = self._expect(TipoToken.LBRACKET)
        elements = []
        self._skip_separators()

        if self._current().tipo != TipoToken.RBRACKET:
            elements.append(self._parse_expression())
            self._skip_separators()
            while self._match(TipoToken.VIRGULA):
                self._skip_separators()
                elements.append(self._parse_expression())
                self._skip_separators()

        self._expect(TipoToken.RBRACKET, "Esperado ']' para fechar lista.")
        return ListNode(elements, line=start_token.linha, column=start_token.coluna)

    def _parse_dict(self):
        start_token = self._expect(TipoToken.LBRACE)
        pairs = []
        self._skip_separators()

        if self._current().tipo != TipoToken.RBRACE:
            pairs.append(self._parse_dict_pair())
            self._skip_separators()
            while self._match(TipoToken.VIRGULA):
                self._skip_separators()
                pairs.append(self._parse_dict_pair())
                self._skip_separators()

        self._expect(TipoToken.RBRACE, "Esperado '}' para fechar dicionario.")
        return DictNode(pairs, line=start_token.linha, column=start_token.coluna)

    def _parse_dict_pair(self):
        key_token = self._current()

        if key_token.tipo == TipoToken.STRING:
            key = StringNode(
                self._advance().valor,
                line=key_token.linha,
                column=key_token.coluna,
            )
        elif key_token.tipo == TipoToken.IDENTIFICADOR:
            key = StringNode(
                self._advance().valor,
                line=key_token.linha,
                column=key_token.coluna,
            )
        else:
            self._syntax_error("Chave de dicionario deve ser string ou identificador.", key_token)

        self._expect(TipoToken.DOIS_PONTOS, "Esperado ':' depois da chave do dicionario.")
        value = self._parse_expression()
        return key, value
