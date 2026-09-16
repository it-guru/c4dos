import os
import mmap
import sys
import signal
from pathlib import Path
import importlib
import time
from flask import Flask, jsonify, request, current_app, Blueprint, abort, g
import threading
from kernel import *
import resource

import http.client
import socket
import urllib.request
import urllib.error
import json
import dbpool


class C4Flask(Flask):

   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)

      self.UniqueID_rec={ 
         "counter": 0,
         "UniqueIdPool": [], 
         "timer": time.time()
      }
      self.UniqueID_lck=threading.Lock()
      self.teardown_appcontext(self._cleanup_db_transactions)

   def _cleanup_db_transactions(self, exception=None):
      dbpool.closeAllOpenTransactionsInCurrentThread(exception)
      
   def load_plugins(self):
      if self.plugdir:
         for base_dir in self.C4AppPath:
            plug_dir = base_dir / self.plugdir
            if not plug_dir.exists():
                continue
            sys.path.insert(0, str(plug_dir))
            for file_path in plug_dir.glob('*.py'):
                self.logger.info(f"[C4Flask] check load {file_path}")
                if file_path.name.startswith('_'):
                    continue
                module_name = file_path.stem 
                
                try:
                    plugin_module = importlib.import_module(module_name)
                    
                    if hasattr(plugin_module, 'setup'):
                        plugin_module.setup(self)
                        self.logger.info(f"[Plugin] loaded: {module_name}")
                    else:
                        self.logger.error(f"[Plugin] Warnung: {module_name}.py no setup()!")
                        
                except Exception as e:
                    print(f"[Plugin] failed to load {module_name}: {e}")
      else:
         print("no plugdir!")


   def closeAllFileDescriptors(self):
      soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
      for fd in range(3, soft_limit):
        # print(f"close [{fd}]")
         try:
             os.close(fd)
         except OSError:
             pass
      if hasattr(dbpool._thread_local, "conns"):
        dbpool._thread_local.conns = {}

   def resetAllSignalHandler(self):
      for sig in range(1, signal.NSIG):
        try:
            signal.signal(sig, signal.SIG_DFL)
        except (OSError, ValueError, RuntimeError):
            pass


   def post_fork_child_cleanup(self):
      self.resetAllSignalHandler()
      self.closeAllFileDescriptors()
      



   def isParentRunning(self):
      getpid=os.getppid()
      print(f"[isParentRunning] ppid={self.ppid}  os.getppid={getpid}")
      return os.getppid() == self.ppid

   def createUniqueId(self):
      self.logger.info(f"[createUniqueId] start")
      proxy_handler=urllib.request.ProxyHandler({})
      HttpAgent=urllib.request.build_opener(proxy_handler)

      target=f"http://127.0.0.1:8081"
      result=None

      max_retries = 15 
      retry_delay = 2 
 
      for attempt in range(1, max_retries + 1): 
         try:
            url=f"{target}/app/rpcCreateUniqueId"
            req=urllib.request.Request(url,method="GET")
            print(f"GET {url}")
            with HttpAgent.open(req,timeout=3) as response:
                status_code=response.status
                if status_code != 200:
                   self.logger.info(f"[createUniqueId] fail retry")
                   time.sleep(retry_delay)
                   continue
                result=response.read().decode('utf-8')
                break

         except (urllib.error.URLError,
                 http.client.HTTPException,
                 socket.error,
                 ConnectionResetError) as e:
            result = '{"status": "network_error","exitcode": 500}'

         except Exception as e:
            result = '{"status": "unexpected_error","exitcode": 500}'

      r=json.loads(result)
      if r["exitcode"]==0 :
         return(r["UniqueID"])
      else:
         return(None)
      

   def myLocalFunc(self):
       print("Hello myLocalFunc");
