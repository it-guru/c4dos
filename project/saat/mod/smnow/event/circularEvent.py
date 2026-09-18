from config import *
from event  import event
from kernel import *
from logger import logger
from pathlib import Path

import re

from nls import NLSManager
_ = NLSManager(__file__)


class Event(event):
   def run(self):
      lsys=getModuleObject("saatcmdb.customExportDevice")
      if (lsys is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance saatcmdb.customExportDevice"
         })

      sys=getModuleObject("saatcmdb.cmdb_ci_server")
      if (sys is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance saatcmdb.cmdb_ci_server"
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
      #o.limit(100)
      loopCount=0
      if (o.query()):
         while True:
           row=o.get_next()
           if row is None: break
           if (sys.acquireLock(row["sysid"])):
              try:
                 logger.info("-----------------------------------")
                 cleanname=re.sub(r"\..*$","",row["name"])
                 cleanname=re.sub(r"\[.+\]$","",cleanname)
                 logger.info("REC: %06d sys_id='%s' mdate='%s' name='%s' cleanname='%s'" % 
                             (int(row["recno"]),row["sysid"],row["mdate"],row["name"],cleanname))
 
                 newrec={
                    "cleanname":cleanname,
                    "w5baseid":"",
                    "realcomputername":"",
                    "computerid":""
                 }
                 if (not cleanname==""):
                    lsys.setFilter({"name": cleanname})
                    lres=lsys.getDictList("(ALL)")

                    if (len(lres)==1):
                       newrec["realcomputername"]=lres[0]["realcomputername"]
                       newrec["w5baseid"]=lres[0]["w5baseid"]
                       newrec["computerid"]=lres[0]["id"]

                       
                 sys.setFilter({"sysid": [row["sysid"]]})
                 r=sys.getDictList("(ALL)")
                 if (len(r)==0):   # not found local - processing insert
                    print("SMNOW recno=%03d id %s not found" % (row["recno"],row["sysid"]))
                    newrec["name"]=row["name"]
                    newrec["sysid"]=row["sysid"]
                    newrec["cost_center"]=row["cost_center"]
                    newrec["object_id"]=row["object_id"]
                    newrec["mdate"]=row["mdate"]
                    try:
                       insertId=sys.validatedInsertRecord(newrec)
                       logger.info(f"validatedInsertRecord={str(insertId)}")

                    except Exception as e:
                       logger.error(f" 'circularEvent insert failed: {e}")
                 else:            # found local - processing update
                    for oldRec in r:
                       newrec["name"]=row["name"]
                       newrec["cost_center"]=row["cost_center"]
                       newrec["object_id"]=row["object_id"]
                       newrec["mdate"]=row["mdate"]
                       try:
                          nAffected=sys.validatedUpdateRecord(
                             oldRec, newrec,[[{"id":[oldRec["id"]]}]]
                          )
                          logger.info(f"validatedUpdateRecord={str(nAffected)}")
                      
                       except Exception as e:
                          logger.error(f" 'circularEvent update failed: {e}")
              finally:
                 sys.releaseLock(row["sysid"])
           else:
              logger.warn(f" lock failed for sysid={row['sysid']}")

           if (loopCount % 10 == 0): sys.commit()
           loopCount+=1




      return({"status": "success","exitcode": 0})

     





