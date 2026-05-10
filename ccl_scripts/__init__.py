"""Cerner Millennium CCL Script Library for HHSC EHR Migration."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ScriptCategory(Enum):
    HL7 = "hl7"
    FIN = "fin"
    CDO = "cdo"


from typing import Optional
from datetime import datetime as dt


@dataclass
class CCLScript:
    name: str
    category: ScriptCategory
    description: str
    schema: str
    created_ts: Optional[dt] = None
    version: str = "1.0.0"
    execution_time_sec: Optional[float] = None
    last_run_ts: Optional[dt] = None


class CCLScriptLibrary:
    def __init__(self):
        self._scripts: dict[str, CCLScript] = {}

    def register(self, script: CCLScript) -> None:
        self._scripts[script.name] = script

    def get(self, name: str) -> Optional[CCLScript]:
        return self._scripts.get(name)

    def list_by_category(self, category: ScriptCategory) -> list[CCLScript]:
        return [s for s in self._scripts.values() if s.category == category]

    def all(self) -> list[CCLScript]:
        return list(self._scripts.values())


SCRIPTS = CCLScriptLibrary()


SCRIPTS.register(CCLScript(
    name="extract_orders_psd",
    category=ScriptCategory.HL7,
    description="Extract ORDER_PROC and SPECIMEN records from PSD schema",
    schema="PSD",
    created_ts=datetime.now(),
    version="1.0.0",
))

SCRIPTS.register(CCLScript(
    name="extract_respiratory_results",
    category=ScriptCategory.HL7,
    description="Extract RESPIRATORY results for clinical reporting",
    schema="PSD",
    created_ts=datetime.now(),
    version="1.0.0",
))

SCRIPTS.register(CCLScript(
    name="extract_organizational_hierarchy",
    category=ScriptCategory.CDO,
    description="Extract CLARITY_SER, CLARITY_DEP, CLARITY_EMP for org structure",
    schema="CDO",
    created_ts=datetime.now(),
    version="1.0.0",
))

SCRIPTS.register(CCLScript(
    name="extract_visit_encounters",
    category=ScriptCategory.HL7,
    description="Extract ORDER_REC, ORDER_MISC, PATIENT_VISIT from HSD",
    schema="HSD",
    created_ts=datetime.now(),
    version="1.0.0",
))

SCRIPTS.register(CCLScript(
    name="extract_patient_demographics",
    category=ScriptCategory.CDO,
    description="Extract PATIENT, PATIENT_ALLERGY, PATIENT_DIAGNOSIS from ARK",
    schema="ARK",
    created_ts=datetime.now(),
    version="1.0.0",
))

SCRIPTS.register(CCLScript(
    name="extract_billing_accounts",
    category=ScriptCategory.FIN,
    description="Extract ACCOUNT, PB_AR, GB_PAYMENT from FIN schema",
    schema="FIN",
    created_ts=datetime.now(),
    version="1.0.0",
))