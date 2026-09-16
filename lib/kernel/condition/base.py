import re
from typing import Any, Dict, List, Optional, Union
from kernel.field import *
from logger import logger
from pprint import pprint


class ConditionASTNode:
   """
   Base class for all AST nodes in the condition parser.
   """
   pass


class ConditionExprNode(ConditionASTNode):
   """
   Represents a terminal expression node comparing a field against a value.
   """

   def __init__(self, fld_obj: Any, op: str, value: Any, negate: bool = False):
      self.field = fld_obj
      self.op = op.upper() if op else "="
      self.value = value
      self.negate = negate

   def __repr__(self) -> str:
      return f"ConditionExprNode(field='{self.field.name}', op='{self.op}', val={repr(self.value)}, negate={self.negate})"

   def to_dict(self):
      return({
         "type": "Condition",
         "field": self.field.name,
         "fldobj": self.field,
         "op": self.op,
         "value": self.value,
        # "is_literal": self.is_literal,
         "negate": self.negate
      })



class ConditionLogicalNode(ConditionASTNode):
   """
   Represents a logical grouping (AND / OR) of child AST nodes.
   """

   def __init__(self, logical_op: str, children: Optional[List[ConditionASTNode]] = None):
      self.logical_op = logical_op.upper()  # "AND" or "OR"
      self.children = children if children is not None else []

   def add_child(self, node: Optional[ConditionASTNode]):
      if node is not None:
         self.children.append(node)

   def __repr__(self) -> str:
      return f"ConditionLogicalNode({self.logical_op}, children={self.children})"

   def to_dict(self):
      return {
         "type": "Logical",
         "op": self.logical_op,
         "children": [child.to_dict() for child in self.children]
      }


def _tokenize_value_string(val_str: str, is_date_field: bool) -> List[str]:
   """
   Tokenizes an expression string into individual condition blocks.
   Handles quoted strings ('...' or "..."), whitespace separation,
   and unquoted YYYY-MM-DD HH:MM:SS timestamps for Date fields.
   """
   tokens = []
   length = len(val_str)
   i = 0

   # Regex pattern to match unquoted timestamp patterns like 2026-06-01 10:23:44
   date_patlst=[
    re.compile(r"^(!|>=|<=|>|<|=)?\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}"),
    re.compile(r"^(!|>=|<=|>|<|=)?\d{1,2}.\d{1,2}.\d{2,4}\s+\d{2}:\d{2}:\d{2}")
   ]

   while i < length:
      # Skip leading whitespace
      while i < length and val_str[i].isspace():
         i += 1
      if i >= length:
         break

      # Check for unquoted date/time string if field is Date/MDate
      if is_date_field:
         is_date_field_handled=False
         for date_pattern in date_patlst:
            match = date_pattern.match(val_str[i:])
            if match:
               token_str = match.group(0)
               tokens.append(token_str)
               i += len(token_str)
               is_date_field_handled=True
               break
         if (is_date_field_handled): continue

      char = val_str[i]

      # Quoted block ('...' or "...")
      if char in ("'", '"'):
         quote_char = char
         start = i
         i += 1
         while i < length and val_str[i] != quote_char:
            if val_str[i] == "\\" and i + 1 < length:
               i += 2  # Skip escaped characters
            else:
               i += 1
         if i < length and val_str[i] == quote_char:
            i += 1  # Include closing quote
         tokens.append(val_str[start:i])

      # Unquoted block (read until whitespace)
      else:
         start = i
         while i < length and not val_str[i].isspace():
            i += 1
         tokens.append(val_str[start:i])

   return tokens


def _parse_single_block(block: str, fld_obj: Any) -> ConditionExprNode:
   """
   Parses a single condition block token (e.g. '!>=100', '*HANS*', "='Hello World'").
   Extracts NEGATION, OPERATOR, and EXPRESSION value.
   """
   raw_block = block.strip()
   is_quoted_single = raw_block.startswith("'") and raw_block.endswith("'") and len(raw_block) >= 2
   is_quoted_double = raw_block.startswith('"') and raw_block.endswith('"') and len(raw_block) >= 2

   # 1. Parse Negation
   negate = False
   if raw_block.startswith("!"):
      negate = True
      raw_block = raw_block[1:]

   # 2. Extract Operator
   op = None
   operators = [">=", "<=", ">", "<", "="]
   for candidate_op in operators:
      if raw_block.startswith(candidate_op):
         op = candidate_op
         raw_block = raw_block[len(candidate_op):]
         break

   # 3. Handle Quoted vs Unquoted Expression
   if is_quoted_single or is_quoted_double:
      # Strip quotes
      expr = raw_block[1:-1] if (raw_block.startswith("'") or raw_block.startswith('"')) else raw_block
   else:
      expr = raw_block

   # 4. Wildcard Detection (* or ?)
   has_wildcards = ("*" in expr or "?" in expr) and not (is_quoted_single)

   if has_wildcards:
      if op is not None:
         raise ValueError(f"Invalid condition construct: " \
                           "Operators like '{op}' are not " \
                           "allowed with wildcards in '{block}'")
      op = "LIKE"
   elif op is None:
      op = "="

   # 5. Apply prepConditionString if available on field object
   if (hasattr(fld_obj, "prepConditionBlock") and 
       callable(fld_obj.prepConditionBlock)):
      expr = fld_obj.prepConditionBlock(expr)

   return ConditionExprNode(fld_obj=fld_obj, op=op, value=expr, negate=negate)


