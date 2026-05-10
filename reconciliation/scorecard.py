"""Data quality scorecard generation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from reconciliation.engine import ReconciliationReport


class QualityScore(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class EntityQualityScore:
    entity_name: str
    quality_score: QualityScore
    row_count_match: bool
    checksum_match: bool
    null_check_pass: bool
    duplicate_check_pass: bool
    overall_percentage: float
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataQualityScorecard:
    generated_at: datetime
    entity_scores: list[EntityQualityScore] = field(default_factory=list)
    overall_score: QualityScore = QualityScore.GOOD
    total_entities: int = 0
    entities_passing: int = 0


class QualityScorecardGenerator:
    def score_entity(self, report: ReconciliationReport) -> EntityQualityScore:
        passing_checks = 0
        total_checks = 4

        if report.row_count_result and report.row_count_result.match:
            passing_checks += 1
        if report.checksum_result and report.checksum_result.match:
            passing_checks += 1
        if all(n.match for n in report.null_check_results):
            passing_checks += 1
        if all(d.match for d in report.duplicate_check_results):
            passing_checks += 1

        percentage = (passing_checks / total_checks) * 100

        if percentage == 100:
            score = QualityScore.EXCELLENT
        elif percentage >= 75:
            score = QualityScore.GOOD
        elif percentage >= 50:
            score = QualityScore.FAIR
        else:
            score = QualityScore.POOR

        return EntityQualityScore(
            entity_name=report.entity_name,
            quality_score=score,
            row_count_match=report.row_count_result.match if report.row_count_result else False,
            checksum_match=report.checksum_result.match if report.checksum_result else False,
            null_check_pass=all(n.match for n in report.null_check_results),
            duplicate_check_pass=all(d.match for d in report.duplicate_check_results),
            overall_percentage=percentage,
        )

    def generate_scorecard(self, reports: list[ReconciliationReport]) -> DataQualityScorecard:
        entity_scores = [self.score_entity(r) for r in reports]

        total_entities = len(entity_scores)
        entities_passing = sum(1 for s in entity_scores if s.quality_score in (QualityScore.EXCELLENT, QualityScore.GOOD))

        overall_pct = sum(s.overall_percentage for s in entity_scores) / total_entities if total_entities > 0 else 0

        if overall_pct == 100:
            overall_score = QualityScore.EXCELLENT
        elif overall_pct >= 75:
            overall_score = QualityScore.GOOD
        elif overall_pct >= 50:
            overall_score = QualityScore.FAIR
        else:
            overall_score = QualityScore.POOR

        return DataQualityScorecard(
            generated_at=datetime.now(),
            entity_scores=entity_scores,
            overall_score=overall_score,
            total_entities=total_entities,
            entities_passing=entities_passing,
        )
