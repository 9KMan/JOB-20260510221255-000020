"""
ETL Pipeline for Cerner Millennium Oracle CDC extraction.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Iterator
import logging

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class EntityType(Enum):
    ORDER_PROC = "ORDER_PROC"
    SPECIMEN = "SPECIMEN"
    RESPIRATORY = "RESPIRATORY"
    CLARITY_SER = "CLARITY_SER"
    CLARITY_DEP = "CLARITY_DEP"
    CLARITY_EMP = "CLARITY_EMP"
    ORDER_REC = "ORDER_REC"
    ORDER_MISC = "ORDER_MISC"
    PATIENT_VISIT = "PATIENT_VISIT"
    PATIENT = "PATIENT"
    PATIENT_ALLERGY = "PATIENT_ALLERGY"
    PATIENT_DIAGNOSIS = "PATIENT_DIAGNOSIS"
    ACCOUNT = "ACCOUNT"
    PB_AR = "PB_AR"
    GB_PAYMENT = "GB_PAYMENT"


@dataclass
class Watermark:
    entity_name: str
    last_extract_ts: datetime
    rows_extracted: int
    status: str
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineJob:
    job_id: str
    entity: EntityType
    status: PipelineStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    watermark: Optional[Watermark] = None
    error_message: Optional[str] = None
    records_processed: int = 0


class PipelineDB:
    def __init__(self):
        self._watermarks: dict[str, Watermark] = {}
        self._jobs: dict[str, PipelineJob] = {}

    def get_watermark(self, entity_name: str) -> Optional[Watermark]:
        return self._watermarks.get(entity_name)

    def update_watermark(self, watermark: Watermark) -> None:
        self._watermarks[watermark.entity_name] = watermark
        logger.info(f"Updated watermark for {watermark.entity_name}: {watermark.rows_extracted} rows at {watermark.last_extract_ts}")

    def save_job(self, job: PipelineJob) -> None:
        self._jobs[job.job_id] = job

    def get_job(self, job_id: str) -> Optional[PipelineJob]:
        return self._jobs.get(job_id)


_db = PipelineDB()


def get_db() -> PipelineDB:
    return _db


class OracleConnector:
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string
        self._connected = False

    def connect(self) -> bool:
        logger.info("Oracle connector initialized (mock mode)")
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def execute_query(self, query: str, params: Optional[dict] = None) -> list[dict]:
        logger.info(f"Executing query (mock): {query[:100]}...")
        return []

    def stream_query(self, query: str, params: Optional[dict] = None, batch_size: int = 1000) -> Iterator[list[dict]]:
        logger.info(f"Streaming query (mock): {query[:100]}...")
        yield []


class WatermarkTracker:
    def __init__(self, db: PipelineDB):
        self._db = db

    def get_watermark(self, entity_name: str) -> Optional[datetime]:
        watermark = self._db.get_watermark(entity_name)
        return watermark.last_extract_ts if watermark else None

    def update_watermark(self, entity_name: str, ts: datetime, rows: int) -> None:
        watermark = Watermark(
            entity_name=entity_name,
            last_extract_ts=ts,
            rows_extracted=rows,
            status="success",
            updated_at=datetime.utcnow(),
        )
        self._db.update_watermark(watermark)

    def get_all_watermarks(self) -> dict[str, Watermark]:
        return dict(self._db._watermarks)


class DataValidator:
    @staticmethod
    def validate_schema(data: list[dict], expected_columns: list[str]) -> tuple[bool, list[str]]:
        if not data:
            return True, []
        columns = set(data[0].keys())
        expected = set(expected_columns)
        missing = expected - columns
        extra = columns - expected
        return len(missing) == 0 and len(extra) == 0, list(missing)

    @staticmethod
    def check_nulls(data: list[dict], required_columns: list[str]) -> list[str]:
        null_rows = []
        for i, row in enumerate(data):
            for col in required_columns:
                if col not in row or row[col] is None:
                    null_rows.append(f"Row {i}: {col} is null")
        return null_rows

    @staticmethod
    def check_duplicates(data: list[dict], key_columns: list[str]) -> list[str]:
        seen = set()
        duplicates = []
        for i, row in enumerate(data):
            key = tuple(row.get(k) for k in key_columns)
            if key in seen:
                duplicates.append(f"Row {i}: duplicate key {key}")
            seen.add(key)
        return duplicates


class IncrementalExtractor:
    def __init__(self, connector: OracleConnector, watermark_tracker: WatermarkTracker):
        self._connector = connector
        self._watermark_tracker = watermark_tracker

    def extract(
        self,
        entity: EntityType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        entity_name = entity.value
        last_watermark = self._watermark_tracker.get_watermark(entity_name)

        if last_watermark:
            logger.info(f"Incremental extract for {entity_name} since {last_watermark}")
            start_date = last_watermark

        query = f"SELECT * FROM {entity_name}"
        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append(f"UPDATE_DTTM >= TO_DATE('{start_date.isoformat()}', 'YYYY-MM-DD HH24:MI:SS')")
            if end_date:
                conditions.append(f"UPDATE_DTTM <= TO_DATE('{end_date.isoformat()}', 'YYYY-MM-DD HH24:MI:SS')")
            query += " WHERE " + " AND ".join(conditions)

        data = self._connector.execute_query(query)
        logger.info(f"Extracted {len(data)} records from {entity_name}")
        return data

    def extract_incremental(self, entity: EntityType, batch_size: int = 1000) -> Iterator[list[dict]]:
        entity_name = entity.value
        last_watermark = self._watermark_tracker.get_watermark(entity_name)

        if last_watermark:
            logger.info(f"Streaming incremental extract for {entity_name} since {last_watermark}")
            query = f"SELECT * FROM {entity_name} WHERE UPDATE_DTTM >= TO_DATE('{last_watermark.isoformat()}', 'YYYY-MM-DD HH24:MI:SS')"
        else:
            query = f"SELECT * FROM {entity_name}"

        for batch in self._connector.stream_query(query, batch_size=batch_size):
            yield batch


class CSVExporter:
    def __init__(self, output_dir: str = "/tmp/exports"):
        self.output_dir = output_dir

    def export(self, data: list[dict], filename: str) -> str:
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        logger.info(f"Exporting {len(data)} records to {filepath}")
        return filepath


class HL7Exporter:
    def __init__(self):
        pass

    def export(self, data: list[dict], filename: str) -> str:
        logger.info(f"Exporting {len(data)} records to HL7 format: {filename}")
        return filename


class FHIRExporter:
    def __init__(self):
        pass

    def export(self, data: list[dict], resource_type: str, filename: str) -> str:
        logger.info(f"Exporting {len(data)} {resource_type} resources to FHIR format: {filename}")
        return filename


class ETLOrchestrator:
    def __init__(
        self,
        connector: OracleConnector,
        watermark_tracker: WatermarkTracker,
        validator: DataValidator,
    ):
        self._connector = connector
        self._watermark_tracker = watermark_tracker
        self._validator = validator
        self._jobs: dict[str, PipelineJob] = {}

    def run_extraction(
        self,
        entity: EntityType,
        export_format: str = "CSV",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PipelineJob:
        job_id = f"etl_{entity.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        job = PipelineJob(
            job_id=job_id,
            entity=entity,
            status=PipelineStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        self._jobs[job_id] = job

        try:
            extractor = IncrementalExtractor(self._connector, self._watermark_tracker)
            data = extractor.extract(entity, start_date, end_date)

            if export_format == "CSV":
                exporter = CSVExporter()
                filepath = exporter.export(data, f"{entity.value}_{job_id}.csv")
            elif export_format == "HL7":
                exporter = HL7Exporter()
                filepath = exporter.export(data, f"{entity.value}_{job_id}.hl7")
            elif export_format == "FHIR":
                exporter = FHIRExporter()
                filepath = exporter.export(data, entity.value, f"{entity.value}_{job_id}.json")
            else:
                raise ValueError(f"Unknown export format: {export_format}")

            job.status = PipelineStatus.SUCCESS
            job.completed_at = datetime.utcnow()
            job.records_processed = len(data)

            watermark_ts = datetime.utcnow()
            self._watermark_tracker.update_watermark(entity.value, watermark_ts, len(data))
            job.watermark = self._watermark_tracker.get_watermark(entity.value)

            logger.info(f"ETL job {job_id} completed: {len(data)} records processed")

        except Exception as e:
            job.status = PipelineStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            logger.error(f"ETL job {job_id} failed: {e}")

        return job

    def get_job_status(self, job_id: str) -> Optional[PipelineJob]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[PipelineJob]:
        return list(self._jobs.values())