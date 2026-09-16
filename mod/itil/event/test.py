from config import *
from event  import event
from kernel import *


class Event(event):
   def __init__(self):
      print(f"Construct Event in {__file__}")
      super().__init__()

   def run(self):
      print(f"run {__file__}")
      o=getModuleObject("itil.system")
      search_criteria=[
         [
           {
              "name": "a*"
           }
         ]
      ]

      pprint(search_criteria)

      o.setFilter(search_criteria)

      result=o.getDictList("mdate,name,id")
      pprint(result)

     





