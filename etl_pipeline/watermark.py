"""Python ETL Pipeline for Cerner Millennium data extraction."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ExtractStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"


@dataclass
class Watermark:
    entity_name: str
    last_extract_ts: datetime
    rows_extracted: int
    status: ExtractStatus


@dataclass
class ETLWatermarkTable:
    entity_name: str
    last_extract_ts: datetime
    rows_extracted: int
    status: str


class WatermarkTracker:
    def __init__(self):
        self._watermarks: dict[str, Watermark] = {}

    def get(self, entity_name: str) -> Optional[Watermark]:
        return self._watermarks.get(entity_name)

    def update(self, entity_name: str, last_extract_ts: datetime, rows_extracted: int, status: ExtractStatus) -> Watermark:
        wm = Watermark(
            entity_name=entity_name,
            last_extract_ts=last_extract_ts,
            rows_extracted=rows_extracted,
            status=status,
        )
        self._watermarks[entity_name] = wm
        return wm

    def all(self) -> list[Watermark]:
        return list(self._watermarks.values())
