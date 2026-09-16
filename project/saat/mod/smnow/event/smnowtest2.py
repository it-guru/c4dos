from config import *
from event  import event
from kernel import *
from logger import logger
from pathlib import Path

from nls import NLSManager
_ = NLSManager(__file__)


class Event(event):
   def run(self):
      dataobjname="smnow.cmdb_ci_server"
      o=getModuleObject(dataobjname)
      if (o is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance "+dataobjname
         })

      o.setFilter({"name":"ede1*","mdate":">2026-09-04 12:00:00"})
#      o.setCurrentView("name,sysid,sysclass,mdate")
#      if (o.query()):
#         while True:
#           row=o.get_next()
#           if row is None: break
#           pprint(row)
      print("Test NLS %s" % _("givenname"))

      return({"status": "success","exitcode": 0})

     





