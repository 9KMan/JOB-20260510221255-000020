"""CCL script execution engine."""

import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class CCLJob:
    job_id: str
    script_name: str
    status: JobStatus
    started_ts: Optional[datetime] = None
    completed_ts: Optional[datetime] = None
    error_message: Optional[str] = None
    result_rows: int = 0


class CCLExecutor:
    def __init__(self, ccl_binary: str = "/usr/bin/ccl"):
        self._binary = ccl_binary
        self._jobs: dict[str, CCLJob] = {}

    def execute(self, script_name: str, params: Optional[dict] = None) -> CCLJob:
        job_id = str(uuid.uuid4())[:8]
        job = CCLJob(
            job_id=job_id,
            script_name=script_name,
            status=JobStatus.RUNNING,
            started_ts=datetime.now(),
        )
        self._jobs[job_id] = job
        try:
            cmd = [self._binary, script_name]
            if params:
                for k, v in params.items():
                    cmd.extend([f"--{k}", str(v)])
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0:
                job.status = JobStatus.SUCCESS
                job.result_rows = self._parse_row_count(result.stdout)
            else:
                job.status = JobStatus.FAILED
                job.error_message = result.stderr.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            job.status = JobStatus.FAILED
            job.error_message = "Execution timeout (>30s)"
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
        job.completed_ts = datetime.now()
        return job

    def get_job(self, job_id: str) -> Optional[CCLJob]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[CCLJob]:
        return list(self._jobs.values())

    @staticmethod
    def _parse_row_count(output: bytes) -> int:
        try:
            lines = output.decode("utf-8", errors="replace").strip().split("\n")
            for line in reversed(lines):
                line = line.strip()
                if line.isdigit():
                    return int(line)
            return 0
        except Exception:
            return 0
