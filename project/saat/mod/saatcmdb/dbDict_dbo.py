from kernel.field   import *
from kernel.dataobj import *


class SaatcmdbDbDict_dbo(DataObjSQLDB):
   _configSection          = "SAATCMDB"
   _primaryBackendTable    = "INFORMATION_SCHEMA.TABLES"

   name             = FieldText(
      backendname          = _primaryBackendTable+".TABLE_NAME",
      label                = "name"
   )
   type             = FieldText(
      backendname          = _primaryBackendTable+".TABLE_TYPE",
      label                = "type"
   )

   def validate(self,oldrec: dict, newrec: dict, orgRec: dict):
      #print("in validate of saatcmdb")
      return(True)









