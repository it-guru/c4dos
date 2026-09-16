import sys
sys.dont_write_bytecode = True


from kernel.condition import *
from kernel.field import *
import json

search_criteria = [ # Level 1 (AND)
  [ # Level 2 (OR)
    {"basefeld": "AusdruckA",
        "cpucount": ">4"
    },
    {"department": "IT", "role": "admin dev*"}
  ],
  [ # Level 2 (OR)
    {"ffeld": "Ausd*ruckA", 
     "name": "Egon",
     "nameneg": "!*Egon*",
     "mdate": ">10.03.1999 10:00:00"
    },
    {
        "address": 'Bamberg Koeln "A*"', 
        "street": "abc* cde?",
        "zipcode": ['1234', '5678', '7890'],# List of constants (=) with OR
        "cpucount": 4,
        "mdate": "10.03.1972 10:00:00"
    }
  ]
]
search_criteria = [ # Level 1 (AND)
  [ # Level 2 (OR)
    {
     "name": "!*Egon*",
     "mdate": ">10.03.1999 10:00:00"
    },
    {
     "name": "Dies ist ein test",
     "mdate": ">1972-03-10 17:33:00"
    },
    {
        "zipcode": ['1234', '5678', '7890'],# List of constants (=) with OR
        "mdate": ">10.03.1972 10:00:00 AND <1972-03-10 17:33:00"
    }
  ]
]

fieldmap={
    "fullname": FieldText(
                   name="fullname"
                ),
    "nameneg":     FieldText(
                   name="nameneg"
                ),
    "basefeld":     FieldText(
                   name="basefeld"
                ),
    "cpucount":     FieldText(
                   name="cpucount"
                ),
    "role":     FieldText(
                   name="role"
                ),
    "ffeld":     FieldText(
                   name="ffeld"
                ),
    "zipcode":     FieldText(
                   name="zipcode"
                ),
    "street":     FieldText(
                   name="street"
                ),
    "name":     FieldText(
                   name="name"
                ),
     "mdate":   FieldMDate()
}



print("iquery=%s" % json.dumps(search_criteria,indent=2))

ast=ConditionalAST(search_criteria,fieldmap)

print("astree=%s" % json.dumps(ast.getAST().to_dict(),indent=2))

ASTprocessor=ConditionSQL()
wherestr,qparam=ASTprocessor.compile(ast.getAST())
print("where=%s" % wherestr)
print("qparam=%s" % json.dumps(qparam,indent=2))


#m=kernel.condition.Static.Compiler()
#matcher=m.compile(ast)
#print("Static matcher code=%s" % matcher.__source__)


