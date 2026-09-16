from kernel.field   import *
from kernel.dataobj import *


class LimaSystem(DataObjSQLDB):
   _configSection          = "LIMA"
   _primaryBackendTable    = "system"

   name             = FieldText(
      backendname          = "system.name",
      label                = "name"
   )
   sysid            = FieldText(
      backendname          = "system.sys_id",
      label                = "sys_id"
   )
   conumber         = FieldText(
      backendname          = "system.conumber",
      label                = "cost element"
   )
   id               = FieldId(
      backendname          = "system.id",
   )
   urlofcurrentrec  = FieldRecordURL()
   recno                   = FieldRecNo(
      label                = "Record Number"
   )
   mdate            = FieldMDate()

   def validate(self,oldrec: dict, newrec: dict, orgRec: dict):
      print("in validate of LimaSystem")
      return(True)







