from .base import DataObj
from .Static import DataObjStatic
from rawRec import rawRec
from kernel.condition import *
from logger import *

from datetime import datetime, timezone

from pprint import pformat, pprint


#
# DataObjRest can be used for backends (normaly JSON Rest) which are
# direct support filtering and ordering (and optional pageing)
#
class DataObjRest(DataObjStatic):
   def __init__(self):
      super().__init__()
      self._rawData=[] 
      self._pageNumber=1      # Support for page-numberging without setFilter
      self._maxPages=None     #
      self._nextPage=None     #
      self._subDataCollectLoopCount=0

   def setFilter(self,filterExpr):
      super().setFilter(filterExpr)
      self._pageNumber=1
      self._maxPages=None
      self._nextPage=None
      self._subDataCollectLoopCount=0


   def rawDataCollect(self):
      return([])

   def mapBackendRec(self,rawDataRec):   # implement "as" selection from SQL
      for key in self._Field:            # on JSON REST Results
         obj=self._Field[key]
         backendname=self._Field[key].getBackendName("select")
         backendVal=None
         if (backendname):
            if (backendname in rawDataRec):
               backendVal=rawDataRec[backendname]
         if (callable(getattr(obj,"decodeBackendStr",None))):
            backendVal=obj.decodeBackendStr(backendVal)
         rawDataRec[key]=backendVal
           
   def _fillRawListBuffer(self):
      self._rawData=self.rawDataCollect() 

      self._rawList=[]
      for rawDataRec in self._rawData: 
         self.mapBackendRec(rawDataRec)      
         stRow=rawRec(rawDataRec,self._Field,self._CurrentView)
         stRow._parent=self
         self._rawList.append(stRow)
      for stRec in self._rawList:
         stRec._raw["_RECNO"]=(self._RECNO+1)
         self._RECNO+=1

   def compileAST(self):
      return(True)



   def query(self):
      self.compileAST()

      self._RECNO=0
      self._rawList=[]

      return(True) 



   def get_next(self):
      curRec=None
      if (self._rawList is None):
         return(None)
      while True:
         if (len(self._rawList)==0):
            self._fillRawListBuffer()
         if (not self._rawList):
            return(None)
         curRec=self._rawList.pop(0)
         if (self._limitStart>0):
            if (curRec._raw['_RECNO']<self._limitStart):
               continue
         break
      if (self._limitResult>0):
         resultRecNo=curRec._raw['_RECNO']-self._limitStart
         if (resultRecNo>self._limitResult):
            return(None) 
      return(curRec)



   def insertRecord(self, record_id: int, data: dict) -> bool:
       return False



   def updateRecord(self, record_id: int, new_data: dict) -> bool:
       return False



   def deleteRecord(self, record_id: int) -> bool:
       return False


