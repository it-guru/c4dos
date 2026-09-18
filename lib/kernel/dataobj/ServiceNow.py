from .base import DataObj
from .Rest import DataObjRest
from rawRec import rawRec
from kernel.condition.ServiceNow import ConditionServiceNow
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



class DataObjServiceNow(DataObjRest):
   def __init__(self):
      super().__init__()

   def compileAST(self):
      self._sysparm_query=None
      if (self._CurrentAST):
         ASTprocessor=ConditionServiceNow()
         self._sysparm_query=ASTprocessor.compile(self._CurrentAST.getAST())
      

      self._sysparm_orderstr=""
      if not self._CurrentOrder:
          self._CurrentOrder = self._CurrentView

      if self._CurrentOrder and self._CurrentOrder != ["(NONE)"]:
          order_fields = []

          for fldname in self._CurrentOrder:
              if fldname in self._Field:
                  backendname = self._Field[fldname].getBackendName("order")
                  if backendname:
                      if backendname not in order_fields:
                          order_fields.append(backendname)
          if order_fields:
              self._sysparm_orderstr="^"+"^"\
                 .join([f"ORDERBY{fld}" for fld in order_fields])


      return(True)

   def getApiEndpointURL(self):
      dataobjconnect=config[self._configSection]["DATAOBJCONNECT"]
      requestURL=f"{dataobjconnect}"
      if (not requestURL.endswith("/")):
         requestURL+="/"
      requestURL+=f"{self._primaryBackendTable}"
      return(requestURL) 

   def rawDataCollect(self):
      if (self._pageNumber is None):
         return([])
      Authorization=self.getAuthorization(self._configSection)
      dataBuffer=[]

      requestURL=self.getApiEndpointURL()

      self._subDataCollectLoopCount+=1
      #if (self._subDataCollectLoopCount>10):
      #   print("to many requests; break")
      #   return([])

      fields_set = set()
      CurrentDepend = set()

      for fldname in self._Field:
         if getattr(self._Field[fldname], "selectfix", False):
             CurrentDepend.add(fldname)

      for fldname in self._CurrentView:
         if fldname in self._Field:
            backendname = self._Field[fldname].getBackendName("select")
            if backendname is not None:
               fields_set.add(backendname)

            depend_list = getattr(self._Field[fldname], "depend", None)
            if depend_list:
               for dfldname in depend_list:
                  if dfldname in self._Field:
                      CurrentDepend.add(dfldname)
                  else:
                      raise ValueError(
                          f"invalid .depend '{dfldname}' in field '{fldname}'"
                      )

      for dfldname in CurrentDepend:
          if dfldname not in self._CurrentView:
              backendname = self._Field[dfldname].getBackendName("select")
              if backendname is not None:
                  fields_set.add(backendname)

      reqParamDict={}
      if (self._primaryBackendTable.startswith("now/table/")): # nativ TableAPI
         reqParamDict={
            "sysparm_suppress_pagination_header"   : "false",
            "sysparm_input_display_value"          : "false",
         #   "sysparm_display_value"                : "all",
            "sysparm_exclude_reference_link"       : "true",
            "sysparm_time_zone" : "UTC"
         }
#         if (self._limitStart>0):
#            reqParamDict["sysparm_offset"]=self._limitStart
#         if (self._limitResult>0):
#            reqParamDict["sysparm_limit"]=self._limitResult

      else:   # Tardis Gateway
         reqParamDict={
            "pageSize"   : 499,
            "pageNumber" : self._pageNumber,
            "sysparm_time_zone" : "UTC"
         }
         # limits ueber das Tardis Gateway passen so sicherlich noch nicht
#         if (self._limitResult>0):   
#            reqParamDict["pageSize"]=self._limitResult
#         if (self._limitStart>0):
#            pageSkip=self._limitStart//reqParamDict["pageSize"]
#            reqParamDict["pageNumber"]=pageSkip


      if (self._sysparm_query):
         reqParamDict["sysparm_query"]=self._sysparm_query

      if fields_set:
         reqParamDict["sysparm_fields"]=",".join(fields_set)

      if (self._sysparm_orderstr):
          reqParamDict['sysparm_query']=\
              f"{reqParamDict['sysparm_query']}{self._sysparm_orderstr}" \
              if self._sysparm_query else self._sysparm_orderstr.lstrip("^")

      reqParam=urllib.parse.urlencode(reqParamDict)

      requestURL=requestURL+'?'+reqParam
      logger.debug(f"requestURL: {requestURL}")

      req = urllib.request.Request(requestURL, method="GET")
      req.add_header("Authorization", Authorization)
      req.add_header("User-Agent",    "C4Request/1.0")
      req.add_header("Content-Type",  "application/x-www-form-urlencoded")
      req.add_header("Accept-Time-Zone","UTC")

      opener = urllib.request.build_opener()
    
      if (config.get(self._configSection,{}).get("HTTP_PROXY",None)=="NONE"):
         no_proxy_handler = urllib.request.ProxyHandler({})
         opener = urllib.request.build_opener(no_proxy_handler)

      with opener.open(req, timeout=5) as response:
         charset = response.headers.get_content_charset(failobj="utf-8")
         #pprint(dict(response.headers))
         result_text = response.read().decode(charset)
         #print(result_text)
         r = json.loads(result_text)
         #pprint(r)
         data=[]
         if (r.get("result",None)):
            if (r.get("result",None).get("code",None)==201):
               return([])
            data=r.get("result",[])
         else:
            data=r.get("data",[])
         dataBuffer.extend(data)
         if (len(data)==0):
            print("no records in data")
            return([])
         paging=r.get("paging",None)
         if (paging):
            self._nextPage=paging.get("nextPage")
            if (self._pageNumber==1):
               maxPages=paging.get("maxPages")

         self._pageNumber=self._nextPage

      return(dataBuffer)





