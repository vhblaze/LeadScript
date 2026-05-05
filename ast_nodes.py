from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


@dataclass
class NumberNode:
    value: float | int
    line: int | None = None
    column: int | None = None


@dataclass
class StringNode:
    value: str
    line: int | None = None
    column: int | None = None


@dataclass
class BooleanNode:
    value: bool
    line: int | None = None
    column: int | None = None


@dataclass
class NullNode:
    value: None = None
    line: int | None = None
    column: int | None = None


@dataclass
class ListNode:
    elements: List[Any]
    line: int | None = None
    column: int | None = None


@dataclass
class DictNode:
    pairs: List[Tuple[Any, Any]]
    line: int | None = None
    column: int | None = None


@dataclass
class VarAccessNode:
    name: str
    line: int | None = None
    column: int | None = None


@dataclass
class VarAssignNode:
    name: str
    value: Any
    line: int | None = None
    column: int | None = None


@dataclass
class IndexAccessNode:
    target: Any
    index: Any
    line: int | None = None
    column: int | None = None


@dataclass
class PropertyAccessNode:
    target: Any
    property_name: str
    line: int | None = None
    column: int | None = None


@dataclass
class BinaryOpNode:
    left: Any
    op: Any
    right: Any
    line: int | None = None
    column: int | None = None


@dataclass
class UnaryOpNode:
    op: Any
    expr: Any
    line: int | None = None
    column: int | None = None


@dataclass
class FunctionCallNode:
    callee: Any
    args: List[Any]
    line: int | None = None
    column: int | None = None


@dataclass
class ExpressionStatementNode:
    expr: Any
    line: int | None = None
    column: int | None = None


@dataclass
class IfNode:
    condition: Any
    then_block: Any
    else_block: Optional[Any] = None
    line: int | None = None
    column: int | None = None


@dataclass
class ForNode:
    var_name: str
    iterable: Any
    body: Any
    line: int | None = None
    column: int | None = None


@dataclass
class BlockNode:
    statements: List[Any]
    line: int | None = None
    column: int | None = None
