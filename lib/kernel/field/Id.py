from kernel.field.base import Field

class FieldId(Field):
   def __init__(self, **param):
      self.autoGen=True 
      param["selectfix"]=True
      super().__init__(**param)
      if "autoGen" in param: self.autoGen=param["autoGen"]


