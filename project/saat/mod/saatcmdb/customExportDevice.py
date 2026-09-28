from kernel.field   import *
from kernel.dataobj import *


class SaatcmdbCustomExportDevice(DataObjSQLDB):
   _configSection          = "SAATCMDB"
   _primaryBackendTable    = "customExportDeviceMView"

   name             = FieldText(
      backendname          = _primaryBackendTable+".systemname",
      label                = "systemname"
   )
   realcomputername        = FieldText(
      backendname          = _primaryBackendTable+".realcomputername",
      label                = "realcomputername"
   )
   w5baseid               = FieldId(
      backendname          = _primaryBackendTable+".w5baseid",
   )
   id               = FieldId(
      backendname          = _primaryBackendTable+".flexeradeviceid",
   )

   def validate(self,oldrec: dict, newrec: dict, orgRec: dict):
      #print("in validate of saatcmdb")
      return(True)


#{'data': [{'company': 'TelekomIT',
#           'correlation_id': 'S47294159',
#           'cost_center': 'T-T5A-202019077-10-0001',
#           'discovery_source': 'Darwin',
#           'life_cycle_stage': 'Operational',
#           'life_cycle_stage_status': 'In Use',
#           'location': 'DE.Biere.Am_Schiens_10.T-Systems_Rechenzentrum',
#           'name': 'ede55m',
#           'object_id': 'S47294159',
#           'serviceInstances': [{'assignment_group': '',
#                                 'cost_center': 'T-T5A-202019077-10-0001',
#                                 'life_cycle_stage': 'Operational',
#                                 'name': 'W5Base/Darwin',
#                                 'support_group': 'DT.HUB.DE.DARWIN',
#                                 'sys_id': '9a66443cf7deb11050c0e7311851e05c',
#                                 'used_for': 'Production'}],
#           'sys_class_name': 'Linux Server',
#           'sys_id': 'd639b35959392a10dca9c82df90f2ba0',
#           'sys_updated_on': '2026-09-16T12:07:38.000Z',
#           'used_for': 'Production'}],








