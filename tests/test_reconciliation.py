"""Tests for Data Reconciliation Engine."""

import pytest
from reconciliation.engine import DataReconciler
from reconciliation.scorecard import QualityScorecardGenerator, QualityScore


def test_data_reconciler_row_counts():
    reconciler = DataReconciler()
    result = reconciler.compare_row_counts("ORDER_PROC", 100, 100)
    assert result.match is True
    assert result.difference == 0


def test_data_reconciler_row_counts_mismatch():
    reconciler = DataReconciler()
    result = reconciler.compare_row_counts("ORDER_PROC", 100, 95)
    assert result.match is False
    assert result.difference == 5


def test_data_reconciler_checksums():
    reconciler = DataReconciler()
    source = [{"ORDER_ID": "1", "PATIENT_ID": "100"}, {"ORDER_ID": "2", "PATIENT_ID": "101"}]
    target = [{"ORDER_ID": "1", "PATIENT_ID": "100"}, {"ORDER_ID": "2", "PATIENT_ID": "101"}]
    result = reconciler.compare_checksums("ORDER_PROC", source, target)
    assert result.match is True


def test_data_reconciler_checksums_mismatch():
    reconciler = DataReconciler()
    source = [{"ORDER_ID": "1", "PATIENT_ID": "100"}]
    target = [{"ORDER_ID": "2", "PATIENT_ID": "101"}]
    result = reconciler.compare_checksums("ORDER_PROC", source, target)
    assert result.match is False


def test_data_reconciler_nulls():
    reconciler = DataReconciler()
    source = [{"PATIENT_ID": "100"}, {"PATIENT_ID": None}]
    target = [{"PATIENT_ID": "100"}, {"PATIENT_ID": None}]
    result = reconciler.check_nulls("ORDER_PROC", "PATIENT_ID", source, target)
    assert result.match is True
    assert result.source_null_count == 1


def test_data_reconciler_duplicates():
    reconciler = DataReconciler()
    source = [{"ORDER_ID": "1"}, {"ORDER_ID": "1"}, {"ORDER_ID": "2"}]
    target = [{"ORDER_ID": "1"}, {"ORDER_ID": "1"}, {"ORDER_ID": "2"}]
    result = reconciler.check_duplicates("ORDER_PROC", "ORDER_ID", source, target)
    assert result.match is True
    assert result.source_duplicates == 1


def test_reconciliation_report_generation():
    reconciler = DataReconciler()
    source = [{"ORDER_ID": "1", "PATIENT_ID": "100"}, {"ORDER_ID": "2", "PATIENT_ID": "101"}]
    target = [{"ORDER_ID": "1", "PATIENT_ID": "100"}, {"ORDER_ID": "2", "PATIENT_ID": "101"}]
    report = reconciler.generate_report("ORDER_PROC", source, target)
    assert report.overall_match is True
    assert report.issues_found == 0


def test_quality_scorecard_generator():
    reconciler = DataReconciler()
    generator = QualityScorecardGenerator()
    source = [{"ORDER_ID": "1", "PATIENT_ID": "100"}]
    target = [{"ORDER_ID": "1", "PATIENT_ID": "100"}]
    report = reconciler.generate_report("ORDER_PROC", source, target)
    scorecard = generator.generate_scorecard([report])
    assert scorecard.total_entities == 1
    assert scorecard.entities_passing == 1
