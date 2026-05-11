"""
Tests for ETL Pipeline.
"""

import pytest
from datetime import datetime, timedelta
from etl_pipeline import EntityType, PipelineStatus
from etl_pipeline.orchestrator import Orchestrator, PipelineJob
from etl_pipeline.watermark import WatermarkStore, WatermarkManager, Watermark
from etl_pipeline.validator import Validator, SchemaValidator, ClinicalValidator
from etl_pipeline.exporters import CSVExporter, HL7Exporter, FHIRExporter, ExporterFactory


class TestOrchestrator:
    def setup_method(self):
        self.orchestrator = Orchestrator()

    def test_trigger_extraction(self):
        job = self.orchestrator.trigger_extraction(EntityType.ORDER_PROC, "CSV")
        assert job is not None
        assert job.entity == EntityType.ORDER_PROC
        assert job.status in [PipelineStatus.SUCCESS, PipelineStatus.FAILED]

    def test_get_job_status(self):
        job = self.orchestrator.trigger_extraction(EntityType.PATIENT, "CSV")
        retrieved = self.orchestrator.get_job_status(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id

    def test_list_jobs(self):
        self.orchestrator.trigger_extraction(EntityType.PATIENT_VISIT, "CSV")
        jobs = self.orchestrator.list_jobs()
        assert len(jobs) >= 1

    def test_get_statistics(self):
        self.orchestrator.trigger_extraction(EntityType.ORDER_PROC, "CSV")
        stats = self.orchestrator.get_statistics()
        assert "total_jobs" in stats
        assert "jobs_by_status" in stats


class TestPipelineJob:
    def test_pipeline_job_to_dict(self):
        job = PipelineJob(job_id="test_123", entity=EntityType.PATIENT)
        d = job.to_dict()
        assert d["job_id"] == "test_123"
        assert d["entity"] == "PATIENT"
        assert d["status"] == "pending"


class TestWatermarkStore:
    def test_set_and_get_watermark(self):
        store = WatermarkStore()
        watermark = Watermark(
            entity_name="ORDER_PROC",
            last_extract_ts=datetime.utcnow(),
            rows_extracted=100,
            status="success",
        )
        store.set(watermark)
        retrieved = store.get("ORDER_PROC")
        assert retrieved is not None
        assert retrieved.entity_name == "ORDER_PROC"

    def test_get_nonexistent_watermark(self):
        store = WatermarkStore()
        result = store.get("NONEXISTENT")
        assert result is None

    def test_get_all_watermarks(self):
        store = WatermarkStore()
        w1 = Watermark("A", datetime.utcnow(), 10, "success")
        w2 = Watermark("B", datetime.utcnow(), 20, "success")
        store.set(w1)
        store.set(w2)
        all_w = store.get_all()
        assert len(all_w) == 2


class TestWatermarkManager:
    def test_update_watermark(self):
        store = WatermarkStore()
        manager = WatermarkManager(store)
        w = manager.update("TEST_ENTITY", datetime.utcnow(), 50)
        assert w.entity_name == "TEST_ENTITY"
        assert w.rows_extracted == 50

    def test_get_last_extract_time(self):
        store = WatermarkStore()
        ts = datetime.utcnow()
        store.set(Watermark("ENTITY", ts, 100, "success"))
        manager = WatermarkManager(store)
        result = manager.get_last_extract_time("ENTITY")
        assert result == ts


class TestValidator:
    def test_validate_record(self):
        v = Validator(strict=True)
        record = {"name": "John", "age": 30}
        schema = {"name": "string", "age": "int"}
        assert v.validate_record(record, schema) is True

    def test_validate_record_missing_required(self):
        v = Validator(strict=True)
        record = {"name": "John"}
        schema = {"name": "string", "age": "int"}
        assert v.validate_record(record, schema) is False

    def test_validate_batch(self):
        v = Validator(strict=False)
        records = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
        ]
        schema = {"name": "string", "age": "int"}
        valid, invalid = v.validate_batch(records, schema)
        assert len(valid) == 2
        assert len(invalid) == 0


class TestSchemaValidator:
    def test_validate_schema(self):
        data = [{"A": 1, "B": 2}, {"A": 3, "B": 4}]
        valid, missing = SchemaValidator.validate_schema(data, ["A", "B"])
        assert valid is True
        assert len(missing) == 0

    def test_validate_schema_missing_columns(self):
        data = [{"A": 1}, {"A": 3}]
        valid, missing = SchemaValidator.validate_schema(data, ["A", "B"])
        assert valid is False
        assert "B" in missing

    def test_validate_not_null(self):
        data = [{"A": 1, "B": None}, {"A": 2, "B": 3}]
        violations = SchemaValidator.validate_not_null(data, ["B"])
        assert len(violations) == 1

    def test_validate_uniqueness(self):
        data = [{"A": 1, "B": 2}, {"A": 1, "B": 2}, {"A": 3, "B": 4}]
        violations = SchemaValidator.validate_uniqueness(data, ["A", "B"])
        assert len(violations) == 1


class TestClinicalValidator:
    def test_validate_mrn(self):
        assert ClinicalValidator.validate_mrn("12345") is True
        assert ClinicalValidator.validate_mrn("1234") is False
        assert ClinicalValidator.validate_mrn("") is False

    def test_validate_order_status(self):
        assert ClinicalValidator.validate_order_status("1") is True
        assert ClinicalValidator.validate_order_status("0") is True
        assert ClinicalValidator.validate_order_status("9") is True
        assert ClinicalValidator.validate_order_status("X") is False


class TestCSVExporter:
    def test_export_empty_data(self, tmp_path):
        exporter = CSVExporter(output_dir=str(tmp_path))
        filepath = exporter.export([], "empty.csv")
        assert filepath.endswith("empty.csv")

    def test_export_with_data(self, tmp_path):
        exporter = CSVExporter(output_dir=str(tmp_path))
        data = [{"A": 1, "B": 2}, {"A": 3, "B": 4}]
        filepath = exporter.export(data, "test.csv")
        assert "test.csv" in filepath


class TestHL7Exporter:
    def test_export(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        exporter = HL7Exporter()
        data = [{"PATIENT_ID": "123", "MRN": "456", "LAST_NAME": "Doe", "FIRST_NAME": "John"}]
        filepath = exporter.export(data, "test.hl7")
        assert "test.hl7" in filepath


class TestFHIRExporter:
    def test_convert_to_fhir_patient(self):
        exporter = FHIRExporter()
        record = {"MRN": "123", "LAST_NAME": "Doe", "FIRST_NAME": "John", "DOB": "1990-01-01", "SEX_C": "1"}
        resource = exporter._convert_to_fhir(record, "Patient")
        assert resource["resourceType"] == "Patient"
        assert resource["identifier"][0]["value"] == "123"


class TestExporterFactory:
    def test_create_csv_exporter(self):
        exporter = ExporterFactory.create_exporter("CSV")
        assert isinstance(exporter, CSVExporter)

    def test_create_hl7_exporter(self):
        exporter = ExporterFactory.create_exporter("HL7")
        assert isinstance(exporter, HL7Exporter)

    def test_create_fhir_exporter(self):
        exporter = ExporterFactory.create_exporter("FHIR")
        assert isinstance(exporter, FHIRExporter)

    def test_create_unknown_exporter(self):
        exporter = ExporterFactory.create_exporter("UNKNOWN")
        assert exporter is None