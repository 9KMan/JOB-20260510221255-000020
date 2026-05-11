"""
CCL Script Library for Cerner Millennium EHR data extraction.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SchemaCategory(Enum):
    HL7 = "HL7"
    FIN = "FIN"
    CDO = "CDO"
    PSD = "PSD"
    HSD = "HSD"
    ARK = "ARK"


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class CCLScript:
    name: str
    category: SchemaCategory
    description: str
    content: str
    schema_area: str
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_modified: datetime = field(default_factory=datetime.utcnow)
    execution_count: int = 0
    avg_execution_time: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "schema_area": self.schema_area,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "execution_count": self.execution_count,
            "avg_execution_time": self.avg_execution_time,
        }


@dataclass
class ExecutionResult:
    script_name: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    rows_affected: int = 0
    output: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "script_name": self.script_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "rows_affected": self.rows_affected,
            "output": self.output,
            "error_message": self.error_message,
        }


class CCLScriptLibrary:
    def __init__(self):
        self._scripts: dict[str, CCLScript] = {}
        self._execution_history: list[ExecutionResult] = []
        self._init_production_scripts()

    def _init_production_scripts(self):
        scripts = [
            CCLScript(
                name="extract_order_proc",
                category=SchemaCategory.PSD,
                description="Extract order procedures from PSD schema",
                schema_area="PSD",
                content=self._ORDER_PROC_CCL,
            ),
            CCLScript(
                name="extract_specimen",
                category=SchemaCategory.PSD,
                description="Extract specimen data from PSD schema",
                schema_area="PSD",
                content=self._SPECIMEN_CCL,
            ),
            CCLScript(
                name="extract_respiratory",
                category=SchemaCategory.PSD,
                description="Extract respiratory results from PSD schema",
                schema_area="PSD",
                content=self._RESPIRATORY_CCL,
            ),
            CCLScript(
                name="extract_clarity_ser",
                category=SchemaCategory.CDO,
                description="Extract service resources from CDO schema",
                schema_area="CDO",
                content=self._CLARITY_SER_CCL,
            ),
            CCLScript(
                name="extract_clarity_dep",
                category=SchemaCategory.CDO,
                description="Extract departments from CDO schema",
                schema_area="CDO",
                content=self._CLARITY_DEP_CCL,
            ),
            CCLScript(
                name="extract_clarity_emp",
                category=SchemaCategory.CDO,
                description="Extract employees from CDO schema",
                schema_area="CDO",
                content=self._CLARITY_EMP_CCL,
            ),
            CCLScript(
                name="extract_order_rec",
                category=SchemaCategory.HSD,
                description="Extract order records from HSD schema",
                schema_area="HSD",
                content=self._ORDER_REC_CCL,
            ),
            CCLScript(
                name="extract_order_misc",
                category=SchemaCategory.HSD,
                description="Extract miscellaneous order data from HSD schema",
                schema_area="HSD",
                content=self._ORDER_MISC_CCL,
            ),
            CCLScript(
                name="extract_patient_visit",
                category=SchemaCategory.HSD,
                description="Extract patient visits from HSD schema",
                schema_area="HSD",
                content=self._PATIENT_VISIT_CCL,
            ),
            CCLScript(
                name="extract_patient",
                category=SchemaCategory.ARK,
                description="Extract patient demographics from ARK schema",
                schema_area="ARK",
                content=self._PATIENT_CCL,
            ),
            CCLScript(
                name="extract_patient_allergy",
                category=SchemaCategory.ARK,
                description="Extract patient allergies from ARK schema",
                schema_area="ARK",
                content=self._PATIENT_ALLERGY_CCL,
            ),
            CCLScript(
                name="extract_patient_diagnosis",
                category=SchemaCategory.ARK,
                description="Extract patient diagnoses from ARK schema",
                schema_area="ARK",
                content=self._PATIENT_DIAGNOSIS_CCL,
            ),
            CCLScript(
                name="extract_account",
                category=SchemaCategory.FIN,
                description="Extract account data from FIN schema",
                schema_area="FIN",
                content=self._ACCOUNT_CCL,
            ),
            CCLScript(
                name="extract_pb_ar",
                category=SchemaCategory.FIN,
                description="Extract accounts receivable from FIN schema",
                schema_area="FIN",
                content=self._PB_AR_CCL,
            ),
            CCLScript(
                name="extract_gb_payment",
                category=SchemaCategory.FIN,
                description="Extract payments from FIN schema",
                schema_area="FIN",
                content=self._GB_PAYMENT_CCL,
            ),
        ]
        for script in scripts:
            self._scripts[script.name] = script

    _ORDER_PROC_CCL = """\
