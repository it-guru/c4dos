from config import *
from event  import event
from kernel import *
from logger import logger
from pathlib import Path


class Event(event):
   def run(self):
      dataobjname="saatcmdb.dbDict_dbo"
      o=getModuleObject(dataobjname)
      if (o is None):
         return({"status": "failed",
           "exitcode": -1,
           "exitmsg": "failed to instance "+dataobjname
         })

      result=o.getDictIndexed(['name'],view=["name"])
      if ("customExportDeviceMView" in result["name"]):
         logger.info("customExportDeviceMView already exists "
                     "- using insert into")
         if (not o.doRawSQL("truncate table customExportDeviceMView")):
            logger.error(o.lastError())
         if (not o.doRawSQL("insert into [dbo].[customExportDeviceMView] "
                            "select * "
                            "from [dbo].[customExportDeviceView]")):
            logger.error(o.lastError())
 
      else:
         logger.info("customExportDeviceMView not exists "
                     "- using select into")
         if (not o.doRawSQL("select * into [dbo].[customExportDeviceMView] "
                            "from [dbo].[customExportDeviceView]")):
            logger.error(o.lastError())

      return({"status": "success","exitcode": 0,"result": result})

     





