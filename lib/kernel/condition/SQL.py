from typing import Any, Dict, Tuple, Optional
from kernel.condition import *


class ConditionSQL:
   """
   Compiles a ConditionalAST into SQL WHERE clause expressions and parameters.
   """

   def __init__(self, ast: Optional[ConditionalAST] = None):
      self.ast = ast
      self._param_counter = 0

   def _get_backend_name(self, field_obj: Any) -> str:
      """
      Extracts the backend column name from the field object.
      """
      if hasattr(field_obj, "backendname") and field_obj.backendname:
         return str(field_obj.backendname)
      if hasattr(field_obj, "name") and field_obj.name:
         return str(field_obj.name)
      return str(field_obj)

   def _get_next_param_name(self, field_name: str) -> str:
      """
      Generates a unique named parameter key for SQL binding.
      """
      self._param_counter += 1
      clean_field = "".join(c for c in field_name if c.isalnum() or c == "_")
      return f"p_{clean_field}_{self._param_counter}"

   def _compile_node(self, node: ConditionASTNode, params: Dict[str, Any]) -> str:
      """
      Recursively traverses the AST nodes and constructs SQL query fragments.
      """
      if isinstance(node, ConditionExprNode):
         # Extract backendname directly from node.field object
         db_column = self._get_backend_name(node.field)
         op = node.op.upper()
         val = node.value
         negate = node.negate

         # 1. Handle Wildcard / LIKE translations (* -> %, ? -> _)
         if op == "LIKE" and isinstance(val, str):
            val = val.replace("*", "%").replace("?", "_")

         # 2. Bind parameter
         param_name = self._get_next_param_name(db_column)
         params[param_name] = val

         # 3. Construct expression using the extracted backend column name
         expr_sql = f"{db_column} {op} :{param_name}"

         # 4. Apply negation
         if negate:
            expr_sql = f"NOT ({expr_sql})"

         return expr_sql

      elif isinstance(node, ConditionLogicalNode):
         if not node.children:
            return ""

         compiled_children = []
         for child in node.children:
            child_sql = self._compile_node(child, params)
            if child_sql:
               compiled_children.append(child_sql)

         if not compiled_children:
            return ""

         if len(compiled_children) == 1:
            return compiled_children[0]

         # Join multiple children with logical operator (AND / OR)
         join_str = f" {node.logical_op.upper()} "
         joined_sql = join_str.join(compiled_children)

         return f"({joined_sql})"

      return ""

   def compile(self, ast: Optional[Any] = None) -> Tuple[str, Dict[str, Any]]:
      """
      Compiles the AST into an SQL string and a dictionary of named parameters.
      Accepts either a ConditionalAST wrapper or a raw ConditionASTNode.
      """
      target = ast if ast is not None else self.ast
      params: Dict[str, Any] = {}
      self._param_counter = 0
   
      if not target:
         return "", {}
   
      # Handle both ConditionalAST wrapper and direct ConditionASTNode (e.g. ConditionLogicalNode)
      root_node = getattr(target, "root", target)
   
      if not isinstance(root_node, ConditionASTNode):
         return "", {}
   
      sql_where = self._compile_node(root_node, params)
   
      # Strip redundant outermost parenthesis wrapper
      if sql_where.startswith("(") and sql_where.endswith(")"):
         depth = 0
         is_outer = True
         for idx, char in enumerate(sql_where[:-1]):
            if char == "(":
               depth += 1
            elif char == ")":
               depth -= 1
            if depth == 0 and idx > 0:
               is_outer = False
               break
         if is_outer:
            sql_where = sql_where[1:-1]
   
      return sql_where, params

def compile_sql(ast: ConditionalAST) -> Tuple[str, Dict[str, Any]]:
   """
   Helper function to directly compile a ConditionalAST to SQL and params.
   """
   compiler = ConditionSQL(ast)
   return compiler.compile()
