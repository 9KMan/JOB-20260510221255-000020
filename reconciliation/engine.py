"""
Reconciliation engine core - performs source-to-target data comparison.
"""

from datetime import datetime
from typing import Optional, Callable
import hashlib
import logging

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self):
        self._results = {}

    def calculate_checksum(self, data: list[dict], key_columns: list[str]) -> str:
        sorted_data = sorted(data, key=lambda x: tuple(x.get(k) for k in key_columns))
        data_str = str(sorted_data)
        return hashlib.md5(data_str.encode()).hexdigest()

    def compare_row_counts(
        self,
        entity_name: str,
        source_count: int,
        target_count: int,
    ) -> tuple[bool, str]:
        match = source_count == target_count
        message = f"source={source_count}, target={target_count}"
        return match, message

    def find_missing_rows(
        self,
        source_data: list[dict],
        target_data: list[dict],
        key_columns: list[str],
    ) -> list[dict]:
        target_keys = set(
            tuple(row.get(k) for k in key_columns) for row in target_data
        )
        missing = [
            row for row in source_data
            if tuple(row.get(k) for k in key_columns) not in target_keys
        ]
        return missing

    def find_extra_rows(
        self,
        source_data: list[dict],
        target_data: list[dict],
        key_columns: list[str],
    ) -> list[dict]:
        source_keys = set(
            tuple(row.get(k) for k in key_columns) for row in source_data
        )
        extra = [
            row for row in target_data
            if tuple(row.get(k) for k in key_columns) not in source_keys
        ]
        return extra

    def compare_values(
        self,
        source_row: dict,
        target_row: dict,
        columns: list[str],
    ) -> list[str]:
        differences = []
        for col in columns:
            source_val = source_row.get(col)
            target_val = target_row.get(col)
            if source_val != target_val:
                differences.append(
                    f"{col}: source='{source_val}' vs target='{target_val}'"
                )
        return differences

    def run_validation(
        self,
        entity_name: str,
        source_data: list[dict],
        target_data: list[dict],
        key_columns: list[str],
        compare_columns: Optional[list[str]] = None,
    ) -> dict:
        result = {
            "entity_name": entity_name,
            "timestamp": datetime.utcnow().isoformat(),
            "source_count": len(source_data),
            "target_count": len(target_data),
            "row_count_match": len(source_data) == len(target_data),
            "missing_rows": [],
            "extra_rows": [],
            "value_differences": [],
            "checksum_match": False,
        }

        result["checksum_match"] = (
            self.calculate_checksum(source_data, key_columns) ==
            self.calculate_checksum(target_data, key_columns)
        )

        result["missing_rows"] = self.find_missing_rows(
            source_data, target_data, key_columns
        )
        result["extra_rows"] = self.find_extra_rows(
            source_data, target_data, key_columns
        )

        if compare_columns:
            target_dict = {
                tuple(row.get(k) for k in key_columns): row
                for row in target_data
            }
            for source_row in source_data:
                key = tuple(source_row.get(k) for k in key_columns)
                if key in target_dict:
                    diffs = self.compare_values(
                        source_row, target_dict[key], compare_columns
                    )
                    if diffs:
                        result["value_differences"].extend(diffs)

        self._results[entity_name] = result
        return result

    def get_results(self, entity_name: str) -> Optional[dict]:
        return self._results.get(entity_name)

    def list_results(self) -> list[dict]:
        return list(self._results.values())