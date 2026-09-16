from .base import DataObj
from rawRec import rawRec
from kernel.condition import *
from logger import *

from datetime import datetime, timezone

from pprint import pformat, pprint

class _ReverseStaticOrder:
    def __init__(self, obj):
        self.obj = obj
        
    def __lt__(self, other):
        return self.obj > other.obj

def parse_typed_value(val: str):
    if not isinstance(val, str):
        return val
    
    # 1. Versuche Integer / Float
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
        
    # 2. Versuche Datum (optional, Format anpassen falls nötig)
    # try:
    #     return datetime.fromisoformat(val)
    # except ValueError:
    #     pass

    return val





class DataObjStatic(DataObj):
    def __init__(self):
       super().__init__()
       self._rawData=[] 

    def rawDataCollect(self):
       return([])

    def compileAST(self):
       logger.debug("Static: condition: "+pformat(self._CurrentFilterExpr))
       ASTprocessor=ConditionStatic(case_sensitive=False)
       self._compiledWhere=ASTprocessor.compile(self._CurrentAST.getAST())
       logger.debug("Static: AST wherestr: '"+pformat(self._compiledWhere)+"'")
       return(True)


    def query(self):
       self.compileAST()

       self._rawData=self.rawDataCollect()  # entspricht dem SQL Kommando
       #logger.debug("Static: _rawData: "+pformat(self._rawData,width=99999))
       self._rawList=[]

       for rawDataRec in self._rawData:
          stRow=rawRec(rawDataRec,self._Field,self._CurrentView)
          stRow._parent=self
          if (self._compiledWhere):
             if (self._compiledWhere(stRow)):
                self._rawList.append(stRow)
          else:
             self._rawList.append(stRow)

       ####################################################################
       if (not self._CurrentOrder):
          logger.debug("Static: no CurrentOrder - using view")
          self._CurrentOrder=self._CurrentView
       if (self._CurrentOrder):
          if (not ["(NONE)"] == self._CurrentOrder):
             logger.debug("Static: COrder: \n"+pformat(self._CurrentOrder))
             sort_key=self.make_sort_key_for_rawData(self._CurrentOrder)
             self._rawList=sorted(self._rawList,key=sort_key)
       ####################################################################

       self._RECNO=0
       for stRec in self._rawList:
          stRec._raw["_RECNO"]=self._RECNO
          self._RECNO+=1


       temp_rawList=[]
       for stRec in self._rawList:
          if (stRec._raw["_RECNO"]<self._limitStart):
             continue
          temp_rawList.append(stRec)
       self._rawList=temp_rawList

       return(True) 



    def get_next(self):
       if (not self._rawList):
          return(None)
       curRec=self._rawList.pop(0)
       if (self._limitResult>0):
          if (curRec._raw["_RECNO"]+1>self._limitResult+self._limitStart):
             self._rawList=[]
             return(None)

       return(curRec)



    def insertRecord(self, record_id: int, data: dict) -> bool:
        return False



    def updateRecord(self, record_id: int, new_data: dict) -> bool:
        return False



    def deleteRecord(self, record_id: int) -> bool:
        return False


    def make_sort_key_for_rawData(self,current_order: list):
       parsed_order = []
       
       for field in current_order:
           if field.startswith("-"):
               parsed_order.append((field[1:], True))
           elif field.startswith("+"):
               parsed_order.append((field[1:], False))
           else:
               parsed_order.append((field, False))
      
       def key_func(rec: dict):
           key_tuple = []
           for field, is_reverse in parsed_order:
               val = rec.get(field, "")
               typed_val = parse_typed_value(val)
               
               if is_reverse:
                   # Absteigende Behandlung je nach Typ:
                   if isinstance(typed_val, (int, float)):
                       key_tuple.append(-typed_val)
                   else:
                       key_tuple.append(ReverseOrder(typed_val))
               else:
                   key_tuple.append(typed_val)
                   
           return tuple(key_tuple)
      
       return key_func

