import re
from kernel.field.base import Field

class FieldDate(Field):
   def __init__(self, **param):
      super().__init__(**param)

   def _normalizeDatestring(self,dStr: str) -> str:
      rules = [
         (
            r"^(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s+(\d{2}):(\d{2}):(\d{2})$",
            (3, 2, 1, 4, 5, 6)
         ),
         (
            r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.\d{2,3}Z$",
            (1, 2, 3, 4, 5, 6)
         ),
      ]
      for pattern, idx in rules:
          match = re.match(pattern, dStr)
          if match:
              y, m, d, hh, mm, ss = [int(match.group(i)) for i in idx]
              if y < 100:
                  y += 2000
              return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}"
      return(dStr)



   def prepConditionBlock(self,condStr: str) -> str:
      return(self._normalizeDatestring(condStr))

   def decodeBackendStr(self,backendstr):
      backendstr=self._normalizeDatestring(backendstr) 
      return(backendstr)



