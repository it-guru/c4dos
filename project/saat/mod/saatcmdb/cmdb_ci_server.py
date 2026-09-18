from kernel.field   import *
from kernel.dataobj import *


class SaatcmdbCmdb_ci_server(DataObjSQLDB):
   _configSection          = "SAATCMDB"
   _primaryBackendTable    = "cmdb_ci_server"

   name             = FieldText(
      backendname          = _primaryBackendTable+".name",
      label                = "name"
   )
   sysid                   = FieldText(
      backendname          = _primaryBackendTable+".sys_id",
      label                = "sys_id"
   )
   cost_center         = FieldText(
      backendname          = _primaryBackendTable+".cost_center",
      label                = "cost_center"
   )
   discovery_source        = FieldText(
      backendname          = _primaryBackendTable+".discovery_source",
      label                = "discovery_source"
   )
   life_cycle_stage        = FieldText(
      backendname          = _primaryBackendTable+".life_cycle_stage",
      label                = "life_cycle_stage"
   )
   life_cycle_stage_status = FieldText(
      backendname          = _primaryBackendTable+".life_cycle_stage_status",
      label                = "life_cycle_stage_status"
   )
   location = FieldText(
      backendname          = _primaryBackendTable+".location",
      label                = "location"
   )
   object_id = FieldText(
      backendname          = _primaryBackendTable+".object_id",
      label                = "object_id"
   )
   sys_class_name          = FieldText(
      backendname          = _primaryBackendTable+".sys_class_name",
      label                = "sys_class_name"
   )
   used_for                = FieldText(
      backendname          = _primaryBackendTable+".used_for",
      label                = "used_for"
   )
   id               = FieldId(
      backendname          = _primaryBackendTable+".id",
   )
   urlofcurrentrec  = FieldRecordURL()
   recno                   = FieldRecNo(
      label                = "Record Number"
   )
   cleanname               = FieldText(
      backendname          = _primaryBackendTable+".cleanname",
      label                = "cleanname"
   )
   realcomputername        = FieldText(
      backendname          = _primaryBackendTable+".realcomputername",
      label                = "Flexera: realcomputername"
   )
   w5baseid                = FieldText(
      backendname          = _primaryBackendTable+".w5baseid",
      label                = "Flexera: w5baseid"
   )
   computerid              = FieldText(
      backendname          = _primaryBackendTable+".compliancecomputerid",
      label                = "Flexera: ComplianceComputerID"
   )
   mdate            = FieldMDate()

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








