from typing import Any, Optional
from kernel.condition import (
    ConditionASTNode,
    ConditionExprNode,
    ConditionLogicalNode,
    ConditionalAST,
)


class ConditionServiceNow:
    """
    Compiles a ConditionalAST into a ServiceNow encoded query string (sysparm_query).
    """

    def __init__(self, ast: Optional[ConditionalAST] = None):
        self.ast = ast

    def _get_backend_name(self, field_obj: Any) -> str:
        """
        Extracts the ServiceNow field name from the field object.
        Prefers field_obj.backendname, then field_obj.name, then str(field_obj).
        """
        if hasattr(field_obj, "backendname") and field_obj.backendname:
            return str(field_obj.backendname)
        if hasattr(field_obj, "name") and field_obj.name:
            return str(field_obj.name)
        return str(field_obj)

    def _compile_expr_node(self, node: ConditionExprNode) -> str:
        """
        Translates a single ConditionExprNode to a ServiceNow query operator statement.
        """
        field_name = self._get_backend_name(node.field)
        op = node.op.upper()
        val = str(node.value) if node.value is not None else ""
        negate = node.negate

        # 1. Wildcard / LIKE Translations

#        if op in ("LIKE", "STARTSWITH"):
#            # Egal ob * am Ende steht oder ein Präfix gesucht wird:
#            # Wir übersetzen Präfix-Suchen auf den stabilen LIKE-Operator
#            clean_val = val.rstrip("*")
#            
#            if negate:
#                return f"{field_name}NOTLIKE{clean_val}"
#            else:
#                return f"{field_name}LIKE{clean_val}"

        if op == "LIKE":
            has_leading_star = val.startswith("*")
            has_trailing_star = val.endswith("*")

            # Clean outer stars for ServiceNow operators
            clean_val = val
            if has_leading_star:
                clean_val = clean_val[1:]
            if has_trailing_star:
                clean_val = clean_val[:-1]

            if has_leading_star and has_trailing_star:
                sn_op = "NOTLIKE" if negate else "LIKE"
            elif has_trailing_star:
                sn_op = "NOTSTARTSWITH" if negate else "STARTSWITH"
            elif has_leading_star:
                sn_op = "NOTENDSWITH" if negate else "ENDSWITH"
            else:
                # Fallback for inner wildcards or general LIKE
                sn_op = "NOTLIKE" if negate else "LIKE"

            return f"{field_name}{sn_op}{clean_val}"

        # 2. Standard Comparison Operators
        op_map = {
            "=": "!=" if negate else "=",
            "!=": "=" if negate else "!=",
            ">": "<=" if negate else ">",
            ">=": "<" if negate else ">=",
            "<": ">=" if negate else "<",
            "<=": ">" if negate else "<=",
        }

        sn_op = op_map.get(op, "!=" if negate else "=")
        return f"{field_name}{sn_op}{val}"

    def _compile_node(self, node: ConditionASTNode) -> str:
        """
        Recursively traverses AST nodes to build the ServiceNow encoded query.
        """
        if isinstance(node, ConditionExprNode):
            return self._compile_expr_node(node)

        elif isinstance(node, ConditionLogicalNode):
            if not node.children:
                return ""

            compiled_children = []
            for child in node.children:
                child_query = self._compile_node(child)
                if child_query:
                    compiled_children.append(child_query)

            if not compiled_children:
                return ""

            if len(compiled_children) == 1:
                return compiled_children[0]

            logical_op = node.logical_op.upper()

            # ServiceNow join syntax:
            # AND: item1^item2
            # OR:  item1^ORitem2
            if logical_op == "OR":
                return "^OR".join(compiled_children)
            else:  # AND
                return "^".join(compiled_children)

        return ""

    def compile(self, ast: Optional[Any] = None) -> str:
        """
        Compiles the AST into a ServiceNow sysparm_query string.
        Accepts either a ConditionalAST wrapper or a raw ConditionASTNode.
        """
        target = ast if ast is not None else self.ast

        if not target:
            return ""

        # Handle both ConditionalAST wrapper and direct ConditionASTNode
        root_node = getattr(target, "_AST", target)
        root_node = getattr(root_node, "root", root_node)

        if not isinstance(root_node, ConditionASTNode):
            return ""

        query_str = self._compile_node(root_node)

        # Cleanup trailing or double query delimiters if any
        query_str = query_str.strip("^")

        return query_str


def compile_servicenow(ast: ConditionalAST) -> str:
    """
    Helper function to directly compile a ConditionalAST to a ServiceNow sysparm_query string.
    """
    compiler = ConditionServiceNow(ast)
    return compiler.compile()

