"""ETL pipeline orchestration."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from etl_pipeline.db import ConnectionPool, ConnectionConfig
from etl_pipeline.exporters import CSVExporter, ExportResult, FHIRExporter, HL7Exporter
from etl_pipeline.validator import DataValidator, ValidationResult
from etl_pipeline.watermark import WatermarkTracker, ExtractStatus


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class ETLJob:
    job_id: str
    entity_name: str
    status: JobStatus
    started_ts: Optional[datetime] = None
    completed_ts: Optional[datetime] = None
    rows_extracted: int = 0
    rows_exported: int = 0
    validation_result: Optional[ValidationResult] = None
    export_result: Optional[ExportResult] = None
    error_message: Optional[str] = None


class ETLOrchestrator:
    def __init__(self):
        self._pool = ConnectionPool()
        self._watermarks = WatermarkTracker()
        self._validator = DataValidator()
        self._jobs: dict[str, ETLJob] = {}

    def trigger_extract(self, entity_name: str, config: ConnectionConfig, export_format: str = "csv") -> ETLJob:
        job_id = str(uuid.uuid4())[:8]
        job = ETLJob(job_id=job_id, entity_name=entity_name, status=JobStatus.RUNNING, started_ts=datetime.now())
        self._jobs[job_id] = job

        try:
            watermark = self._watermarks.get(entity_name)
            start_ts = watermark.last_extract_ts if watermark else datetime(1900, 1, 1)

            with self._pool.get_connection(config) as conn:
                data = self._pool.execute_query(conn, f"SELECT * FROM {entity_name} WHERE UPDATE_DT_TM > :ts", {"ts": start_ts})

            validation_result = self._validator.validate_all(entity_name, data)

            if export_format == "csv":
                exporter = CSVExporter()
            elif export_format == "hl7":
                exporter = HL7Exporter()
            elif export_format == "fhir":
                exporter = FHIRExporter()
            else:
                exporter = CSVExporter()

            export_result = exporter.export(data)

            job.status = JobStatus.SUCCESS
            job.rows_extracted = len(data)
            job.rows_exported = export_result.record_count
            job.validation_result = validation_result
            job.export_result = export_result

            self._watermarks.update(entity_name, datetime.now(), len(data), ExtractStatus.SUCCESS)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self._watermarks.update(entity_name, datetime.now(), 0, ExtractStatus.FAILED)

        job.completed_ts = datetime.now()
        return job

    def get_status(self, job_id: str) -> Optional[ETLJob]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[ETLJob]:
        return list(self._jobs.values())
