#from .Rest import DataObjRest
from rawRec import rawRec
from kernel.condition import *
from logger import *

from datetime import datetime, timezone

from pprint import pformat, pprint
from config import config

import http.client
import json
import urllib.error
import urllib.request
import base64
import time

import re
from pprint import pprint



class HttpAuthBasic():
   def __init__(self):
      self._tardis_token=None

   def _replaceURLPath(self,url,newpath):
      url=re.sub(r'//([^/]+)/.*$', fr'//\1{newpath}', url)
      return(url)

   def _deriveIrisUrl(self,dataurl: str):
      irisPath="/auth/realms/default/protocol/openid-connect/token"
      dataurl=re.sub(r'stargate([\.-])', r'iris\1', dataurl)
      dataurl=self._replaceURLPath(dataurl,irisPath)
      return(dataurl)

   def getAuthorization(self,configSection: str):
      dataobjuser=config[configSection]["DATAOBJUSER"]
      dataobjpass=config[configSection]["DATAOBJPASS"]
      print("DATAOBJUSER:%s" % dataobjuser)
      print("DATAOBJPASS:%s" % dataobjpass)

      credentials = f"{dataobjuser}:{dataobjpass}"
      b64_credentials=base64.b64encode(credentials.encode("utf-8"))\
                      .decode("utf-8")
      return(f"Basic {b64_credentials}")

#      no_proxy_handler = urllib.request.ProxyHandler({})
#      opener = urllib.request.build_opener(no_proxy_handler)
#      with opener.open(req, timeout=5) as response:
#         charset = response.headers.get_content_charset(failobj="utf-8")
#         result_text = response.read().decode(charset)
#         data = json.loads(result_text)
#         data["create_time"]=int(time.time())
#         data["Authorization"]=\
#            f'{data.get("token_type")} {data.get("access_token")}'
#         #pprint(data)
#         self._tardis_token=data
#         return(self._tardis_token.get("Authorization"))
#      return(None)
#
#   def getAuthorization(self,configSection: str):
#      return(self._getTardisToken(configSection))



