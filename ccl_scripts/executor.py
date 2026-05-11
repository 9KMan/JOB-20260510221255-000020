"""
CCL Script Executor - Runs CCL scripts against Cerner Millennium Oracle database.
"""

import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionJob:
    job_id: str
    script_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None


class CCLExecutor:
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string
        self._active_jobs: dict[str, ExecutionJob] = {}

    def execute(
        self,
        script_name: str,
        params: Optional[dict] = None,
        wait: bool = True,
    ) -> ExecutionJob:
        from ccl_scripts import get_library

        library = get_library()
        result = library.execute_script(script_name, params, dry_run=True)

        job = ExecutionJob(
            job_id=f"job_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            script_name=script_name,
            status=result.status.value,
            started_at=result.started_at,
            completed_at=result.completed_at,
            result=result.to_dict(),
        )
        self._active_jobs[job.job_id] = job
        logger.info(f"Created execution job: {job.job_id} for script: {script_name}")
        return job

    def get_job_status(self, job_id: str) -> Optional[ExecutionJob]:
        return self._active_jobs.get(job_id)

    def list_jobs(self) -> list[ExecutionJob]:
        return list(self._active_jobs.values())