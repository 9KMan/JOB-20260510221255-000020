"""
Exporters for ETL pipeline - CSV, HL7, FHIR formats.
"""

import csv
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class CSVExporter:
    def __init__(self, output_dir: str = "/tmp/exports"):
        self.output_dir = output_dir

    def export(self, data: list[dict], filename: str) -> str:
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = f"{self.output_dir}/{filename}"

        if not data:
            with open(filepath, 'w', newline='') as f:
                pass
            return filepath

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Exported {len(data)} rows to {filepath}")
        return filepath

    def export_streaming(self, data_iter, filename: str) -> str:
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = f"{self.output_dir}/{filename}"

        first_chunk = next(data_iter, None)
        if first_chunk is None:
            with open(filepath, 'w', newline='') as f:
                pass
            return filepath

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=first_chunk.keys())
            writer.writeheader()
            writer.writerow(first_chunk)
            for chunk in data_iter:
                writer.writerows(chunk)

        logger.info(f"Exported streaming data to {filepath}")
        return filepath


class HL7Exporter:
    TERMINATOR = "\r"
    SEPARATOR = "|"
    FIELD_SEPARATOR = "^"

    def __init__(self):
        self.version = "2.3"

    def export(self, data: list[dict], filename: str) -> str:
        filepath = f"/tmp/exports/{filename}"
        logger.info(f"Exporting {len(data)} records to HL7 v{self.version} format: {filepath}")

        with open(filepath, 'w') as f:
            for record in data:
                message = self._build_hl7_message(record)
                f.write(message + self.TERMINATOR)

        return filepath

    def _build_hl7_message(self, record: dict) -> str:
        segments = []
        segments.append(f"MSH|^~\\&|EHR|SYSTEM|RECV|SYSTEM|{datetime.utcnow().strftime('%Y%m%d%H%M%S')}||{self.version}")
        segments.append(f"PID|{record.get('PATIENT_ID', '')}|{record.get('MRN', '')}||{record.get('LAST_NAME', '')}^{record.get('FIRST_NAME', '')}")
        segments.append(f"PV1|{record.get('VISIT_ID', '')}|{record.get('VISIT_TYPE', 'O')}")
        return "\n".join(segments)


class FHIRExporter:
    def __init__(self):
        self.resource_types = {
            "PATIENT": "Patient",
            "ORDER_PROC": "ServiceRequest",
            "PATIENT_VISIT": "Encounter",
            "SPECIMEN": "Specimen",
            "PATIENT_DIAGNOSIS": "Condition",
            "PATIENT_ALLERGY": "AllergyIntolerance",
        }

    def export(self, data: list[dict], resource_type: str, filename: str) -> str:
        import os
        os.makedirs("/tmp/exports", exist_ok=True)
        filepath = f"/tmp/exports/{filename}"

        fhir_type = self.resource_types.get(resource_type, "Resource")
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"resource": self._convert_to_fhir(record, fhir_type)}
                for record in data
            ],
        }

        with open(filepath, 'w') as f:
            json.dump(bundle, f, indent=2)

        logger.info(f"Exported {len(data)} FHIR {fhir_type} resources to {filepath}")
        return filepath

    def _convert_to_fhir(self, record: dict, resource_type: str) -> dict:
        resource: dict = {"resourceType": resource_type}

        if resource_type == "Patient":
            resource["identifier"] = [{"value": str(record.get("MRN", ""))}]
            resource["name"] = [{"family": str(record.get("LAST_NAME", "")), "given": [str(record.get("FIRST_NAME", ""))]}]
            if record.get("DOB"):
                resource["birthDate"] = str(record.get("DOB"))
            if record.get("SEX_C"):
                resource["gender"] = "male" if str(record.get("SEX_C")) == "1" else "female"

        elif resource_type == "Encounter":
            resource["id"] = str(record.get("VISIT_ID", ""))
            resource["status"] = "finished"

        elif resource_type == "ServiceRequest":
            resource["id"] = str(record.get("ORDER_ID", ""))
            resource["status"] = str(record.get("ORDER_STATUS_C", "unknown"))

        else:
            resource["id"] = str(record.get("PATIENT_ID", ""))

        return resource


class ExporterFactory:
    @staticmethod
    def create_exporter(format_type: str) -> "CSVExporter | HL7Exporter | FHIRExporter | None":
        exporters = {
            "csv": CSVExporter,
            "CSV": CSVExporter,
            "hl7": HL7Exporter,
            "HL7": HL7Exporter,
            "fhir": FHIRExporter,
            "FHIR": FHIRExporter,
        }
        exporter_class = exporters.get(format_type)
        return exporter_class() if exporter_class else None