; CCL Script: extract_order_proc
; Schema: PSD
; Purpose: Extract order procedures for EHR migration
free (order_proc_cur, order_proc_val)

call parser(ccl_table)
with order_proc_cur
 select op.ORDER_ID,
        op.PROC_ID,
        op.ORDERING_PROVIDER_ID,
        op.ORDER_STATUS_C,
        op.ORDER_DTTM,
        op.COMPLETE_DTTM,
        op.RESULT_DTTM
 from ORDER_PROC op
 where op.ORDER_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
   and op.ORDER_DTTM <= to_date('{{end_date}}', 'YYYY-MM-DD')
 order by op.ORDER_DTTM desc
with status = 0
"""

    _SPECIMEN_CCL = """\
; CCL Script: extract_specimen
; Schema: PSD
; Purpose: Extract specimen data for EHR migration
free (specimen_cur, specimen_val)

call parser(ccl_table)
with specimen_cur
 select s.SPECIMEN_ID,
        s.PATIENT_ID,
        s.ORDER_ID,
        s.COLLECT_DTTM,
        s.RECEIVE_DTTM,
        s.STATUS_C,
        s.SPECIMEN_TYPE_C
 from SPECIMEN s
 where s.COLLECT_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by s.COLLECT_DTTM desc
with status = 0
"""

    _RESPIRATORY_CCL = """\
; CCL Script: extract_respiratory
; Schema: PSD
; Purpose: Extract respiratory results for EHR migration
free (resp_cur, resp_val)

call parser(ccl_table)
with resp_cur
 select r.RESULT_ID,
        r.PATIENT_ID,
        r.ORDER_ID,
        r.RESULT_DTTM,
        r.TEST_TYPE,
        r.RESULT_VALUE,
        r.UNITS,
        r.NORMAL_RANGE
 from RESPIRATORY r
 where r.RESULT_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by r.RESULT_DTTM desc
with status = 0
"""

    _CLARITY_SER_CCL = """\
; CCL Script: extract_clarity_ser
; Schema: CDO
; Purpose: Extract service resources for organizational hierarchy
free (ser_cur, ser_val)

call parser(ccl_table)
with ser_cur
 select cs.SER_ID,
        cs.SERVICE_NAME,
        cs.DEPT_ID,
        cs.ACTIVE_IND,
        cs.BILLING_PROVIDER_ID
 from CLARITY_SER cs
 where cs.ACTIVE_IND = 1
 order by cs.SERVICE_NAME
with status = 0
"""

    _CLARITY_DEP_CCL = """\
; CCL Script: extract_clarity_dep
; Schema: CDO
; Purpose: Extract department data for organizational hierarchy
free (dep_cur, dep_val)

call parser(ccl_table)
with dep_cur
 select cd.DEPT_ID,
        cd.DEPT_NAME,
        cd.DIVISION_ID,
        cd.LOCATION_C,
        cd.ACTIVE_IND
 from CLARITY_DEP cd
 where cd.ACTIVE_IND = 1
 order by cd.DEPT_NAME
with status = 0
"""

    _CLARITY_EMP_CCL = """\
; CCL Script: extract_clarity_emp
; Schema: CDO
; Purpose: Extract employee data for organizational hierarchy
free (emp_cur, emp_val)

call parser(ccl_table)
with emp_cur
 select ce.EMP_ID,
        ce.EMP_NAME,
        ce.DEPT_ID,
        ce.USER_ID,
        ce.ACTIVE_IND,
        ce.EMP_TYPE_C
 from CLARITY_EMP ce
 where ce.ACTIVE_IND = 1
 order by ce.EMP_NAME
with status = 0
"""

    _ORDER_REC_CCL = """\
; CCL Script: extract_order_rec
; Schema: HSD
; Purpose: Extract order records for visit and encounter data
free (order_rec_cur, order_rec_val)

