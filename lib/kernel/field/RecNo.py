from kernel.field.URL import FieldURL

def _urlofcurrentrec_decodeRaw(self,dbRec,rawVal):
   recno=int(dbRec._raw['_RECNO'])

   return(recno)

class FieldRecNo(FieldURL):

   def __init__(
                self, 
                **param
               ):
      if (not "name" in param):
         param["name"]="recno"
      if (not "decodeRaw" in param):
         param["decodeRaw"]=_urlofcurrentrec_decodeRaw

      param["sortable"]=False

      super().__init__(**param)
      self.backendname=None




