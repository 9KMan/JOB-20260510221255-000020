"""Export formatters for ETL pipeline (CSV, HL7 v2, FHIR R4)."""

import csv
import io
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ExportResult:
    format: str
    record_count: int
    content: str
    exported_at: datetime = datetime.now()


class CSVExporter:
    def export(self, data: list[dict[str, Any]], filename: str = "export.csv") -> ExportResult:
        if not data:
            return ExportResult(format="csv", record_count=0, content="")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return ExportResult(format="csv", record_count=len(data), content=output.getvalue())


class HL7Exporter:
    SEGMENT_TERMINATOR = "\r"

    def export(self, data: list[dict[str, Any]], msg_type: str = "ORU") -> ExportResult:
        segments = []
        for i, row in enumerate(data):
            msg_id = f"MSG{str(uuid.uuid4())[:8].upper()}"
            segments.append(f"MSH|^~\\&|EHR_SRC|HHSC|RECV_SYS|DEST|{datetime.now().strftime('%Y%m%d%H%M')}|{msg_id}|{msg_type}|2.4")
            segments.append(f"PID|{i+1}|{row.get('PATIENT_ID', '')}||{row.get('LAST_NAME', '')}^{row.get('FIRST_NAME', '')}||{row.get('DOB', '')}|{row.get('SEX_CD', '')}")
            if "ORDER_ID" in row:
                segments.append(f"ORC|{row.get('ORDER_STATUS_CD', 'NW')}|{row.get('ORDER_ID', '')}")
            segments.append(self.SEGMENT_TERMINATOR.rstrip("\r"))

        return ExportResult(
            format="hl7v2",
            record_count=len(data),
            content=self.SEGMENT_TERMINATOR.join(segments),
        )


class FHIRExporter:
    def export(self, data: list[dict[str, Any]], resource_type: str = "Patient") -> ExportResult:
        bundle = {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "type": "collection",
            "timestamp": datetime.now().isoformat(),
            "entry": [],
        }

        for row in data:
            if resource_type == "Patient":
                resource = self._patient_to_fhir(row)
            elif resource_type == "Encounter":
                resource = self._encounter_to_fhir(row)
            elif resource_type == "Observation":
                resource = self._observation_to_fhir(row)
            else:
                resource = row

            bundle["entry"].append({"resource": resource})

        return ExportResult(
            format="fhir_r4",
            record_count=len(data),
            content=json.dumps(bundle, indent=2),
        )

    @staticmethod
    def _patient_to_fhir(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "resourceType": "Patient",
            "id": str(row.get("PATIENT_ID", "")),
            "name": [{"family": row.get("LAST_NAME", ""), "given": [row.get("FIRST_NAME", "")]}],
            "birthDate": row.get("DOB", ""),
            "gender": row.get("SEX_CD", "").lower() if row.get("SEX_CD") else "unknown",
            "address": [{"line": [row.get("ADDRESS_LINE_1", "")], "city": row.get("CITY", ""), "state": row.get("STATE_CD", ""), "postalCode": row.get("ZIP_CD", "")}],
        }

    @staticmethod
    def _encounter_to_fhir(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "resourceType": "Encounter",
            "id": str(row.get("VISIT_ID", "")),
            "subject": {"reference": f"Patient/{row.get('PATIENT_ID', '')}"},
            "status": "finished",
            "class": {"code": row.get("VISIT_TYPE_CD", "")},
            "period": {"start": row.get("ADMIT_DT_TM", ""), "end": row.get("DISCH_DT_TM", "")},
        }

    @staticmethod
    def _observation_to_fhir(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "resourceType": "Observation",
            "id": str(row.get("RESULT_ID", "")),
            "subject": {"reference": f"Patient/{row.get('PATIENT_ID', '')}"},
            "status": "final",
            "code": {"coding": [{"code": row.get("RESULT_TYPE_CD", "")}]},
            "valueQuantity": {"value": row.get("VALUE", ""), "unit": row.get("UNITS", "")},
            "effectiveDateTime": row.get("RESULT_DT_TM", ""),
        }
