from kernel.field   import *
from kernel.dataobj import *

from httpAuth.Basic import HttpAuthBasic

import re
from pprint import pprint, pformat
from logger import logger


class W5darwinSys_user_group(DataObjServiceNow, HttpAuthBasic):
   _configSection          = "W5DarwinSMNow"
   _primaryBackendTable    = "now/table/sys_user_group"
 
   name                    = FieldText(
      backendname          = "name",
      label                = "name"
   )
   sysid                   = FieldId(
      backendname          = "sys_id",
      label                = "sys_id"
   )
   mdate                   = FieldDate(
      backendname          = "sys_updated_on",
      label                = "SysUpdatedOn"
   )




