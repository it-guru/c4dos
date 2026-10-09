import re
from kernel.field.base import Field
from dateUtils import expTimeExpr

class FieldDate(Field):
   def __init__(self, **param):
      super().__init__(**param)

   def prepConditionString(self,condStr: str) -> str :
      # remove spaces on normaly seperation positions
      datemap={
         "deformat1": [r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})",r"\1_\2"],
         "enformat1": [r"(\d{1,2}.\d{1,2}.\d{2,4})\s+(\d{2}:\d{2}:\d{2})",r"\1_\2"],
      }
      for pattern,repl in datemap.values():
          condStr=re.sub(pattern,repl,condStr)
      return(condStr)

   def prepConditionBlock(self,condStr: str) -> str:
      mappedCondStr=expTimeExpr(condStr)
      if (mappedCondStr):
         condStr=mappedCondStr
      return(condStr)

      #return(self._normalizeDatestring(condStr))

   def decodeBackendStr(self,backendstr):
      formatedBackendString=expTimeExpr(backendstr)
      if (formatedBackendString):
         backendstr=formatedBackendString
      return(backendstr)



