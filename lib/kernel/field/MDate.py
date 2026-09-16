from kernel.field.Date import FieldDate

class FieldMDate(FieldDate):
   def __init__(self, **param):
      if ("backendname" not in param.keys()): param["backendname"]="modifydate"
      if ("name" not in param): param["name"]="mdate"
      if ("group" not in param): param["group"]="source"
      super().__init__(**param)


