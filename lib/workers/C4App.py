import json
import ctypes
import os
import json
import threading
import time
import sys
from pathlib import Path
import importlib
from C4Flask import C4Flask, jsonify, request, current_app
#from multiprocessing import Process, Array, Event
from kernel import *


class C4FlaskApp(C4Flask):
   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)


app = C4FlaskApp(__name__)
app.plugdir="plugin"

@app.before_request
def set_request_language():
   lang=request.args.get("lang") \
        or request.accept_languages.best_match(["de","en"])
   g.lang = lang  
   g.remote_user=session.get("username",None)
   g.isWebUIRequest=True


@app.route('/<AppConfig>/internalTimer')

def internalTimer(AppConfig):
   auth_key = request.headers.get('X-AUTHKEY')

   if not auth_key or auth_key != current_app.C4InternalKey:
      abort(403, description="Access denied. Invalid X-AUTHKEY token.")

   return jsonify({"status":"success","exitcode": 0})



@app.route('/<AppConfig>/info')
def run_fork(AppConfig):
   self=current_app
   self.logger.info("/info call.")

   for rule in self.url_map.iter_rules():
      methoden = ",".join(rule.methods - {'HEAD', 'OPTIONS'})
      # rule.rule = Die URL (z.B. /internal/internalTimer)
      # rule.endpoint = Der Name (z.B. mein_blueprint.internal_timer_func)
      print(f"URL: {rule.rule:<30} | Methoden: {methoden:<15} | Endpoint: {rule.endpoint}")

   id=self.getUniqueId()

   print(f"getUniqueId={id}")

   return jsonify({"status":"success","exitcode": 0,"result": id})



#def Task1(self,TaskLabel):
#   print(f"[Task1-Worker] Prozess mit PID {os.getpid()} gestartet.")
#   #time.sleep(5)
#   threading.Event().wait(timeout=20)
#   print(f"[Task1-Worker] exit Prozess mit PID {os.getpid()}.")
#   with self.C4ShmLock:
#      W5Shm=getC4Shm(self.C4Shm,self.C4ShmSize)
#      W5Shm[TaskLabel]["thread_state"]="finished"
#      W5Shm[TaskLabel]["thread_end"]=time.time()
#      setC4Shm(self.C4Shm,self.C4ShmSize,W5Shm)
#
#
#@app.route('/<AppConfig>/runTask1')
#def runTask1(AppConfig):
#   return(current_app._get_current_object().invokeLabeledThread(Task1,"Task1"))



if __name__ == '__main__':
    app.run(port=8080)


