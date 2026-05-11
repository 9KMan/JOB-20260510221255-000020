"""
FastAPI REST endpoints for EHR migration platform.
"""

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ccl_scripts import get_library, SchemaCategory, CCLScript, ExecutionStatus
from etl_pipeline import EntityType, PipelineStatus
from etl_pipeline.orchestrator import Orchestrator, PipelineJob
from reconciliation import ReconciliationEngine, ReconciliationStatus

app = FastAPI(title="EHR Migration API", version="1.0.0")

_library = get_library()
_orchestrator = Orchestrator()
_reconciliation_engine = ReconciliationEngine()


class CCLScriptRequest(BaseModel):
    name: str
    category: str
    description: str
    content: str
    schema_area: str


class ETLExtractionRequest(BaseModel):
    entity: str
    export_format: str = "CSV"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ReconciliationValidateRequest(BaseModel):
    entity_name: str
    source_data: list[dict]
    target_data: list[dict]
    key_columns: list[str]
    required_columns: list[str]


@app.get("/")
def root():
    return {"message": "EHR Migration API", "version": "1.0.0"}


@app.post("/api/ccel/run")
def run_ccl_script(script_name: str, params: Optional[dict] = None, dry_run: bool = True):
    result = _library.execute_script(script_name, params, dry_run)
    return result.to_dict()


@app.post("/api/etl/extract")
def trigger_extraction(entity: str, export_format: str = "CSV", start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        entity_type = EntityType(entity)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown entity: {entity}")

    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    job = _orchestrator.trigger_extraction(entity_type, export_format, start_dt, end_dt)
    return job.to_dict()


@app.get("/api/etl/status/{job_id}")
def get_etl_status(job_id: str):
    job = _orchestrator.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job.to_dict()


@app.get("/api/reconciliation/{entity}")
def get_reconciliation_report(entity: str):
    result = _reconciliation_engine.get_result(entity)
    if not result:
        raise HTTPException(status_code=404, detail=f"No reconciliation result for: {entity}")
    return result.to_dict()


@app.post("/api/reconciliation/validate")
def validate_reconciliation(request: ReconciliationValidateRequest):
    result = _reconciliation_engine.run_full_reconciliation(
        request.entity_name,
        request.source_data,
        request.target_data,
        request.key_columns,
        request.required_columns,
    )
    return result.to_dict()


@app.get("/api/ccel/scripts")
def list_scripts(category: Optional[str] = None):
    cat = SchemaCategory(category) if category else None
    return _library.list_scripts(cat)


@app.post("/api/ccel/scripts")
def register_script(script: CCLScriptRequest):
    cat = SchemaCategory(script.category)
    new_script = CCLScript(
        name=script.name,
        category=cat,
        description=script.description,
        content=script.content,
        schema_area=script.schema_area,
    )
    _library.register_script(new_script)
    return {"message": "Script registered", "name": new_script.name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)