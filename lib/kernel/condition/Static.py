import re
from typing import Any, List, Dict, Callable, Optional, Pattern, Union

from kernel.condition.base import (
    ConditionASTNode,
    ConditionExprNode,
    ConditionLogicalNode,
    ConditionalAST,
)


def _wildcard_to_regex(pattern: str) -> str:
    """
    Converts a pattern string containing wildcards (* and ?) or SQL-LIKE wildcards (% and _)
    into a valid regular expression string.
    """
    res = []
    # Tokenize escaped characters and wildcards
    tokens = re.findall(r'(\\\\|\\%|\\_|\*|\?|\%|_|.)', pattern, re.DOTALL)
    for t in tokens:
        if t in ('*', '%'):
            res.append('.*')
        elif t in ('?', '_'):
            res.append('.')
        elif t in (r'\%', r'\_'):
            res.append(re.escape(t[-1]))
        elif t == r'\\':
            res.append(re.escape('\\'))
        else:
            res.append(re.escape(t))
    return '^' + ''.join(res) + '$'


class ConditionStatic:
    """
    Compiles a Condition AST (from base.py) into a high-performance Python matcher function.
    """

    def __init__(self, case_sensitive: bool = True):
        self.case_sensitive = case_sensitive

    def compile(
        self, ast: Optional[Union[ConditionalAST, ConditionASTNode]]
    ) -> Callable[[Dict[str, Any]], bool]:
        """
        Compiles the given AST into a executable Python callable taking a dict record.
        """
        # Unwrap if a ConditionalAST instance was provided
        root_node = getattr(ast, "getAST", lambda: ast)()
        if isinstance(root_node, ConditionalAST):
            root_node = root_node.getAST()

        if not root_node or not isinstance(root_node, ConditionASTNode):
            return lambda d: True

        env = {
            '_check_eq': self._check_eq,
            '_check_gt': self._check_gt,
            '_check_ge': self._check_ge,
            '_check_lt': self._check_lt,
            '_check_le': self._check_le,
            '_check_like': self._check_like,
            're': re,
        }
        regex_counter = 0

        def _build_expr(node: ConditionASTNode) -> str:
            nonlocal regex_counter

            if isinstance(node, ConditionExprNode):
                # Extract field name from the Field object (fallback to str(node.field))
                fld_obj = node.field
                fld_name = getattr(fld_obj, "name", str(fld_obj))
                
                field_repr = repr(fld_name)
                val_repr = repr(node.value)
                op = node.op.upper()

                expr_code = ""

                if op == "=":
                    expr_code = f"_check_eq(d.get({field_repr}), {val_repr})"
                elif op == ">":
                    expr_code = f"_check_gt(d.get({field_repr}), {val_repr})"
                elif op == ">=":
                    expr_code = f"_check_ge(d.get({field_repr}), {val_repr})"
                elif op == "<":
                    expr_code = f"_check_lt(d.get({field_repr}), {val_repr})"
                elif op == "<=":
                    expr_code = f"_check_le(d.get({field_repr}), {val_repr})"
                elif op == "LIKE":
                    regex_counter += 1
                    reg_key = f"_reg_{regex_counter}"
                    pattern_str = _wildcard_to_regex(str(node.value))
                    flags = 0 if self.case_sensitive else re.IGNORECASE
                    env[reg_key] = re.compile(pattern_str, re.DOTALL | flags)
                    expr_code = f"_check_like(d.get({field_repr}), {reg_key})"
                else:
                    # Fallback for unknown operators -> equality check
                    expr_code = f"_check_eq(d.get({field_repr}), {val_repr})"

                # Apply negation if specified in AST node
                if node.negate:
                    expr_code = f"(not ({expr_code}))"

                return expr_code

            elif isinstance(node, ConditionLogicalNode):
                if not node.children:
                    return "True"

                child_exprs = [_build_expr(child) for child in node.children]
                child_exprs = [e for e in child_exprs if e]

                if not child_exprs:
                    return "True"
                if len(child_exprs) == 1:
                    return child_exprs[0]

                join_operator = " and " if node.logical_op == "AND" else " or "
                return f"({join_operator.join(child_exprs)})"

            return "True"

        body_expr = _build_expr(root_node)
        func_code = f"def matcher(d):\n    return bool({body_expr})"

        # Dynamically compile and execute python function
        exec(func_code, env)
        matcher = env['matcher']

        # Attach generated Python source code string for debugging purposes
        matcher.__source__ = func_code
        return matcher

    # --- Static Evaluator Helpers ---

    @staticmethod
    def _to_comparable(val: Any, target: Any) -> tuple:
        """Attempts numeric comparison if target is numeric, otherwise defaults to string comparison."""
        if isinstance(target, (int, float)):
            try:
                return float(val), float(target)
            except (ValueError, TypeError):
                pass
        return str(val), str(target)

    @classmethod
    def _check_eq(cls, val: Any, target: Any) -> bool:
        """Fast equality check supporting scalar values and lists."""
        if val is None:
            return False
        if val == target:
            return True
        if isinstance(val, list):
            return any(cls._check_eq(x, target) for x in val)
        return str(val) == str(target)

    @classmethod
    def _check_gt(cls, val: Any, target: Any) -> bool:
        """Greater than (>) comparison."""
        if val is None:
            return False
        if isinstance(val, list):
            return any(cls._check_gt(x, target) for x in val if x is not None)
        v, t = cls._to_comparable(val, target)
        return v > t

    @classmethod
    def _check_ge(cls, val: Any, target: Any) -> bool:
        """Greater than or equal (>=) comparison."""
        if val is None:
            return False
        if isinstance(val, list):
            return any(cls._check_ge(x, target) for x in val if x is not None)
        v, t = cls._to_comparable(val, target)
        return v >= t

    @classmethod
    def _check_lt(cls, val: Any, target: Any) -> bool:
        """Less than (<) comparison."""
        if val is None:
            return False
        if isinstance(val, list):
            return any(cls._check_lt(x, target) for x in val if x is not None)
        v, t = cls._to_comparable(val, target)
        return v < t

    @classmethod
    def _check_le(cls, val: Any, target: Any) -> bool:
        """Less than or equal (<=) comparison."""
        if val is None:
            return False
        if isinstance(val, list):
            return any(cls._check_le(x, target) for x in val if x is not None)
        v, t = cls._to_comparable(val, target)
        return v <= t

    @staticmethod
    def _check_like(val: Any, regex: Pattern) -> bool:
        """LIKE pattern check using pre-compiled regex."""
        if val is None:
            return False
        if isinstance(val, list):
            return any(regex.match(str(x)) is not None for x in val if x is not None)
        return regex.match(str(val)) is not None


def compile_static(
    ast: Union[ConditionalAST, ConditionASTNode], case_sensitive: bool = True
) -> Callable[[Dict[str, Any]], bool]:
    """
    Helper function to compile a Condition AST directly into a matcher function.
    """
    compiler = ConditionStatic(case_sensitive=case_sensitive)
    return compiler.compile(ast)

