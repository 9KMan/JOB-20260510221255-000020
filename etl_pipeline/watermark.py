"""
Watermark tracking for incremental CDC extraction.
"""

from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Watermark:
    def __init__(
        self,
        entity_name: str,
        last_extract_ts: datetime,
        rows_extracted: int,
        status: str = "success",
    ):
        self.entity_name = entity_name
        self.last_extract_ts = last_extract_ts
        self.rows_extracted = rows_extracted
        self.status = status
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "entity_name": self.entity_name,
            "last_extract_ts": self.last_extract_ts.isoformat(),
            "rows_extracted": self.rows_extracted,
            "status": self.status,
            "updated_at": self.updated_at.isoformat(),
        }


class WatermarkStore:
    def __init__(self):
        self._watermarks: dict[str, Watermark] = {}

    def get(self, entity_name: str) -> Optional[Watermark]:
        return self._watermarks.get(entity_name)

    def set(self, watermark: Watermark) -> None:
        self._watermarks[watermark.entity_name] = watermark
        logger.info(f"Watermark updated: {watermark.entity_name} -> {watermark.rows_extracted} rows at {watermark.last_extract_ts}")

    def get_all(self) -> dict[str, Watermark]:
        return dict(self._watermarks)

    def delete(self, entity_name: str) -> bool:
        if entity_name in self._watermarks:
            del self._watermarks[entity_name]
            return True
        return False

    def reset(self, entity_name: str) -> None:
        self._watermarks[entity_name] = Watermark(
            entity_name=entity_name,
            last_extract_ts=datetime(1900, 1, 1),
            rows_extracted=0,
            status="reset",
        )
        logger.info(f"Watermark reset for {entity_name}")


class WatermarkManager:
    def __init__(self, store: WatermarkStore):
        self._store = store

    def get_last_extract_time(self, entity_name: str) -> Optional[datetime]:
        watermark = self._store.get(entity_name)
        return watermark.last_extract_ts if watermark else None

    def update(self, entity_name: str, ts: datetime, rows: int, status: str = "success") -> Watermark:
        watermark = Watermark(
            entity_name=entity_name,
            last_extract_ts=ts,
            rows_extracted=rows,
            status=status,
        )
        self._store.set(watermark)
        return watermark

    def get_watermarks(self) -> list[dict]:
        return [w.to_dict() for w in self._store.get_all().values()]