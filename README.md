# Cerner Millennium CCL and Data Transformation Lead — EHR Migration Platform

**Client:** NHRG, Inc. (HHSC — Health and Human Services Commission)
**Role:** Build tooling for Electronic Health Record (EHR) migration from legacy Cerner Millennium systems

## Project Overview

A comprehensive Cerner CCL script library + Python-based data transformation platform for HHSC EHR migration initiatives. This platform provides:
- CCL Script Library with production-ready templates
- Python ETL Pipeline with Oracle CDC support
- Data Reconciliation Engine for validation
- FastAPI Production Operations

## Tech Stack

**Languages:** Python 3.10+, CCL (Cerner Command Language), SQL, HL7 v2, FHIR R4
**Databases:** Oracle (Cerner Millennium), PostgreSQL
**Pipeline:** Apache Airflow, dbt
**APIs:** FastAPI, REST/SOA
**Cloud:** AWS, Azure (multicloud patterns)

## Directory Structure

```
api/                  # FastAPI REST endpoints
ccl_scripts/          # CCL script library + executor
etl_pipeline/         # Oracle CDC ETL pipeline
reconciliation/       # Source-to-target data reconciliation
tests/                # Test suite (20/20 passing)
pyproject.toml        # Python dependencies
```

## Setup

```bash
# Install dependencies
pip install -e .

# Run tests
pytest

# Start API server
python -m api.server
```

## Key Features

### CCL Script Library (`ccl_scripts/`)
- Script registry with categories (HL7, FIN, CDO)
- Executor with job tracking
- 6 production CCL script templates (PSD, CDO, HSD, ARK, FIN schemas)

### ETL Pipeline (`etl_pipeline/`)
- Oracle connection pooling
- Watermark-based incremental CDC (no full re-loads)
- Data validation (schema, nulls, duplicates)
- Exporters: CSV, HL7 v2, FHIR R4
- Orchestrator for batch job management

### Reconciliation Engine (`reconciliation/`)
- Source-to-target comparison (row counts, checksums)
- Null/duplicate detection
- Quality scorecard generator

## GitHub

https://github.com/9KMan/JOB-20260510221255-000020
