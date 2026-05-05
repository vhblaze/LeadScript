import asyncio
import inspect

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
from errors import RuntimeErrorCustom
from lexico import TipoToken


class Environment:
    """Escopo de execucao com variaveis do script e funcoes nativas.

    As funcoes de dominio sao corrotinas. Hoje elas sao mocks, mas a fronteira
    assincrona ja permite trocar por HTTP, SMTP, filas ou LLMs reais sem mudar o
    parser nem a AST.
    """

    def __init__(self):
        self.values = {
            "payload": {
                "nome": "Ana Silva",
                "email": "ana@empresa-b2b.com",
                "empresa": "Unitri Leads",
                "segmento": "B2B",
                "origem": "webhook",
            }
        }
        self.builtins = {
            "extrair_payload": self.extrair_payload,
            "classificar_ia": self.classificar_ia,
            "disparar_webhook": self.disparar_webhook,
            "enviar_email": self.enviar_email,
            "enviar_discord": self.enviar_discord,
        }

    def get(self, name, line=None, column=None):
        if name in self.values:
            return self.values[name]
        if name in self.builtins:
            return self.builtins[name]
        raise RuntimeErrorCustom(
            f"Variavel ou funcao '{name}' nao definida.",
            line,
            column,
        )

    def set(self, name, value):
        self.values[name] = value
        return value

    async def extrair_payload(self):
        await asyncio.sleep(0.05)
        lead = dict(self.values["payload"])
        print(f"[leadscript] payload extraido para {lead['email']}")
        return lead

    async def classificar_ia(self, lead, prompt):
        await asyncio.sleep(0.08)
        texto = f"{lead} {prompt}".lower()
        score = 92 if "b2b" in texto else 55
        print(f"[leadscript] lead classificado com score {score}")
        return score

    async def disparar_webhook(self, url, lead):
        await asyncio.sleep(0.05)
        print(f"[leadscript] POST {url} lead={lead.get('email', '<sem-email>')}")
        return {"status": "ok", "destino": url}

    async def enviar_email(self, para, assunto, template):
        await asyncio.sleep(0.05)
        print(f"[leadscript] email para {para}: {assunto} ({template})")
        return {"status": "enviado", "para": para}

    async def enviar_discord(self, webhook_url, mensagem):
        await asyncio.sleep(0.05)
        print(f"[leadscript] discord {webhook_url}: {mensagem}")
        return {"status": "notificado"}


