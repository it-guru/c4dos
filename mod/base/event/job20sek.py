from config import *
from event  import event
from kernel import *
from logger import logger
from pathlib import Path


class Event(event):
   def run(self):
      o=getModuleObject("base.contact")
      if (o is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance base.contact"
         })

      min_search_crit={
        "surname": "vo*",
        "givenname": "h*",
        "cistatusid": [3,4,5]
      }

      search_criteria=[[ min_search_crit]]
      o.setFilter(search_criteria)
      logger.debug(f"{Path(__file__).name}: start")

      logger.debug(f"Count1={str(o.countRecords())}")
      o.limit(3)
      logger.debug(f"Count2={str(o.countRecords())}")

      result=o.getDictList(
          "fullname,mdate,name,surname,givenname,"\
          "urlofcurrentrec,virtual,groups",
      )

      return({"status": "success","exitcode": 0,"result": result})

     





