from kernel.field.URL import FieldURL

def _urlofcurrentrec_decodeRaw(self,dbRec,rawVal):
   idFldName=dbRec._parent.getIdFieldName()
   if (idFldName):
      return(f"http://ById/{dbRec[idFldName]}")
   return(None)

class FieldRecordURL(FieldURL):

   def __init__(
                self, 
                **param
               ):
      if (not "name" in param):
         param["name"]="urlofcurrentrec"
      if (not "decodeRaw" in param):
         param["decodeRaw"] = _urlofcurrentrec_decodeRaw

      super().__init__(**param)
      self.backendname=None




