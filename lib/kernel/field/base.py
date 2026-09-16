from pprint import pprint

class Field(dict):
   def __init__(self, **param):
      self.name=param.get("name",None)
      self.backendname=None
      self.selectfix=False

      if "backendname" in param:   self.backendname=param["backendname"]
      if "selectfix"   in param:   self.selectfix=param["selectfix"]
      if "vjointo"     in param:   self.vjointo=param["vjointo"]
      if "vjoinon"     in param:   self.vjoinon=param["vjoinon"]
      if "vjoindisp"   in param:   self.vjoindisp=param["vjoindisp"]
      if "vjointodict" in param:   self.vjointodict=param["vjointodict"]

      if "group" not in param:       param["group"]="default"
      if not isinstance(param["group"],list): param["group"]=[param["group"]]

      self.decodeRaw=param.get("decodeRaw",None)
      self.depend=param.get("depend",None)
      self.group=param["group"]
      self._initParam=param
      self._parent=None
      if (self.name): 
         self["name"]=self.name
      self["type"]=type(self).__name__

   def __2nd__init__(self):  # second pass init after 1st addFields loop
      pass

   def _vjoin(self,dbRec): 
      if (not self.vjointo):
         return([])
      return([{"name":"t1"},{"name":"t2"},{"name":"xxx"}])

   def getBackendName(self,mode:str):
      if (mode == "select"):
         if (self.backendname):
            return(self.backendname)
         if (not self.decodeRaw and not self.vjointo): 
            if (self.name):
               return(self.name)
      if (mode == "order"):
         if (self.backendname):
            return(self.backendname)
      if (mode == "insert" or mode == "update"):
         if (self.backendname):
            return(self.backendname)
      return(None)

   def validate(self,oldRec: dict, newRec: dict, orgRec: dict):


      return(False)

   def prepConditionString(self,condStr: str) -> str :
      #print("prepConditionString %s : '%s'" % (self.name,condStr) )
      return(condStr)

   def prepConditionBlock(self,condStr: str) -> str :
      #print("prepConditionBlock %s : '%s'" % (self.name,condStr) )
      return(condStr)