call parser(ccl_table)
with order_rec_cur
 select or_.ORDER_REC_ID,
        or_.PATIENT_ID,
        or_.ENCOUNTER_ID,
        or_.ORDER_ID,
        or_.ORDER_STATUS_C,
        or_.START_DTTM,
        or_.END_DTTM
 from ORDER_REC or_
 where or_.START_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by or_.START_DTTM desc
with status = 0
"""

    _ORDER_MISC_CCL = """\
; CCL Script: extract_order_misc
; Schema: HSD
; Purpose: Extract miscellaneous order data
free (order_misc_cur, order_misc_val)

call parser(ccl_table)
with order_misc_cur
 select om.ORDER_ID,
        om.MISC_ORDER_TYPE_C,
        om.ORDER_DTTM,
        om.STATUS_C,
        om.ORDERING_PROVIDER_ID
 from ORDER_MISC om
 where om.ORDER_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by om.ORDER_DTTM desc
with status = 0
"""

    _PATIENT_VISIT_CCL = """\
; CCL Script: extract_patient_visit
; Schema: HSD
; Purpose: Extract patient visits for encounter data
free (visit_cur, visit_val)

call parser(ccl_table)
with visit_cur
 select pv.VISIT_ID,
        pv.PATIENT_ID,
        pv.ADMIT_DTTM,
        pv.DISCH_DTTM,
        pv.LOC_ID,
        pv.VISIT_TYPE_C,
        pv.ATTENDING_PROVIDER_ID,
        pv.FINANCIAL_CLASS_C
 from PATIENT_VISIT pv
 where pv.ADMIT_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by pv.ADMIT_DTTM desc
with status = 0
"""

    _PATIENT_CCL = """\
; CCL Script: extract_patient
; Schema: ARK
; Purpose: Extract patient demographics for EHR migration
free (patient_cur, patient_val)

call parser(ccl_table)
with patient_cur
 select p.PATIENT_ID,
        p.MRN,
        p.FIRST_NAME,
        p.LAST_NAME,
        p.DOB,
        p.SEX_C,
        p.ADDRESS_ID,
        p.PHONE_ID,
        p.ACTIVE_IND,
        p.UPDATE_DTTM
 from PATIENT p
 where p.UPDATE_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by p.UPDATE_DTTM desc
with status = 0
"""

    _PATIENT_ALLERGY_CCL = """\
; CCL Script: extract_patient_allergy
; Schema: ARK
; Purpose: Extract patient allergies for clinical data
free (allergy_cur, allergy_val)

call parser(ccl_table)
with allergy_cur
 select pa.ALLERGY_ID,
        pa.PATIENT_ID,
        pa.ALLERGY_TYPE_C,
        pa.ALLERGEN_C,
        pa.SEVERITY_C,
        pa.STATUS_C,
        pa.ONSET_DTTM,
        pa.ALLERGY_ID
 from PATIENT_ALLERGY pa
 where pa.ALLERGY_ID > 0
 order by pa.PATIENT_ID
with status = 0
"""

    _PATIENT_DIAGNOSIS_CCL = """\
; CCL Script: extract_patient_diagnosis
; Schema: ARK
; Purpose: Extract patient diagnoses for clinical data
free (diag_cur, diag_val)

call parser(ccl_table)
with diag_cur
 select pd.DIAGNOSIS_ID,
        pd.PATIENT_ID,
        pd.ENC_ID,
        pd.DIAGNOSIS_C,
        pd.DIAG_TYPE_C,
        pd.ADD_DTTM,
        pd.PRIMARY_IND
 from PATIENT_DIAGNOSIS pd
 where pd.ADD_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by pd.ADD_DTTM desc
with status = 0
"""

    _ACCOUNT_CCL = """\
; CCL Script: extract_account
; Schema: FIN
; Purpose: Extract account data for billing migration
free (account_cur, account_val)

call parser(ccl_table)
with account_cur
 select a.ACCOUNT_ID,
        a.PATIENT_ID,
        a.VISIT_ID,
        a.ACCOUNT_TYPE_C,
        a.ACCOUNT_STATUS_C,
        a.BALANCE_AMT,
        a.CREATE_DTTM,
        a.UPDATE_DTTM
 from ACCOUNT a
 where a.UPDATE_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by a.UPDATE_DTTM desc
with status = 0
"""

    _PB_AR_CCL = """\
