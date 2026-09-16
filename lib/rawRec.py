import json
from pprint import pprint

class rawRec(dict):
  def __init__(self,initraw,field,view:list):
     super().__init__()
     self._raw={}
     self._rec={}
     self._Field=field
     self._keys=view

     if (initraw):
        self._raw=initraw

  def _generate(self, key):
     if key in self._Field:
        obj=self._Field[key]
        vjointo=getattr(obj,"vjointo",None)
        if (vjointo):  # if there is a vjointo attr, resolv it by _vjoin
           self._raw[key]=obj._vjoin(self)
        if key in self._rec:
           return(self._rec[key])
        recAttrDecodedVal=None
 
        if key in self._raw:
           if callable(getattr(obj,"decodeRaw",None)):
              recAttrDecodedVal=obj.decodeRaw(obj,self,self._raw[key])
           else:
              recAttrDecodedVal=self._raw[key]
        else:
           if callable(getattr(obj,"decodeRaw",None)):
              recAttrDecodedVal=obj.decodeRaw(obj,self,None)
           else:
              recAttrDecodedVal=None
        if (not recAttrDecodedVal is None):  # only not None Values are cached
           self._rec[key]=recAttrDecodedVal
        return(recAttrDecodedVal)
     return(None) 

  def __getitem__(self, key):
      return self._generate(key)

  def __contains__(self, key):
      return key in self._keys

  def __iter__(self):
      return iter(self._keys)

  def __len__(self):
      return len(self._keys)

  def get(self, key, default=None):
      if key in self:
          return self[key]
      return default

  def keys(self):
      return list(self._keys)

  def values(self):
      return [self[k] for k in self._keys]

  def items(self):
      return [(k, self[k]) for k in self._keys]

  def getIdField(self):
     for fldObj in self._Field.values():
         if (fldObj["type"] == "FieldId"):
            return(fldObj)
     return(None)

  def getIdFieldName(self):
     fldObj=self.getIdField()
     return(fldObj.name if (fldObj) else None)


      
