from .base import DataObj
from sqlalchemy import text,table,select,event,insert,update,column
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from rawRec import rawRec
from kernel.condition import *
from logger import *
import re

import dbpool
from datetime import datetime, timezone

from pprint import pformat, pprint

#@event.listens_for(Engine, "before_cursor_execute")
#def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
#    print("--- REAL EXECUTED SQL ---")
#    print(statement)
#    print("WITH PARAMS:", parameters)
#    print("-------------------------")


class DataObjSQLDB(DataObj):
    def __init__(self):
        super().__init__()
        self._is_connected         = False
        self._currentResultSet    = None

    def _connect(self):
       if (not self._is_connected):
          self.db=dbpool.get_connection(self._configSection) 
          self._is_connected = True
       return(self._is_connected)


    def get_from_sql(self) -> str:
       return(self._primaryBackendTable)

    def query(self):
       if (self._connect()):
          logger.debug("SQLDB: condition: "+pformat(self._CurrentFilterExpr))
          logger.debug("SQLDB: dialect: '"+self.db.dialect.name+"'")
          wherestr=""
          qparam=""
          if (self._CurrentAST):
             ASTprocessor=ConditionSQL()
             wherestr,qparam=ASTprocessor.compile(self._CurrentAST.getAST())
          logger.debug("SQLDB: AST wherestr: '"+pformat(wherestr)+"'")
         
          selLst=[]
          CurrentDepend=set()
          for fldname in self._Field:
             if (self._Field[fldname].selectfix):
                CurrentDepend.add(fldname)
          for fldname in self._CurrentView:
             if (fldname in self._Field):
                backendname=self._Field[fldname].getBackendName("select")
                if (not backendname is None):
                   aliasname=fldname
                   selLst.append(backendname+' AS "'+aliasname+'"')
                if (self._Field[fldname].depend):
                   for dfldname in self._Field[fldname].depend:
                      if (dfldname in self._Field):
                         CurrentDepend.add(dfldname)   
                      else:
                         raise(ValueError(
                            f"invalid .depend '{dfldname}' "\
                             "in field '{fldname}'")
                         )
          for dfldname in CurrentDepend:
             if (not dfldname in self._CurrentView):
                backendname=self._Field[dfldname].getBackendName("select")
                if (not backendname is None):
                   aliasname=dfldname
                   selLst.append(backendname+' AS "'+aliasname+'"')
         
          selectstr=', '.join(selLst) if (selLst) else "*"


          ####################################################################
          orderstr=None
          if (not self._CurrentOrder):
             self._CurrentOrder=self._CurrentView
          if (self._CurrentOrder):
             if (not ([self._CurrentOrder] == ["(NONE)"])):
                currentOrder=set()
                for fldname in self._CurrentOrder:
                   if (fldname in self._Field):
                      backendname=self._Field[fldname].getBackendName("order")
                      if (backendname):
                         currentOrder.add(backendname)
                if (currentOrder):
                   orderstr=",".join(currentOrder)
          ####################################################################
           
          
         

          ####################################################################
          limitAsLimit=None
          limitAsWhere=None
          if (self._limitResult>0 and not self._limitSoft):
             limitAsLimit=""+str(self._limitStart)+","+str(self._limitResult)
             limitAsWhere="(ROWNUM>="+str(self._limitStart)+\
                          " AND ROWNUM<="+str(self._limitResult)+")"

          if (self.db.dialect.name == "oracle"):
             if (not wherestr):
                wherestr=limitAsWhere
             else:
                wherestr=limitAsWhere+" AND "+wherestr
          ####################################################################

         
          sqlparts = [
              f"select {selectstr}",
              f"from {self.get_from_sql()}",
              f"where {wherestr}" if wherestr else None,
              f"order by {orderstr}" if orderstr else None,
              f"limit {limitAsLimit}" if self.db.dialect.name == "mysql" \
                                         and not limitAsLimit is None else None
          ]
         
          self._lastSQL=text(" ".join(filter(None,sqlparts)))

          logger.debug("SQLDB: cmd: '"+" ".join(filter(None,sqlparts))+"'")
          logger.debug("SQLDB: param: "+pformat(qparam,width=99999))
          result={}
          result["data"]=[]

           
         
          if (self.do_sql(self._lastSQL,qparam)):
             return(True)
          else:
             print("DB Error:(%s) %s" % (self._lastSQL,self.lastError()))



    def do_sql(self,cmd,param):
       if (self._connect()):
          try:
             query=cmd
             #pprint(cmd)
             self._currentResultSet = self.db.execute(query,param)
             self._lastError=None
             self._RECNO=0
             return(True)
          except DBAPIError as e:
             self._lastError=e.orig
             if hasattr(self._lastError,'args') and len(self._lastError.args)>1:
                self._lastError=self._lastError.args[1]
          except SQLAlchemyError as e:
             self._lastError=str(e)

       else:
          self._lastError="Backend not connected"

       return(False)




    def get_next_sql(self):
       if (not self._currentResultSet is None):
          row = self._currentResultSet.fetchone()
          if (not row is None):
             self._RECNO+=1
             if hasattr(row, "_mapping"):
                return dict(row._mapping)
             return(dict(row))
          else:
             return(None)
       else:
          print("ERROR: call get_next_sql without self._currentResultSet")
       return(None)



    def get_next(self):
       row=self.get_next_sql()
       if (row is not None):
          mrow={}
          for k,v in row.items():
             if isinstance(v, datetime):
                if v is None:
                   mapped_row[k]=v
                elif v.tzinfo is None:
                   mrow[k]=v.replace(tzinfo=timezone.utc).strftime(
                             "%Y-%m-%d %H:%M:%S")
                else:
                   mrow[k]=v.astimezone(timezone.utc).strftime(
                             "%Y-%m-%d %H:%M:%S")
             elif isinstance(v, bytes):
                mrow[k]="[bytes]"
             else:
                mrow[k]=v
          # add some internal _ Entries
          mrow["_RECNO"]=self._RECNO+self._limitStart

          # pack it in a rawRec
          dbRow=rawRec(mrow,self._Field,self._CurrentView)
          dbRow._parent=self
          return(dbRow)

       return(None)


    def insertRecord(self,  newRec: dict) -> str:
       if (self._connect()):
          insertID=None
          idobj=self.getIdField()
          if (idobj):
             if (not idobj.name in newRec \
                 or newRec[idobj.name] is None):
                if (idobj.autoGen):
                   id=self.createUniqueId()
                   if (not id):
                      raise(ValueError(f"unable to autoGen unique id "
                                       f"on insertRecord"))
                   newRec[idobj.name]=id
                   insertID=id
             else:
                insertID=newRec[idobj.name]
         
          #print("SQLDB: newRec: ", end='')
          #pprint(newRec)
          rawRec={}
         
          for fname in self._Field:
             if (not fname in newRec): 
                continue
             fieldValue=newRec[fname]
             alias=getattr(self._Field[fname],"alias",None)
             if (alias):
                if (not alias in self._Field):
                   raise(ValueError(f"unable to resolv alias in field"))
                else:
                   fname=alias
             backendname=self._Field[fname].getBackendName("insert")
             if (not backendname):
                continue
             rawname=re.sub(r"^.*\.", "", backendname)
             rawRec[rawname]=fieldValue
         
         
          #print("SQLDB: rawRec: ", end='')
          #pprint(rawRec)
          cols = [column(k) for k in rawRec.keys()]
          backendTable=table(self._primaryBackendTable,*cols)
          stmt=insert(backendTable).values(**rawRec)
          debstmt=re.sub(r"\s+", " ",str(stmt))
          debstmt+=" param="+pformat(rawRec,width=80*4,compact=True)
          #logger.debug("SQLDB: rawRec %s" % \
          #             pformat(rawRec,width=80*4,compact=True))
          logger.debug("SQLDB: insert stmt=%s" % debstmt)

          try:
            result=self.db.execute(stmt)
            if (result.rowcount>0):
               return(insertID)
            return(None)
         
          except Exception as e:
              raise RuntimeError(
                  f" 'insertRecord failed: {e}"
              ) from e

       return None

    def updateRecord(self,newRec: dict,filterExpr)->int: #return n affected rows
       if (self._connect()):
          rawRec={}
          normalzedFilter=self._normalizeFilterExpression(filterExpr)
          updateConditionAST=ConditionalAST(normalzedFilter,self._Field)
          ASTprocessor=ConditionSQL()
          wherestr,qparam=ASTprocessor.compile(updateConditionAST.getAST())

          for fname in self._Field:
             if (not fname in newRec): 
                continue
             fieldValue=newRec[fname]
             alias=getattr(self._Field[fname],"alias",None)
             if (alias):
                if (not alias in self._Field):
                   raise(ValueError(f"unable to resolv alias in field"))
                else:
                   fname=alias
             backendname=self._Field[fname].getBackendName("update")
             if (not backendname):
                continue
             rawname=re.sub(r"^.*\.", "", backendname)
             rawRec[rawname]=fieldValue
         
          cols = [column(k) for k in rawRec.keys()]
          backendTable=table(self._primaryBackendTable,*cols)

          stmt=update(backendTable).values(**rawRec)
          if wherestr:
             stmt=stmt.where(text(wherestr))
         
          debstmt=re.sub(r"\s+", " ",str(stmt))
          debstmt+=" rawRec="+pformat(rawRec,width=80*4,compact=True)
          debstmt+=" qparam="+pformat(qparam,width=80*4,compact=True)
          #logger.debug("SQLDB: rawRec %s" % \
          #             pformat(rawRec,width=80*4,compact=True))
          logger.debug("SQLDB: update stmt=%s" % debstmt)

          try:
            exec_params = {**rawRec, **qparam}
            result=self.db.execute(stmt,exec_params)
            if (result.rowcount>0):
               return(result.rowcount)
            return(0)
         
          except Exception as e:
              raise RuntimeError(
                  f" 'updateRecord failed: {e}"
              ) from e

       return(0)


    def deleteRecord(self, record_id: int) -> bool:
        if record_id not in self.records:
            print(f"Fehler: Datensatz {record_id} existiert nicht.")
            return False

        del self.records[record_id]
        print(f"Datensatz {record_id} erfolgreich geloescht.")
        return True

