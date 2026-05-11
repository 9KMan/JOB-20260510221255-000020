"""
Reconciliation scorecard generator for data quality reports.
"""

from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ScorecardGenerator:
    def __init__(self, reconciliation_engine):
        self._engine = reconciliation_engine

    def generate_scorecard(self, entity_name: str, data: list[dict]) -> dict:
        from reconciliation import DataQualityScorecard

        scorecard = DataQualityScorecard(entity_name)
        scorecard.total_rows = len(data)

        if not data:
            return scorecard.to_dict()

        columns = list(data[0].keys())
        for col in columns:
            null_count = sum(1 for row in data if col not in row or row[col] is None)
            if null_count > 0:
                scorecard.add_null_violation(col, null_count)

        key_columns = columns[:3] if len(columns) >= 3 else columns
        seen = {}
        for i, row in enumerate(data):
            key = tuple(row.get(k) for k in key_columns)
            if key in seen:
                scorecard.add_duplicate_violation()
            seen[key] = i

        return scorecard.to_dict()

    def generate_report(
        self,
        entity_name: str,
        source_data: list[dict],
        target_data: list[dict],
        key_columns: list[str],
        required_columns: list[str],
    ) -> dict:
        result = self._engine.run_full_reconciliation(
            entity_name, source_data, target_data, key_columns, required_columns
        )

        report = {
            "entity_name": entity_name,
            "reconciliation_result": result.to_dict(),
            "quality_scorecard": self.generate_scorecard(entity_name, source_data),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return report

    def generate_daily_summary(self, entities: list[str]) -> dict:
        summary = {
            "date": datetime.utcnow().date().isoformat(),
            "entities": [],
            "total_passed": 0,
            "total_failed": 0,
            "average_quality_score": 0.0,
        }

        scores = []
        for entity in entities:
            result = self._engine.get_result(entity)
            if result:
                scorecard = self._engine.get_scorecard(entity)
                summary["entities"].append({
                    "entity_name": entity,
                    "status": result.status.value,
                    "quality_score": scorecard.calculate_score() if scorecard else 0.0,
                })
                if result.status.value == "pass":
                    summary["total_passed"] += 1
                elif result.status.value == "fail":
                    summary["total_failed"] += 1
                if scorecard:
                    scores.append(scorecard.calculate_score())

        if scores:
            summary["average_quality_score"] = sum(scores) / len(scores)

        return summary