def _parse_field_value_expression(fld_name: str, val: Union[str, List[Any]], fld_obj: Any) -> ConditionASTNode:
   """
   Parses a single field's condition value (List or String) into an AST structure.
   """
   # Check if field is Date or MDate type
   fld_class_name = fld_obj.__class__.__name__ if fld_obj else ""
   is_date_field = isinstance(fld_obj,FieldDate) # in fld_class_name

   # Case 1: Value is a List -> OR-connected '=' conditions
   if isinstance(val, list):
      or_node = ConditionLogicalNode("OR")
      for item in val:
         item_val = item
         if (hasattr(fld_obj, "prepConditionBlock") and \
             callable(fld_obj.prepConditionBlock)):
            item_val = fld_obj.prepConditionBlock(item_val)
         or_node.add_child(ConditionExprNode(fld_obj=fld_obj, 
                                             op="=", value=item_val, negate=False))
      return or_node if (len(or_node.children) > 1) else (or_node.children[0] \
                         if (or_node.children) else None)

   # Case 2: Value is a String
   elif isinstance(val, str):
      if (hasattr(fld_obj, "prepConditionString") and \
          callable(fld_obj.prepConditionString)):
         val = fld_obj.prepConditionString(val)
      # Split by " AND " first
      and_segments = val.split(" AND ")
      and_node = ConditionLogicalNode("AND")

      for segment in and_segments:
         # Tokenize segment into whitespace-separated blocks (OR-connected)
         tokens = _tokenize_value_string(segment, is_date_field)
         if not tokens:
            continue

         or_node = ConditionLogicalNode("OR")
         for token in tokens:
            expr_node = _parse_single_block(token, fld_obj)
            or_node.add_child(expr_node)

         if len(or_node.children) == 1:
            and_node.add_child(or_node.children[0])
         elif len(or_node.children) > 1:
            and_node.add_child(or_node)

      if len(and_node.children) == 1:
         return and_node.children[0]
      elif len(and_node.children) > 1:
         return and_node

   # Case 3: Fallback for scalar non-string values
   return ConditionExprNode(fld_obj=fld_obj, op="=", value=val, negate=False)


def build_ast(filterExpr: List[List[Dict[str, Any]]], parent_fields: Dict[str, Any]) -> Optional[ConditionASTNode]:
   """
   Builds a Condition AST from a nested filter expression structure.

   Structure:
   Level 1 (Outer List): AND-connected groups
   Level 2 (Inner List): OR-connected dict-conditions
   Dict-Conditions: Key-Value pairs matching fields in parent_fields
   """
   if not filterExpr:
      return None

   level1_and_node = ConditionLogicalNode("AND")

   for level2_list in filterExpr:
      if not level2_list:
         continue

      level2_or_node = ConditionLogicalNode("OR")

      for dict_cond in level2_list:
         if not dict_cond:
            continue

         # Each dict condition groups its field constraints with AND
         dict_and_node = ConditionLogicalNode("AND")

         for fld_key, fld_val in dict_cond.items():
            if fld_key not in parent_fields:
               logger.debug("WARN: skip expression key %s" % fld_key)
               continue

            fld_obj = parent_fields[fld_key]
            field_ast = _parse_field_value_expression(fld_key, fld_val, fld_obj)

            if field_ast:
               dict_and_node.add_child(field_ast)

         if len(dict_and_node.children) == 1:
            level2_or_node.add_child(dict_and_node.children[0])
         elif len(dict_and_node.children) > 1:
            level2_or_node.add_child(dict_and_node)

      if len(level2_or_node.children) == 1:
         level1_and_node.add_child(level2_or_node.children[0])
      elif len(level2_or_node.children) > 1:
         level1_and_node.add_child(level2_or_node)

   if len(level1_and_node.children) == 1:
      return level1_and_node.children[0]
   elif len(level1_and_node.children) > 1:
      return level1_and_node

   return None


class ConditionalAST():
   def __init__(self,filterExpr,fieldmap):
      self._AST=build_ast(filterExpr,fieldmap)

   def getAST(self):
      return(self._AST)



__all__ = [k for k in locals() if k.startswith("Condition")]

