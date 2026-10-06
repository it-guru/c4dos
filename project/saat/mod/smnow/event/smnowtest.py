from config import *
from event  import event
from kernel import *
from logger import logger
from pathlib import Path
from pprint import pprint, pformat


class Event(event):
   def run(self,param):
      dataobjname="smnow.cmdb_ci_server"
      if (not param):
         param={"name":"ede55m ede127 ede188"}
      
     
      o=getModuleObject(dataobjname)
      if (o is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance "+dataobjname
         })

      logger.info("o.setFilter="+pformat(param))
      o.setFilter(param)
      result=o.getDictList("(ALL)")

      return({"status": "success","exitcode": 0,"result": result})

     





