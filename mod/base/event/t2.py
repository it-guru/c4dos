from config import *
from event  import event
from kernel import *


class Event(event):
   def __init__(self):
      #print(f"Construct Event in {__file__}")
      super().__init__()

   def run(self):
      #print(f"run {__file__}")
      o=getModuleObject("base.grp")
      search_criteria=[
         [
           {
              "fullname": "a*"
           }
         ]
      ]

      o.setFilter(search_criteria)

      result=o.getDictList("fullname,mdate")
      pprint(result)

     





