from config import *
from event  import event
from kernel import *
from logger import logger
from pathlib import Path


class Event(event):
   def run(self):
      dataobjname="w5darwin.sys_user_group"
      o=getModuleObject(dataobjname)
      if (o is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance "+dataobjname
         })

      o.setFilter({"name":"a*"})
      o.limit(3,5)
      o.setCurrentView("(ALL)")
      if (o.query()):
         while True:
           row=o.get_next()
           if row is None: break
           pprint(row)

      return({"status": "success","exitcode": 0})

     





