"""Data validation engine for ETL pipeline."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(Enum):
    SCHEMA = "schema"
    REFERENTIAL = "referential"
    CLINICAL = "clinical"
    NULL_CHECK = "null_check"
    DUPLICATE = "duplicate"


@dataclass
class ValidationIssue:
    level: ValidationLevel
    validation_type: ValidationType
    entity_name: str
    field_name: str
    message: str
    row_count: int = 0
    detected_ts: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    entity_name: str
    passed: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.now)
    rows_checked: int = 0
    issues_found: int = 0


class DataValidator:
    REQUIRED_FIELDS = {
        "ORDER_PROC": ["ORDER_ID", "PATIENT_ID", "ORDER_START_DT_TM"],
        "SPECIMEN": ["SPECIMEN_ID", "ORDER_ID", "COLLECT_DT_TM"],
        "RESPIRATORY": ["RESULT_ID", "PATIENT_ID", "RESULT_DT_TM"],
        "CLARITY_SER": ["SER_ID", "SER_NAME"],
        "CLARITY_DEP": ["DEP_ID", "DEP_NAME"],
        "CLARITY_EMP": ["EMP_ID", "EMP_NAME"],
        "ORDER_REC": ["ORDER_ID", "VISIT_ID"],
        "ORDER_MISC": ["ORDER_MISC_ID", "VISIT_ID"],
        "PATIENT_VISIT": ["VISIT_ID", "PATIENT_ID", "ADMIT_DT_TM"],
        "PATIENT": ["PATIENT_ID", "LAST_NAME", "DOB"],
        "PATIENT_ALLERGY": ["ALLERGY_ID", "PATIENT_ID"],
        "PATIENT_DIAGNOSIS": ["DIAGNOSIS_ID", "PATIENT_ID"],
        "ACCOUNT": ["ACCOUNT_ID", "PATIENT_ID"],
        "PB_AR": ["AR_ID", "ACCOUNT_ID"],
        "GB_PAYMENT": ["PAYMENT_ID", "ACCOUNT_ID"],
    }

    def validate_schema(self, entity_name: str, data: list[dict[str, Any]]) -> ValidationResult:
        issues = []
        required = self.REQUIRED_FIELDS.get(entity_name, [])
        if not data:
            return ValidationResult(entity_name=entity_name, passed=True, rows_checked=0)

        sample = data[0]
        for field_name in required:
            if field_name not in sample:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    validation_type=ValidationType.SCHEMA,
                    entity_name=entity_name,
                    field_name=field_name,
                    message=f"Required field '{field_name}' missing from {entity_name}",
                    row_count=len(data),
                ))

        return ValidationResult(
            entity_name=entity_name,
            passed=len(issues) == 0,
            issues=issues,
            rows_checked=len(data),
            issues_found=len(issues),
        )

    def validate_nulls(self, entity_name: str, data: list[dict[str, Any]], null_fields: list[str]) -> ValidationResult:
        issues = []
        for field_name in null_fields:
            null_count = sum(1 for row in data if row.get(field_name) is None)
            if null_count > 0:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    validation_type=ValidationType.NULL_CHECK,
                    entity_name=entity_name,
                    field_name=field_name,
                    message=f"{null_count} null values found in '{field_name}'",
                    row_count=null_count,
                ))
        return ValidationResult(
            entity_name=entity_name,
            passed=len(issues) == 0,
            issues=issues,
            rows_checked=len(data),
            issues_found=len(issues),
        )

    def validate_duplicates(self, entity_name: str, data: list[dict[str, Any]], key_field: str) -> ValidationResult:
        issues = []
        seen: dict[str, int] = {}
        for row in data:
            key = str(row.get(key_field, ""))
            seen[key] = seen.get(key, 0) + 1

        duplicates = {k: v for k, v in seen.items() if v > 1}
        if duplicates:
            total_dupes = sum(v - 1 for v in duplicates.values())
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                validation_type=ValidationType.DUPLICATE,
                entity_name=entity_name,
                field_name=key_field,
                message=f"{total_dupes} duplicate key values in '{key_field}'",
                row_count=total_dupes,
            ))

        return ValidationResult(
            entity_name=entity_name,
            passed=len(duplicates) == 0,
            issues=issues,
            rows_checked=len(data),
            issues_found=len(issues),
        )

    def validate_all(self, entity_name: str, data: list[dict[str, Any]]) -> ValidationResult:
        schema_result = self.validate_schema(entity_name, data)
        null_result = self.validate_nulls(entity_name, data, ["PATIENT_ID", "ORDER_ID"])
        dup_result = self.validate_duplicates(entity_name, data, f"{entity_name[:-1]}_ID")

        all_issues = schema_result.issues + null_result.issues + dup_result.issues
        return ValidationResult(
            entity_name=entity_name,
            passed=schema_result.passed and null_result.passed and dup_result.passed,
            issues=all_issues,
            rows_checked=len(data),
            issues_found=len(all_issues),
        )
