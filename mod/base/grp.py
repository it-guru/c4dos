from kernel.field   import *
from kernel.dataobj import *

class BaseGrp(DataObjSQLDB):
   def __init__(self):
      super().__init__()
      self._configSection       = "BASE"
      self._primaryBackendTable = "grp"

      self.addFields(
         FieldText(
            name      = "fullname",
            label     = "fullqualified name"
         ),
         FieldText(  
            name      = "surname",
            label     = "fullqualified name"
         ),
         FieldId(  
            name      = "grpid"
         ),
         FieldRecordURL(),
         FieldMDate()
      )






