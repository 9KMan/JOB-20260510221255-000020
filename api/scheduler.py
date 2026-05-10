"""Batch job scheduling for EHR migration pipeline."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class ScheduleStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class JobSchedule:
    schedule_id: str
    job_name: str
    cron_expression: str
    entity_name: str
    export_format: str
    status: ScheduleStatus
    created_ts: datetime = field(default_factory=datetime.now)
    last_run_ts: Optional[datetime] = None
    next_run_ts: Optional[datetime] = None
    enabled: bool = True


class Scheduler:
    def __init__(self):
        self._schedules: dict[str, JobSchedule] = {}

    def add_schedule(
        self,
        job_name: str,
        cron_expression: str,
        entity_name: str,
        export_format: str = "csv",
    ) -> JobSchedule:
        schedule_id = str(uuid.uuid4())[:8]
        schedule = JobSchedule(
            schedule_id=schedule_id,
            job_name=job_name,
            cron_expression=cron_expression,
            entity_name=entity_name,
            export_format=export_format,
            status=ScheduleStatus.ACTIVE,
        )
        self._schedules[schedule_id] = schedule
        return schedule

    def get_schedule(self, schedule_id: str) -> Optional[JobSchedule]:
        return self._schedules.get(schedule_id)

    def list_schedules(self) -> list[JobSchedule]:
        return list(self._schedules.values())

    def pause_schedule(self, schedule_id: str) -> bool:
        schedule = self._schedules.get(schedule_id)
        if schedule:
            schedule.status = ScheduleStatus.PAUSED
            return True
        return False

    def resume_schedule(self, schedule_id: str) -> bool:
        schedule = self._schedules.get(schedule_id)
        if schedule:
            schedule.status = ScheduleStatus.ACTIVE
            return True
        return False

    def cancel_schedule(self, schedule_id: str) -> bool:
        schedule = self._schedules.get(schedule_id)
        if schedule:
            schedule.status = ScheduleStatus.CANCELLED
            return True
        return False
