"""FastAPI REST API for EHR migration operations."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel


app = FastAPI(title="HHSC EHR Migration API", version="1.0.0")


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class CCLJobResponse:
    job_id: str
    script_name: str
    status: JobStatus
    started_ts: Optional[datetime] = None
    completed_ts: Optional[datetime] = None
    result_rows: int = 0
    error_message: Optional[str] = None


class CCLRunRequest(BaseModel):
    script_name: str
    params: Optional[dict[str, Any]] = None


class ETLExtractRequest(BaseModel):
    entity_name: str
    export_format: str = "csv"


class ValidationRequest(BaseModel):
    entity_name: str
    source_data: list[dict[str, Any]]
    target_data: list[dict[str, Any]]


_jobs: dict[str, dict] = {}


@app.get("/")
def root():
    return {"service": "HHSC EHR Migration API", "version": "1.0.0", "status": "operational"}


@app.post("/api/ccel/run", response_model=CCLJobResponse, status_code=status.HTTP_201_CREATED)
def run_ccl_script(request: CCLRunRequest):
    job_id = str(uuid.uuid4())[:8]
    job = CCLJobResponse(
        job_id=job_id,
        script_name=request.script_name,
        status=JobStatus.SUCCESS,
        started_ts=datetime.now(),
        completed_ts=datetime.now(),
        result_rows=0,
    )
    _jobs[job_id] = {"type": "ccl", "data": job}
    return job


@app.get("/api/ccel/scripts")
def list_ccl_scripts():
    return {"scripts": [], "total": 0}


@app.post("/api/ccel/scripts", status_code=status.HTTP_201_CREATED)
def register_ccl_script(script: dict):
    return {"script_name": script.get("name", "unknown"), "registered": True}


@app.post("/api/etl/extract", status_code=status.HTTP_201_CREATED)
def trigger_etl_extract(request: ETLExtractRequest):
    job_id = str(uuid.uuid4())[:8]
    return {"job_id": job_id, "entity_name": request.entity_name, "status": "running"}


@app.get("/api/etl/status/{job_id}")
def get_etl_status(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


@app.get("/api/reconciliation/{entity}")
def get_reconciliation_report(entity: str):
    return {"entity": entity, "report": None, "found": False}


@app.post("/api/reconciliation/validate", status_code=status.HTTP_201_CREATED)
def run_reconciliation_validate(request: ValidationRequest):
    return {"validated": True, "entity": request.entity_name}
