"""
Data Reconciliation Engine for source-to-target comparison.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ReconciliationStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    PENDING = "pending"


@dataclass
class ReconciliationResult:
    entity_name: str
    source_count: int
    target_count: int
    status: ReconciliationStatus
    checked_at: datetime
    differences: list[str]
    checksum_match: bool
    null_violations: list[str]
    duplicate_violations: list[str]

    def to_dict(self) -> dict:
        return {
            "entity_name": self.entity_name,
            "source_count": self.source_count,
            "target_count": self.target_count,
            "status": self.status.value,
            "checked_at": self.checked_at.isoformat(),
            "differences": self.differences,
            "checksum_match": self.checksum_match,
            "null_violations": self.null_violations,
            "duplicate_violations": self.duplicate_violations,
        }


class DataQualityScorecard:
    def __init__(self, entity_name: str):
        self.entity_name = entity_name
        self.total_rows = 0
        self.null_counts: dict[str, int] = {}
        self.duplicate_count = 0
        self.validation_errors: list[str] = []

    def add_null_violation(self, field: str, count: int = 1) -> None:
        self.null_counts[field] = self.null_counts.get(field, 0) + count

    def add_duplicate_violation(self) -> None:
        self.duplicate_count += 1

    def add_validation_error(self, error: str) -> None:
        self.validation_errors.append(error)

    def calculate_score(self) -> float:
        if self.total_rows == 0:
            return 0.0
        null_penalty = sum(self.null_counts.values()) / (self.total_rows * len(self.null_counts)) if self.null_counts else 0
        dup_penalty = self.duplicate_count / self.total_rows
        error_penalty = len(self.validation_errors) / self.total_rows
        return max(0.0, 100.0 * (1 - null_penalty - dup_penalty - error_penalty))

    def to_dict(self) -> dict:
        return {
            "entity_name": self.entity_name,
            "total_rows": self.total_rows,
            "null_counts": self.null_counts,
            "duplicate_count": self.duplicate_count,
            "validation_errors": self.validation_errors,
            "quality_score": self.calculate_score(),
        }


class ReconciliationEngine:
    def __init__(self):
        self._results: dict[str, ReconciliationResult] = {}
        self._scorecards: dict[str, DataQualityScorecard] = {}

    def compare_counts(
        self,
        entity_name: str,
        source_count: int,
        target_count: int,
    ) -> ReconciliationResult:
        status = ReconciliationStatus.PASS
        differences = []

        if source_count != target_count:
            status = ReconciliationStatus.FAIL
            differences.append(f"Count mismatch: source={source_count}, target={target_count}")

        result = ReconciliationResult(
            entity_name=entity_name,
            source_count=source_count,
            target_count=target_count,
            status=status,
            checked_at=datetime.utcnow(),
            differences=differences,
            checksum_match=True,
            null_violations=[],
            duplicate_violations=[],
        )
        self._results[entity_name] = result
        return result

    def validate_checksum(
        self,
        entity_name: str,
        source_checksum: str,
        target_checksum: str,
    ) -> bool:
        match = source_checksum == target_checksum
        logger.info(f"Checksum validation for {entity_name}: {match}")
        if entity_name in self._results:
            self._results[entity_name].checksum_match = match
        return match

    def check_nulls(self, data: list[dict], required_columns: list[str]) -> list[str]:
        violations = []
        for i, row in enumerate(data):
            for col in required_columns:
                if col not in row or row[col] is None:
                    violations.append(f"Row {i}: {col} is null")
        return violations

    def check_duplicates(self, data: list[dict], key_columns: list[str]) -> list[str]:
        seen = {}
        duplicates = []
        for i, row in enumerate(data):
            key = tuple(row.get(k) for k in key_columns)
            if key in seen:
                duplicates.append(f"Row {i}: duplicate of row {seen[key]}")
            seen[key] = i
        return duplicates

    def run_full_reconciliation(
        self,
        entity_name: str,
        source_data: list[dict],
        target_data: list[dict],
        key_columns: list[str],
        required_columns: list[str],
    ) -> ReconciliationResult:
        source_count = len(source_data)
        target_count = len(target_data)

        result = self.compare_counts(entity_name, source_count, target_count)

        source_nulls = self.check_nulls(source_data, required_columns)
        target_nulls = self.check_nulls(target_data, required_columns)

        source_dups = self.check_duplicates(source_data, key_columns)
        target_dups = self.check_duplicates(target_data, key_columns)

        result.null_violations = source_nulls + target_nulls
        result.duplicate_violations = source_dups + target_dups

        if source_nulls or target_nulls:
            result.status = ReconciliationStatus.WARNING
        if source_dups or target_dups:
            result.status = ReconciliationStatus.FAIL

        self._results[entity_name] = result

        scorecard = self._generate_scorecard(entity_name, source_data, required_columns)
        self._scorecards[entity_name] = scorecard

        logger.info(f"Reconciliation for {entity_name}: {result.status.value}")
        return result

    def _generate_scorecard(
        self,
        entity_name: str,
        data: list[dict],
        required_columns: list[str],
    ) -> DataQualityScorecard:
        scorecard = DataQualityScorecard(entity_name)
        scorecard.total_rows = len(data)

        for col in required_columns:
            null_count = sum(1 for row in data if col not in row or row[col] is None)
            if null_count > 0:
                scorecard.add_null_violation(col, null_count)

        key = list(data[0].keys())[:3] if data else []
        dups = self.check_duplicates(data, key)
        for _ in dups:
            scorecard.add_duplicate_violation()

        return scorecard

    def get_result(self, entity_name: str) -> Optional[ReconciliationResult]:
        return self._results.get(entity_name)

    def list_results(self) -> list[ReconciliationResult]:
        return list(self._results.values())

    def get_scorecard(self, entity_name: str) -> Optional[DataQualityScorecard]:
        return self._scorecards.get(entity_name)

    def list_scorecards(self) -> list[DataQualityScorecard]:
        return list(self._scorecards.values())

    def get_summary(self) -> dict:
        total = len(self._results)
        passed = sum(1 for r in self._results.values() if r.status == ReconciliationStatus.PASS)
        failed = sum(1 for r in self._results.values() if r.status == ReconciliationStatus.FAIL)
        warnings = sum(1 for r in self._results.values() if r.status == ReconciliationStatus.WARNING)

        avg_score = sum(s.calculate_score() for s in self._scorecards.values()) / len(self._scorecards) if self._scorecards else 0

        return {
            "total_entities": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "average_quality_score": avg_score,
        }