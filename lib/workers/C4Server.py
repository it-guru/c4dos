import json
import ctypes
import os
import sys
import time
import threading
from kernel import *
from logger import *
from setproctitle import setproctitle

from config import config

from kernel.condition import *
import kernel.condition.base

from pprint import pformat, pprint





from C4Flask import C4Flask, jsonify, request, current_app, abort, g

class C4FlaskServer(C4Flask):
   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.UniqueID_rec={
         "counter": 0,
         "UniqueIdPool": [],
         "timer": time.time()
      }
      self.UniqueID_lck=threading.Lock()



app = C4FlaskServer(__name__)
app.plugdir="event"

@app.before_request
def set_request_language():
   lang=request.args.get("lang") \
        or request.accept_languages.best_match(["de","en"])
   g.lang = lang


@app.route('/<AppConfig>/internalTimer')
def internalTimer(AppConfig):
   auth_key = request.headers.get('X-AUTHKEY')
   if not auth_key or auth_key != current_app.C4InternalKey:
      abort(403, description="Access denied. Invalid X-AUTHKEY token.")
   logger.debug(f"internalTimer: handled at PID({os.getpid()}")
   return jsonify({"status":"success","exitcode": 0})


@app.route('/<AppConfig>/getConfig')
def getConfig(AppConfig):
   auth_key = request.headers.get('X-AUTHKEY')
   if not auth_key or auth_key != current_app.C4InternalKey:
      abort(403, description="Access denied. Invalid X-AUTHKEY token.")
 
   return jsonify({
       "status":"success",
       "exitcode": 0,
       "result": config,
   })



@app.route('/<basePath>/<AppConfig>/<module>/event/<evname>' \
           '/<any(sync,async):mode>', 
           methods=['GET','POST'])
def runEvent(basePath,AppConfig,module,evname,mode):
   self=current_app._get_current_object()
   dataobjname=f"{module}.{evname}"
   auth_key = request.headers.get('X-AUTHKEY')
   if not auth_key or auth_key != current_app.C4InternalKey:
      abort(403, description="Access denied. Invalid X-AUTHKEY token.")

   o=getEventObject(module,evname)

   if (o):
      if (mode == "sync"):
         logger.info(f"[Ev:{module}.{evname}] "\
                      "sync run at PID({os.getpid()}")
         bk=o.run()
         return(jsonify(bk))
      else:
         try:
             pid = os.fork()
         except OSError as e:
             sys.exit(f"Fork failed: {e}")
        
         if pid > 0:
             logger.info(f"{mode} event '{module}.{evname} forked PID({pid})")
         else:
             self.post_fork_child_cleanup()
             setproctitle(f"c4dos: Event({module}.{evname}")
             logger.info(f"[Ev:{module}.{evname}] "\
                          "start at PID({os.getpid()}")
             try:
                 bk=o.run()
             except Exception as e:
                 print(f"[Child] Fehler: {e}")
             finally:
                 logger.info(f"[Ev:{module}.{evname}] "\
                              "finished pid({os.getpid()}")
                 os._exit(0)
   else:
      return jsonify({"status":"failed","exitcode": -1, 
                      "exitmsg": "fail to instance EventObjekt"})

   return jsonify({"status":"success","exitcode": 0})



@app.route('/<AppConfig>/<module>/<dataobj>/<method>', methods=['GET', 'POST'])
def do_dbcall(AppConfig,module,dataobj,method):
   dataobjname=f"{module}.{dataobj}"
   logger.info(f"call {method} to {dataobjname}")

   o=getModuleObject(module,dataobj)
   if (o is None):
      return jsonify({
                       "status":"failed",
                       "exitcode": -1, 
                       "exitmsg": "ERROR: dataobj {method}/{dataobjname} "\
                                  "failed to instance"
      })

   auth_key = request.headers.get('X-AUTHKEY')

   param=request.values.to_dict()

   CurrentView="(ALL)"

   if ("_CurrentView" in param):
      CurrentView=param["_CurrentView"]
      del param["_CurrentView"]
      

   search_criteria=[
      [
        param 
      ] 
   ]

   pprint(search_criteria)

   if (not auth_key or auth_key != current_app.C4InternalKey):
      o.secureSetFilter(search_criteria)
   else:
      o.setFilter(search_criteria)

   o.setCurrentView(CurrentView); 
   #o.setCurrentOrder("fullname,grpid,mdate"); 
   result=o.getDictList() 
                   
   return jsonify({"status":"success","exitcode": 0, "result" : result})



@app.route('/<basePath>/<AppConfig>/rpcCreateUniqueId')
def rpcCreateUniqueId(basePath,AppConfig):
   self=current_app._get_current_object()
   logger.info("/rpcCreateUniqueId call.")
   newID=None
   with self.UniqueID_lck:
     if len(self.UniqueID_rec["UniqueIdPool"])==0 :
        for i in range(999):
            self.UniqueID_rec["UniqueIdPool"].append(int("%d09%04d" % (time.time(),i)))
     newID=self.UniqueID_rec["UniqueIdPool"].pop(0)
   logger.info("/rpcCreateUniqueId returned "+str(newID))
   return jsonify({"status":"success","exitcode": 0, "UniqueID": newID})





