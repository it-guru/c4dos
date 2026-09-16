from config import *
from event  import event
from kernel import *
from logger import logger
from pathlib import Path

from nls import NLSManager
_ = NLSManager(__file__)


class Event(event):
   def run(self):
      sys=getModuleObject("smnow::smnowsys")
      if (sys is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance smnow::smnowsys"
         })



      dataobjname="smnow.cmdb_ci_server"
      o=getModuleObject(dataobjname)
      if (o is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance "+dataobjname
         })

      #o.setFilter({"mdate": ">2026-06-01 18:15:03"})
      o.setCurrentView("(ALL)")
      o.setCurrentOrder(["mdate"])
      #o.limit(2)
      if (o.query()):
         while True:
           row=o.get_next()
           if row is None: break
           logger.info("-----------------------------------")
           logger.info("REC: %06d sys_id='%s' mdate='%s' name='%s'" % (int(row["recno"]),row["sysid"],row["mdate"],row["name"]))
           sys.setFilter({"sysid": [row["sysid"]]})
           r=sys.getDictList("(ALL)")
           if (len(r)==0):   # not found local - processing insert
              print("SMNOW recno=%03d id %s not found" % (row["recno"],row["sysid"]))
              newrec={
                 "name": row["name"],
                 "sysid": row["sysid"],
                 "conumber": row["conumber"],
                 "mdate": row["mdate"]
              }
              try:
                 insertId=sys.validatedInsertRecord(newrec)
                 logger.info(f"validatedInsertRecord={str(insertId)}")

              except Exception as e:
                 logger.error(f" 'circularEvent insert failed: {e}")
           else:            # found local - processing update
              for oldRec in r:
                 print("oldRec recno=%03d id %s try to update" \
                       % (oldRec["recno"],str(oldRec["id"])))
                 newrec={
                    "name": row["name"],
                    "sysid": row["sysid"],
                    "conumber": row["conumber"],
                    "mdate": row["mdate"]
                 }
                 try:
                    nAffected=sys.validatedUpdateRecord(oldRec,newrec,[[{"id":[oldRec["id"]]}]])
                    logger.info(f"validatedUpdateRecord={str(nAffected)}")
                
                 except Exception as e:
                    logger.error(f" 'circularEvent update failed: {e}")




      return({"status": "success","exitcode": 0})

     





