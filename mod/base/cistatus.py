from kernel.field   import *
from kernel.dataobj import *


class BaseCistatus(DataObjStatic):
   name             = FieldText(
      label                = "CI-State"
   )
   info             = FieldText(
      label                = "CI-State Level explaination"
   )
   id               = FieldId(
      label                = "CI-StateID"
   )
   def rawDataCollect(self):
      return([
         { "id" : 0, "name" : "CI-Status(0)", "info" : "undefined"},
         { "id" : 2, "name" : "CI-Status(2)", "info" : "on order"},
         { "id" : 3, "name" : "CI-Status(3)", "info" : "available/in project"},
         { "id" : 4, "name" : "CI-Status(4)", "info" : "installed/active"},
         { "id" : 1, "name" : "CI-Status(1)", "info" : "reserved"},
         { "id" : 5, "name" : "CI-Status(5)", "info" : "inactive/stored"},
         { "id" : 7, "name" : "CI-Status(7)", "info" : "disposed of waste"},
         { "id" : 6, "name" : "CI-Status(6)", "info" : "deconstruction"},
         { "id" : 9, "name" : "CI-Status(9)", "info" : "wasted"},
      ]) 

