from kernel.field   import *
from kernel.dataobj import *

from httpAuth.Tardis import HttpAuthTardis

import re
from pprint import pprint, pformat
from logger import logger


class SmnowCmdb_ci_server(DataObjServiceNow, HttpAuthTardis):
   _configSection          = "SMNOW"
   _primaryBackendTable    = "get/cmdb_ci_server"
 
   name                    = FieldText(
      backendname          = "name",
      label                = "name"
   )
   lifecycle               = FieldText(
      backendname          = "life_cycle_stage",
      label                = "life cycle state"
   )
   status                  = FieldText(
      backendname          = "life_cycle_stage_status",
      label                = "status"
   )
   opmode                  = FieldText(
      backendname          = "used_for",
      label                = "operation mode"
   )

   company                 = FieldText(
      backendname          = "company",
      label                = "company"
   )
   location                = FieldText(
      backendname          = "location",
      label                = "location"
   )
   costobject              = FieldText(
      backendname          = "cost_center",
      label                = "costobject"
   )
   correlationid           = FieldText(
      backendname          = "correlation_id",
      label                = "correlation_id"
   )
   srcsys                  = FieldText(
      backendname          = "discovery_source",
      label                = "Source-System"
   )
   srcid                   = FieldText(
      backendname          = "object_id",
      label                = "Source-Id"
   )
   sysclass                = FieldText(
      backendname          = "sys_class_name",
      label                = "SysClass"
   )
   sysid                   = FieldId(
      backendname          = "sys_id",
      label                = "SysId"
   )
   recno                   = FieldRecNo(
      label                = "Record Number"
   )
   mdate                   = FieldDate(
      backendname          = "sys_updated_on",
      label                = "SysUpdatedOn"
   )




