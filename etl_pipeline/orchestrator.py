"""
ETL Pipeline Orchestrator - coordinates extraction, validation, and export.
"""

from datetime import datetime
from typing import Optional, Iterator
import logging

from etl_pipeline import PipelineStatus, EntityType
from etl_pipeline.db import OracleDB
from etl_pipeline.validator import Validator, SchemaValidator
from etl_pipeline.watermark import WatermarkManager, WatermarkStore
from etl_pipeline.exporters import ExporterFactory, CSVExporter, HL7Exporter, FHIRExporter

logger = logging.getLogger(__name__)


class PipelineJob:
    def __init__(
        self,
        job_id: str,
        entity: EntityType,
        status: PipelineStatus = PipelineStatus.PENDING,
    ):
        self.job_id = job_id
        self.entity = entity
        self.status = status
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.records_processed = 0
        self.error_message: Optional[str] = None
        self.watermark_ts: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "entity": self.entity.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "records_processed": self.records_processed,
            "error_message": self.error_message,
            "watermark_ts": self.watermark_ts.isoformat() if self.watermark_ts else None,
        }


class Orchestrator:
    def __init__(
        self,
        db: Optional[OracleDB] = None,
        watermark_store: Optional[WatermarkStore] = None,
    ):
        self._db = db or OracleDB()
        self._watermark_manager = WatermarkManager(watermark_store or WatermarkStore())
        self._jobs: dict[str, PipelineJob] = {}
        self._validator = Validator(strict=False)

    def _create_job_id(self, entity: EntityType) -> str:
        return f"etl_{entity.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    def trigger_extraction(
        self,
        entity: EntityType,
        export_format: str = "CSV",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PipelineJob:
        job_id = self._create_job_id(entity)
        job = PipelineJob(job_id=job_id, entity=entity, status=PipelineStatus.RUNNING)
        self._jobs[job_id] = job

        logger.info(f"Starting ETL job {job_id} for {entity.value}")

        try:
            data = self._extract_data(entity, start_date, end_date)
            job.records_processed = len(data)

            exporter = ExporterFactory.create_exporter(export_format)
            if exporter:
                output_file = f"{entity.value}_{job_id}.{export_format.lower()}"
                if export_format.upper() == "FHIR":
                    exporter.export(data, entity.value, output_file)
                else:
                    exporter.export(data, output_file)

            job.status = PipelineStatus.SUCCESS
            job.completed_at = datetime.utcnow()
            job.watermark_ts = datetime.utcnow()

            self._watermark_manager.update(
                entity.value, job.watermark_ts, job.records_processed
            )

            logger.info(f"ETL job {job_id} completed: {job.records_processed} records")

        except Exception as e:
            job.status = PipelineStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            logger.error(f"ETL job {job_id} failed: {e}")

        return job

    def _extract_data(
        self,
        entity: EntityType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        last_watermark = self._watermark_manager.get_last_extract_time(entity.value)

        if start_date or last_watermark:
            effective_start = start_date or last_watermark
            logger.info(f"Incremental extract for {entity.value} since {effective_start}")

        return []

    def get_job_status(self, job_id: str) -> Optional[PipelineJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, status: Optional[PipelineStatus] = None) -> list[PipelineJob]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.started_at, reverse=True)

    def get_statistics(self) -> dict:
        total = len(self._jobs)
        by_status = {}
        for job in self._jobs.values():
            status = job.status.value
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_jobs": total,
            "jobs_by_status": by_status,
            "total_records_processed": sum(j.records_processed for j in self._jobs.values()),
        }