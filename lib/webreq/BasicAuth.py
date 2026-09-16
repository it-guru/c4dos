from pprint import pprint
import urllib.request
import urllib.error
import json
from .base import WebReq


class WebReqBasicAuth(WebReq):
   def __init__(self, configsection: str):
      super().__init__(**param)