; CCL Script: extract_pb_ar
; Schema: FIN
; Purpose: Extract accounts receivable data
free (pb_ar_cur, pb_ar_val)

call parser(ccl_table)
with pb_ar_cur
 select pbr.AR_ID,
        pbr.ACCOUNT_ID,
        pbr.BILL_DATE,
        pbr.DUE_DATE,
        pbr.AMOUNT_DUE,
        pbr.PAYMENT_AMT,
        pbr.AR_STATUS_C,
        pbr.UPDATE_DTTM
 from PB_AR pbr
 where pbr.UPDATE_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by pbr.UPDATE_DTTM desc
with status = 0
"""

    _GB_PAYMENT_CCL = """\
; CCL Script: extract_gb_payment
; Schema: FIN
; Purpose: Extract payment data for billing
free (payment_cur, payment_val)

call parser(ccl_table)
with payment_cur
 select gp.PAYMENT_ID,
        gp.ACCOUNT_ID,
        gp.PAYMENT_DATE,
        gp.PAYMENT_AMT,
        gp.PAYMENT_TYPE_C,
        gp.PAYMENT_STATUS_C,
        gp.CREATE_DTTM
 from GB_PAYMENT gp
 where gp.CREATE_DTTM >= to_date('{{start_date}}', 'YYYY-MM-DD')
 order by gp.CREATE_DTTM desc
with status = 0
"""

    def register_script(self, script: CCLScript) -> None:
        self._scripts[script.name] = script
        logger.info(f"Registered CCL script: {script.name}")

    def get_script(self, name: str) -> Optional[CCLScript]:
        return self._scripts.get(name)

    def list_scripts(self, category: Optional[SchemaCategory] = None) -> list[dict]:
        scripts = list(self._scripts.values())
        if category:
            scripts = [s for s in scripts if s.category == category]
        return [s.to_dict() for s in sorted(scripts, key=lambda s: s.name)]

    def execute_script(
        self, name: str, params: Optional[dict] = None, dry_run: bool = False
    ) -> ExecutionResult:
        script = self._scripts.get(name)
        if not script:
            return ExecutionResult(
                script_name=name,
                status=ExecutionStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=f"Script not found: {name}",
            )

        started_at = datetime.utcnow()
        logger.info(f"Executing CCL script: {name}")

        if dry_run:
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            result = ExecutionResult(
                script_name=name,
                status=ExecutionStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                rows_affected=0,
                output=f"[DRY RUN] CCL script: {name}\nParameters: {params}\n{script.content}",
            )
        else:
            result = self._execute_ccl(script, params, started_at)

        self._execution_history.append(result)
        if result.status == ExecutionStatus.SUCCESS:
            script.execution_count += 1
            if result.duration_seconds:
                script.avg_execution_time = (
                    (script.avg_execution_time * (script.execution_count - 1) + result.duration_seconds)
                    / script.execution_count
                )
        return result

    def _execute_ccl(
        self, script: CCLScript, params: Optional[dict], started_at: datetime
    ) -> ExecutionResult:
        try:
            content = script.content
            if params:
                for key, value in params.items():
                    content = content.replace(f"{{{{{key}}}}}", str(value))

            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()

            return ExecutionResult(
                script_name=script.name,
                status=ExecutionStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                rows_affected=0,
                output=f"CCL script executed: {script.name}\nSchema: {script.schema_area}\nCategory: {script.category.value}",
            )
        except Exception as e:
            return ExecutionResult(
                script_name=script.name,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                error_message=str(e),
            )

    def get_execution_history(self, limit: int = 100) -> list[dict]:
        history = self._execution_history[-limit:]
        return [r.to_dict() for r in history]

    def get_statistics(self) -> dict:
        total_scripts = len(self._scripts)
        total_executions = sum(s.execution_count for s in self._scripts.values())
        successful = sum(1 for r in self._execution_history if r.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for r in self._execution_history if r.status == ExecutionStatus.FAILED)

        return {
            "total_scripts": total_scripts,
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "scripts_by_category": {
                cat.value: len([s for s in self._scripts.values() if s.category.value == cat.value])
                for cat in SchemaCategory
            },
        }


_library = CCLScriptLibrary()


def get_library() -> CCLScriptLibrary:
    return _library