class Interpreter:
    def __init__(self, environment=None):
        self.env = environment or Environment()

    async def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise RuntimeErrorCustom(
                f"No desconhecido: {type(node).__name__}.",
                getattr(node, "line", None),
                getattr(node, "column", None),
            )
        return await method(node)

    async def visit_BlockNode(self, node: BlockNode):
        result = None
        for statement in node.statements:
            result = await self.visit(statement)
        return result

    async def visit_NumberNode(self, node: NumberNode):
        return node.value

    async def visit_StringNode(self, node: StringNode):
        return node.value

    async def visit_BooleanNode(self, node: BooleanNode):
        return node.value

    async def visit_NullNode(self, node: NullNode):
        return node.value

    async def visit_ListNode(self, node: ListNode):
        return [await self.visit(element) for element in node.elements]

    async def visit_DictNode(self, node: DictNode):
        result = {}
        for key_node, value_node in node.pairs:
            key = await self.visit(key_node)
            value = await self.visit(value_node)
            result[key] = value
        return result

    async def visit_VarAccessNode(self, node: VarAccessNode):
        return self.env.get(node.name, node.line, node.column)

    async def visit_VarAssignNode(self, node: VarAssignNode):
        value = await self.visit(node.value)
        return self.env.set(node.name, value)

    async def visit_IndexAccessNode(self, node: IndexAccessNode):
        target = await self.visit(node.target)
        index = await self.visit(node.index)

        try:
            return target[index]
        except (KeyError, IndexError, TypeError):
            raise RuntimeErrorCustom(
                f"Nao foi possivel acessar indice/chave {index!r}.",
                node.line,
                node.column,
            )

    async def visit_PropertyAccessNode(self, node: PropertyAccessNode):
        target = await self.visit(node.target)

        if isinstance(target, dict):
            try:
                return target[node.property_name]
            except KeyError:
                raise RuntimeErrorCustom(
                    f"Propriedade '{node.property_name}' nao existe.",
                    node.line,
                    node.column,
                )

        if hasattr(target, node.property_name):
            return getattr(target, node.property_name)

        raise RuntimeErrorCustom(
            f"Objeto nao possui propriedade '{node.property_name}'.",
            node.line,
            node.column,
        )

    async def visit_ExpressionStatementNode(self, node: ExpressionStatementNode):
        return await self.visit(node.expr)

    async def visit_FunctionCallNode(self, node: FunctionCallNode):
        function = await self.visit(node.callee)
        if not callable(function):
            raise RuntimeErrorCustom(
                "Tentativa de chamar um valor que nao e funcao.",
                node.line,
                node.column,
            )

        args = [await self.visit(arg) for arg in node.args]
        try:
            result = function(*args)
            if inspect.isawaitable(result):
                return await result
            return result
        except RuntimeErrorCustom:
            raise
        except TypeError as exc:
            raise RuntimeErrorCustom(
                f"Argumentos invalidos na chamada de '{self._callable_name(node)}': {exc}.",
                node.line,
                node.column,
            ) from exc
        except Exception as exc:
            raise RuntimeErrorCustom(
                f"Falha ao executar funcao nativa '{self._callable_name(node)}': {exc}.",
                node.line,
                node.column,
            ) from exc

    async def visit_IfNode(self, node: IfNode):
        condition = await self.visit(node.condition)

        if self._is_truthy(condition):
            return await self.visit(node.then_block)

        if node.else_block is not None:
            return await self.visit(node.else_block)

        return None

    async def visit_ForNode(self, node: ForNode):
        iterable = await self.visit(node.iterable)
        if not hasattr(iterable, "__iter__"):
            raise RuntimeErrorCustom(
                "Objeto usado em 'para cada' nao e iteravel.",
                node.line,
                node.column,
            )

        result = None
        previous = self.env.values.get(node.var_name)
        had_previous = node.var_name in self.env.values

        for item in iterable:
            self.env.set(node.var_name, item)
            result = await self.visit(node.body)

        if had_previous:
            self.env.set(node.var_name, previous)
        else:
            self.env.values.pop(node.var_name, None)

        return result

    async def visit_UnaryOpNode(self, node: UnaryOpNode):
        value = await self.visit(node.expr)

        if node.op.tipo == TipoToken.NOT:
            return not self._is_truthy(value)
        if node.op.tipo == TipoToken.SUB:
            return -value

        raise RuntimeErrorCustom(
            f"Operador unario nao suportado: {node.op.valor}.",
            node.line,
            node.column,
        )

    async def visit_BinaryOpNode(self, node: BinaryOpNode):
        if node.op.tipo == TipoToken.AND:
            left = await self.visit(node.left)
            return self._is_truthy(left) and self._is_truthy(await self.visit(node.right))

        if node.op.tipo == TipoToken.OR:
            left = await self.visit(node.left)
            return self._is_truthy(left) or self._is_truthy(await self.visit(node.right))

        left = await self.visit(node.left)
        right = await self.visit(node.right)
        op = node.op.tipo

        try:
            if op == TipoToken.SOMA:
                return left + right
            if op == TipoToken.SUB:
                return left - right
            if op == TipoToken.MULT:
                return left * right
            if op == TipoToken.DIV:
                return left / right
            if op == TipoToken.MOD:
                return left % right
            if op == TipoToken.MAIOR:
                return left > right
            if op == TipoToken.MENOR:
                return left < right
            if op == TipoToken.MAIOR_IGUAL:
                return left >= right
            if op == TipoToken.MENOR_IGUAL:
                return left <= right
            if op == TipoToken.IGUALDADE:
                return left == right
            if op == TipoToken.DIFERENTE:
                return left != right
        except (TypeError, ZeroDivisionError) as exc:
            raise RuntimeErrorCustom(
                f"Erro ao aplicar operador '{node.op.valor}': {exc}.",
                node.line,
                node.column,
            ) from exc

        raise RuntimeErrorCustom(
            f"Operador binario nao suportado: {node.op.valor}.",
            node.line,
            node.column,
        )

    def _is_truthy(self, value):
        return bool(value)

    def _callable_name(self, node):
        callee = node.callee
        return getattr(callee, "name", "<expressao>")
