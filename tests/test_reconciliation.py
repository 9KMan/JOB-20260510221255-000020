"""
Tests for Reconciliation Engine.
"""

import pytest
from datetime import datetime
from reconciliation import (
    ReconciliationEngine,
    ReconciliationResult,
    ReconciliationStatus,
    DataQualityScorecard,
)
from reconciliation.engine import Engine
from reconciliation.scorecard import ScorecardGenerator


class TestReconciliationEngine:
    def setup_method(self):
        self.engine = ReconciliationEngine()

    def test_compare_counts_matching(self):
        result = self.engine.compare_counts("TEST", 100, 100)
        assert result.status == ReconciliationStatus.PASS
        assert result.source_count == 100

    def test_compare_counts_mismatching(self):
        result = self.engine.compare_counts("TEST", 100, 99)
        assert result.status == ReconciliationStatus.FAIL

    def test_check_nulls(self):
        data = [{"A": 1, "B": None}, {"A": 2, "B": 3}]
        violations = self.engine.check_nulls(data, ["B"])
        assert len(violations) == 1

    def test_check_duplicates(self):
        data = [{"A": 1, "B": 2}, {"A": 1, "B": 2}, {"A": 3, "B": 4}]
        violations = self.engine.check_duplicates(data, ["A", "B"])
        assert len(violations) == 1

    def test_run_full_reconciliation(self):
        source = [{"A": 1, "B": 2}, {"A": 2, "B": 3}]
        target = [{"A": 1, "B": 2}, {"A": 2, "B": 3}]
        result = self.engine.run_full_reconciliation("TEST", source, target, ["A"], ["A", "B"])
        assert result.entity_name == "TEST"
        assert result.status == ReconciliationStatus.PASS

    def test_get_result(self):
        self.engine.compare_counts("TEST", 50, 50)
        result = self.engine.get_result("TEST")
        assert result is not None
        assert result.entity_name == "TEST"

    def test_get_nonexistent_result(self):
        result = self.engine.get_result("NONEXISTENT")
        assert result is None

    def test_list_results(self):
        self.engine.compare_counts("A", 10, 10)
        self.engine.compare_counts("B", 20, 20)
        results = self.engine.list_results()
        assert len(results) >= 2

    def test_get_summary(self):
        self.engine.compare_counts("TEST", 100, 100)
        summary = self.engine.get_summary()
        assert "total_entities" in summary
        assert "passed" in summary


class TestReconciliationResult:
    def test_to_dict(self):
        result = ReconciliationResult(
            entity_name="TEST",
            source_count=100,
            target_count=100,
            status=ReconciliationStatus.PASS,
            checked_at=datetime.utcnow(),
            differences=[],
            checksum_match=True,
            null_violations=[],
            duplicate_violations=[],
        )
        d = result.to_dict()
        assert d["entity_name"] == "TEST"
        assert d["status"] == "pass"


class TestDataQualityScorecard:
    def test_add_null_violation(self):
        scorecard = DataQualityScorecard("TEST")
        scorecard.add_null_violation("AGE", 5)
        assert scorecard.null_counts["AGE"] == 5

    def test_calculate_score_no_data(self):
        scorecard = DataQualityScorecard("TEST")
        assert scorecard.calculate_score() == 0.0

    def test_calculate_score_perfect(self):
        scorecard = DataQualityScorecard("TEST")
        scorecard.total_rows = 100
        scorecard.null_counts = {}
        scorecard.duplicate_count = 0
        scorecard.validation_errors = []
        assert scorecard.calculate_score() == 100.0


class TestReconciliationEngineModule:
    def setup_method(self):
        self.engine = Engine()

    def test_calculate_checksum(self):
        data = [{"A": 1, "B": 2}, {"A": 3, "B": 4}]
        checksum = self.engine.calculate_checksum(data, ["A"])
        assert len(checksum) == 32

    def test_compare_row_counts_match(self):
        match, msg = self.engine.compare_row_counts("TEST", 100, 100)
        assert match is True

    def test_compare_row_counts_mismatch(self):
        match, msg = self.engine.compare_row_counts("TEST", 100, 99)
        assert match is False

    def test_find_missing_rows(self):
        source = [{"A": 1}, {"A": 2}, {"A": 3}]
        target = [{"A": 1}, {"A": 2}]
        missing = self.engine.find_missing_rows(source, target, ["A"])
        assert len(missing) == 1

    def test_find_extra_rows(self):
        source = [{"A": 1}, {"A": 2}]
        target = [{"A": 1}, {"A": 2}, {"A": 3}]
        extra = self.engine.find_extra_rows(source, target, ["A"])
        assert len(extra) == 1

    def test_run_validation(self):
        source = [{"A": 1, "B": 2}, {"A": 2, "B": 3}]
        target = [{"A": 1, "B": 2}, {"A": 2, "B": 3}]
        result = self.engine.run_validation("TEST", source, target, ["A"])
        assert result["entity_name"] == "TEST"
        assert result["source_count"] == 2


class TestScorecardGenerator:
    def setup_method(self):
        self.recon_engine = ReconciliationEngine()
        self.generator = ScorecardGenerator(self.recon_engine)

    def test_generate_scorecard(self):
        data = [{"A": 1, "B": 2}, {"A": 3, "B": None}]
        scorecard = self.generator.generate_scorecard("TEST", data)
        assert scorecard["entity_name"] == "TEST"
        assert scorecard["total_rows"] == 2

    def test_generate_report(self):
        source = [{"A": 1, "B": 2}]
        target = [{"A": 1, "B": 2}]
        report = self.generator.generate_report("TEST", source, target, ["A"], ["A", "B"])
        assert "entity_name" in report
        assert "reconciliation_result" in report

    def test_generate_daily_summary(self):
        self.recon_engine.compare_counts("A", 100, 100)
        self.recon_engine.compare_counts("B", 50, 49)
        summary = self.generator.generate_daily_summary(["A", "B"])
        assert summary["total_passed"] == 1
        assert summary["total_failed"] == 1