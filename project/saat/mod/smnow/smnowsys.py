from kernel.field   import *
from kernel.dataobj import *


class SmnowSmnowsys(DataObjSQLDB):
   _configSection          = "LIMA"
   _primaryBackendTable    = "smnow_system"

   name             = FieldText(
      backendname          = _primaryBackendTable+".name",
      label                = "name"
   )
   sysid            = FieldText(
      backendname          = _primaryBackendTable+".sys_id",
      label                = "sys_id"
   )
   conumber         = FieldText(
      backendname          = _primaryBackendTable+".conumber",
      label                = "cost element"
   )
   id               = FieldId(
      backendname          = _primaryBackendTable+".id",
   )
   recno                   = FieldRecNo(
      label                = "Record Number"
   )
   urlofcurrentrec  = FieldRecordURL()
   mdate            = FieldMDate()

   def validate(self,oldrec: dict, newrec: dict, orgRec: dict):
      #print("in validate of LimaSystem")
      return(True)







