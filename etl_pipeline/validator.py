"""
Data validation module for ETL pipeline.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Validator:
    def __init__(self, strict: bool = False):
        self.strict = strict
        self._errors = []
        self._warnings = []

    def validate_record(self, record: dict, schema: dict) -> bool:
        valid = True
        for field, field_type in schema.items():
            if field not in record:
                if self.strict:
                    self._errors.append(f"Missing required field: {field}")
                    valid = False
                else:
                    self._warnings.append(f"Missing optional field: {field}")
            else:
                value = record[field]
                if not self._check_type(value, field_type):
                    self._errors.append(f"Invalid type for {field}: expected {field_type}, got {type(value)}")
                    valid = False
        return valid

    def _check_type(self, value, expected_type: str) -> bool:
        type_map = {
            "string": str,
            "int": int,
            "float": (int, float),
            "datetime": str,
            "date": str,
        }
        expected = type_map.get(expected_type, object)
        return isinstance(value, expected) or value is None

    def validate_batch(self, records: list[dict], schema: dict) -> tuple[list[dict], list[dict]]:
        valid_records = []
        invalid_records = []
        for record in records:
            if self.validate_record(record, schema):
                valid_records.append(record)
            else:
                invalid_records.append(record)
        return valid_records, invalid_records

    def get_errors(self) -> list[str]:
        return self._errors

    def get_warnings(self) -> list[str]:
        return self._warnings

    def clear(self) -> None:
        self._errors = []
        self._warnings = []


class SchemaValidator:
    @staticmethod
    def validate_schema(data: list[dict], expected_columns: list[str]) -> tuple[bool, list[str]]:
        if not data:
            return True, []
        columns = set(data[0].keys())
        expected = set(expected_columns)
        missing = list(expected - columns)
        extra = list(columns - expected)
        return len(missing) == 0, missing

    @staticmethod
    def validate_foreign_key(
        data: list[dict], fk_column: str, reference_values: set
    ) -> list[str]:
        violations = []
        for i, row in enumerate(data):
            if fk_column in row and row[fk_column] not in reference_values:
                violations.append(f"Row {i}: FK {fk_column}={row[fk_column]} not in reference")
        return violations

    @staticmethod
    def validate_not_null(data: list[dict], columns: list[str]) -> list[str]:
        violations = []
        for i, row in enumerate(data):
            for col in columns:
                if col not in row or row[col] is None:
                    violations.append(f"Row {i}: {col} is NULL")
        return violations

    @staticmethod
    def validate_uniqueness(data: list[dict], key_columns: list[str]) -> list[str]:
        seen = {}
        violations = []
        for i, row in enumerate(data):
            key = tuple(row.get(k) for k in key_columns)
            if key in seen:
                violations.append(f"Row {i}: duplicate of row {seen[key]} for key {key}")
            seen[key] = i
        return violations


class ClinicalValidator:
    @staticmethod
    def validate_dob(dob: str) -> bool:
        try:
            from datetime import datetime
            dt = datetime.strptime(dob, "%Y-%m-%d")
            return dt.year >= 1900 and dt <= datetime.utcnow()
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_mrn(mrn: str) -> bool:
        return bool(mrn and len(mrn) >= 5)

    @staticmethod
    def validate_order_status(status: str) -> bool:
        valid_statuses = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
        return status in valid_statuses

    @staticmethod
    def validate_date_range(start: str, end: str) -> bool:
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            return start_dt <= end_dt
        except (ValueError, TypeError):
            return True