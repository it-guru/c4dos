from kernel.field   import *
from kernel.dataobj import *

def _urlofcurrentrec_decodeRaw(self,backendRec,rawVal):
   idFldName=backendRec._parent.getIdFieldName()
   return(f"virtual val idfield={idFldName} surname={backendRec['surname']}")

class BaseContact(DataObjSQLDB):
   _configSection          = "BASE"
   _primaryBackendTable    = "contact"

   fullname         = FieldText(
      backendname          = "contact.fullname",
      label                = "fullqualified name"
   )
   cistatusid       = FieldText(
      backendname          = "contact.cistatus",
      label                = "CI-StatusID"
   )
   surname          = FieldText(  
      backendname          = "contact.surname",
      label                = "surname"
   )
   givenname        = FieldText(  
      backendname          = "contact.givenname",
      label                = "givenname"
   )
   virtual          = FieldText(  
      label                = "virtual full",
      depend               = ["surname"],
      decodeRaw            = _urlofcurrentrec_decodeRaw
   )
   groups           = FieldSubList(  
      label                = "Groups",
      vjointo              = "base.grp",
      vjoinon              = ["userid","grpid"],
      vjoindisp            = ["fullname","mdate","grpid"],
   )
   userid           = FieldId(
      backendname          = "contact.userid",
   )
   urlofcurrentrec  = FieldRecordURL()
   mdate            = FieldMDate()






