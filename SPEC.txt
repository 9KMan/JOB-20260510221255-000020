# Cerner Millennium CCL and Data Transformation Lead — EHR Migration Platform

## 1. Project Overview

**Client:** NHRG, Inc. (for HHSC — Health and Human Services Commission)
**Goal:** EHR migration tooling — CCL script development, data extraction from Cerner Millennium Oracle schemas, ETL pipeline for legacy system retirement
**Core Function:** Build a Cerner CCL script library + Python-based data transformation platform for HHSC Electronic Health Record migration initiatives

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EHR Migration Architecture                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │  Cerner        │    │  CCL Script     │    │  Python ETL Platform    │  │
│  │  Millennium    │───▶│  Development    │───▶│  (Data Extraction,      │  │
│  │  Oracle Schema │    │  (HL7, Fin, CDO)│    │   Validation, Export)   │  │
│  └─────────────────┘    └─────────────────┘    └───────────┬─────────────┘  │
│                                                              │                │
│                                                              ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Output Deliverables                                  │ │
│  │  • CCL Scripts (production-ready)    • Flat file extracts               │ │
│  │  • Data validation reports           • ETL job schedules                │ │
│  │  • Data lineage documentation        • Migration status dashboards     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. Connect to Cerner Millennium Oracle schemas (PSD, CDO, HSD, ARK)
2. Analyze clinical workflows (inpatient, outpatient, ancillary)
3. Write CCL scripts to extract data per clinical requirements
4. Python ETL pipeline: validate → transform → export
5. Generate data reconciliation reports
6. Support legacy system retirement tracking

## 3. Core Workstreams

### Workstream 1 — Cerner CCL Script Library
- Framework for writing, testing, and version-controlling CCL scripts
- Test harness: unit test CCL procedures against sandbox
- Performance profiling: identify and resolve CCL bottlenecks
- Production script templates for common data extracts

### Workstream 2 — Python ETL Pipeline
- Oracle connection via cx_Oracle or oracledb
- Incremental extraction with watermark tracking (no full re-loads)
- Data validation: schema checks, referential integrity, clinical rules
- Export formats: CSV, HL7 v2, FHIR (R4), flat file per HHSC spec
- Error handling with retry queues and alerting

### Workstream 3 — Data Reconciliation Engine
- Source-to-target comparison (Cerner Millennium → downstream systems)
- Row counts, checksum validation, null/duplicate detection
- Daily/weekly reconciliation reports (PDF + CSV)
- Data quality scorecard per entity type

### Workstream 4 — Production Operations
- Batch job scheduling (cron + Python APScheduler)
- Production/non-production environment parity testing
- CCL script performance monitoring (execution time, I/O)
- REST API for script invocation and job status

## 4. Data Model

### Cerner Millennium Schema Areas (key tables)
| Schema | Tables | Purpose |
|--------|--------|---------|
| PSD | ORDER_PROC, SPECIMEN, RESPIRATORY | Orders, results |
| CDO | CLARITY_SER, CLARITY_DEP, CLARITY_EMP | Organizational hierarchy |
| HSD | ORDER_REC, ORDER_MISC, PATIENT_VISIT | Visit and encounter data |
| ARK | PATIENT, PATIENT_ALLERGY, PATIENT_DIAGNOSIS | Patient demographics |
| FIN | ACCOUNT, PB_AR, GB_PAYMENT | Billing and accounts |

### ETL Watermark Table
| Column | Type | Notes |
|--------|------|-------|
| entity_name | VARCHAR(100) | e.g., 'ORDER_PROC' |
| last_extract_ts | TIMESTAMP | Watermark per entity |
| rows_extracted | INT | Count per run |
| status | VARCHAR(20) | success/failed/running |

## 5. API Design

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ccel/run` | Execute CCL script, return results |
| POST | `/api/etl/extract` | Trigger data extraction job |
| GET | `/api/etl/status/{job_id}` | Check ETL job status |
| GET | `/api/reconciliation/{entity}` | Get reconciliation report |
| POST | `/api/reconciliation/validate` | Run validation against target |
| GET | `/api/ccel/scripts` | List CCL scripts with metadata |
| POST | `/api/ccel/scripts` | Register new CCL script |

## 6. Technical Decisions

1. **cx_Oracle + SQLAlchemy for Oracle** — battle-tested Python Oracle driver; SQLAlchemy for schema reflection and ORM layer
2. **CCL embedded in Python** — subprocess call to `cclpy` or direct Oracle passthrough; CCL scripts as `.ccl` files in version control
3. **Incremental CDC via watermarks** — no full re-extract; timestamp-based change detection on key tables
4. **FHIR R4 for downstream export** — FHIR resources (Patient, Encounter, Observation) for modern system integration
5. **Apache Airflow for orchestration** — DAGs for ETL schedule, monitoring, and alerting
6. **dbt for data transformation** — dbt models for complex CCL-derived data; testing and documentation built in

## 7. Out of Scope

- Direct Cerner Millennium administration (no access to Millennium admin console)
- Real-time clinical decision support
- FHIR server hosting
- Multi-tenant SaaS architecture

## 8. Success Metrics

- CCL script execution time < 30 seconds for typical extract queries
- Data reconciliation: 100% row count match between source and target
- ETL pipeline: zero data loss on incremental runs
- All CCL scripts have unit test coverage and execution logs
- FHIR export validated against HL7 conformance tests