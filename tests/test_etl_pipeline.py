"""Tests for ETL Pipeline."""

import pytest
from etl_pipeline.validator import DataValidator, ValidationLevel, ValidationType
from etl_pipeline.exporters import CSVExporter, HL7Exporter, FHIRExporter
from etl_pipeline.watermark import WatermarkTracker, ExtractStatus


def test_data_validator_schema():
    validator = DataValidator()
    data = [
        {"ORDER_ID": "1", "PATIENT_ID": "100", "ORDER_START_DT_TM": "2024-01-01"},
        {"ORDER_ID": "2", "PATIENT_ID": "101", "ORDER_START_DT_TM": "2024-01-02"},
    ]
    result = validator.validate_schema("ORDER_PROC", data)
    assert result.passed is True


def test_data_validator_schema_missing_field():
    validator = DataValidator()
    data = [
        {"ORDER_ID": "1", "PATIENT_ID": "100"},
    ]
    result = validator.validate_schema("ORDER_PROC", data)
    assert result.passed is False
    assert result.issues_found > 0


def test_data_validator_nulls():
    validator = DataValidator()
    data = [
        {"ORDER_ID": "1", "PATIENT_ID": None},
        {"ORDER_ID": "2", "PATIENT_ID": "101"},
    ]
    result = validator.validate_nulls("ORDER_PROC", data, ["PATIENT_ID"])
    assert result.passed is False
    assert any(i.field_name == "PATIENT_ID" for i in result.issues)


def test_data_validator_duplicates():
    validator = DataValidator()
    data = [
        {"ORDER_ID": "1", "PATIENT_ID": "100"},
        {"ORDER_ID": "1", "PATIENT_ID": "101"},
        {"ORDER_ID": "2", "PATIENT_ID": "102"},
    ]
    result = validator.validate_duplicates("ORDER_PROC", data, "ORDER_ID")
    assert result.passed is False


def test_csv_exporter():
    exporter = CSVExporter()
    data = [
        {"ORDER_ID": "1", "PATIENT_ID": "100"},
        {"ORDER_ID": "2", "PATIENT_ID": "101"},
    ]
    result = exporter.export(data)
    assert result.format == "csv"
    assert result.record_count == 2
    assert "ORDER_ID" in result.content


def test_hl7_exporter():
    exporter = HL7Exporter()
    data = [
        {"PATIENT_ID": "100", "LAST_NAME": "Smith", "FIRST_NAME": "John", "DOB": "1980-01-01", "SEX_CD": "M"},
    ]
    result = exporter.export(data)
    assert result.format == "hl7v2"
    assert "MSH" in result.content


def test_fhir_exporter():
    exporter = FHIRExporter()
    data = [
        {"PATIENT_ID": "100", "LAST_NAME": "Smith", "FIRST_NAME": "John", "DOB": "1980-01-01", "SEX_CD": "M"},
    ]
    result = exporter.export(data, resource_type="Patient")
    assert result.format == "fhir_r4"
    assert "Patient" in result.content


def test_watermark_tracker():
    tracker = WatermarkTracker()
    from datetime import datetime
    wm = tracker.update("ORDER_PROC", datetime.now(), 100, ExtractStatus.SUCCESS)
    assert wm.entity_name == "ORDER_PROC"
    assert wm.rows_extracted == 100
    retrieved = tracker.get("ORDER_PROC")
    assert retrieved is not None
    assert retrieved.rows_extracted == 100
