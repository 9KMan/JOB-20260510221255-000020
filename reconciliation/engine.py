"""Data Reconciliation Engine for source-to-target comparison."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ComparisonStatus(Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    SOURCE_MISSING = "source_missing"
    TARGET_MISSING = "target_missing"


@dataclass
class RowCountResult:
    entity_name: str
    source_count: int
    target_count: int
    match: bool
    difference: int
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class ChecksumResult:
    entity_name: str
    source_checksum: str
    target_checksum: str
    match: bool
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class NullCheckResult:
    entity_name: str
    field_name: str
    source_null_count: int
    target_null_count: int
    match: bool
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class DuplicateCheckResult:
    entity_name: str
    key_field: str
    source_duplicates: int
    target_duplicates: int
    match: bool
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReconciliationReport:
    report_id: str
    entity_name: str
    generated_at: datetime
    row_count_result: Optional[RowCountResult] = None
    checksum_result: Optional[ChecksumResult] = None
    null_check_results: list[NullCheckResult] = field(default_factory=list)
    duplicate_check_results: list[DuplicateCheckResult] = field(default_factory=list)
    overall_match: bool = True
    issues_found: int = 0


class DataReconciler:
    def compare_row_counts(self, entity_name: str, source_count: int, target_count: int) -> RowCountResult:
        diff = source_count - target_count
        return RowCountResult(
            entity_name=entity_name,
            source_count=source_count,
            target_count=target_count,
            match=diff == 0,
            difference=diff,
        )

    def compare_checksums(self, entity_name: str, source_data: list[dict[str, Any]], target_data: list[dict[str, Any]]) -> ChecksumResult:
        import hashlib
        import json

        def compute_checksum(data: list[dict[str, Any]]) -> str:
            normalized = [json.dumps(row, sort_keys=True) for row in data]
            combined = "||".join(normalized)
            return hashlib.md5(combined.encode()).hexdigest()

        src_checksum = compute_checksum(source_data)
        tgt_checksum = compute_checksum(target_data)
        return ChecksumResult(
            entity_name=entity_name,
            source_checksum=src_checksum,
            target_checksum=tgt_checksum,
            match=src_checksum == tgt_checksum,
        )

    def check_nulls(self, entity_name: str, field_name: str, source_data: list[dict[str, Any]], target_data: list[dict[str, Any]]) -> NullCheckResult:
        src_nulls = sum(1 for row in source_data if row.get(field_name) is None)
        tgt_nulls = sum(1 for row in target_data if row.get(field_name) is None)
        return NullCheckResult(
            entity_name=entity_name,
            field_name=field_name,
            source_null_count=src_nulls,
            target_null_count=tgt_nulls,
            match=src_nulls == tgt_nulls,
        )

    def check_duplicates(self, entity_name: str, key_field: str, source_data: list[dict[str, Any]], target_data: list[dict[str, Any]]) -> DuplicateCheckResult:
        def count_dupes(data: list[dict[str, Any]]) -> int:
            seen: dict[str, int] = {}
            for row in data:
                key = str(row.get(key_field, ""))
                seen[key] = seen.get(key, 0) + 1
            return sum(1 for v in seen.values() if v > 1)

        src_dupes = count_dupes(source_data)
        tgt_dupes = count_dupes(target_data)
        return DuplicateCheckResult(
            entity_name=entity_name,
            key_field=key_field,
            source_duplicates=src_dupes,
            target_duplicates=tgt_dupes,
            match=src_dupes == tgt_dupes,
        )

    def generate_report(self, entity_name: str, source_data: list[dict[str, Any]], target_data: list[dict[str, Any]]) -> ReconciliationReport:
        report_id = str(uuid.uuid4())[:8]

        row_count_result = self.compare_row_counts(entity_name, len(source_data), len(target_data))
        checksum_result = self.compare_checksums(entity_name, source_data, target_data)

        null_fields = ["PATIENT_ID", "ORDER_ID", "VISIT_ID"]
        null_check_results = []
        for field_name in null_fields:
            result = self.check_nulls(entity_name, field_name, source_data, target_data)
            null_check_results.append(result)

        key_field = f"{entity_name[:-1]}_ID" if entity_name.endswith("S") else f"{entity_name}_ID"
        dup_result = self.check_duplicates(entity_name, key_field, source_data, target_data)
        duplicate_check_results = [dup_result]

        all_match = (
            row_count_result.match
            and checksum_result.match
            and all(n.match for n in null_check_results)
            and dup_result.match
        )

        issues_found = sum(1 for r in [row_count_result, checksum_result] if not r.match)
        issues_found += sum(1 for r in null_check_results if not r.match)
        issues_found += sum(1 for r in duplicate_check_results if not r.match)

        return ReconciliationReport(
            report_id=report_id,
            entity_name=entity_name,
            generated_at=datetime.now(),
            row_count_result=row_count_result,
            checksum_result=checksum_result,
            null_check_results=null_check_results,
            duplicate_check_results=duplicate_check_results,
            overall_match=all_match,
            issues_found=issues_found,
        )
