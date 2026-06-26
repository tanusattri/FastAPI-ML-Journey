# System Architecture & Design Specification

This document provides a comprehensive overview of the architectural framework, data pipeline, and system design paradigms implemented in the **FastAPI Machine Learning Journey** application.

---

## Technical Stack Overview

| Component | Technology | Role |
| :--- | :--- | :--- |
| **API Framework** | FastAPI (Python) | High-performance, asynchronous REST API gateway. |
| **Data Validation** | Pydantic v2 | Type safety, data parsing, and runtime input constraints. |
| **Data Storage** | Flat-file Document Store (`patients.json`) | Lightweight local JSON persistence layer. |
| **Hosting Platform** | Render | Automated cloud hosting with native container builds. |
| **CI/CD Engine** | GitHub Webhooks | Immediate, zero-downtime deployment triggering on `main` push. |

---

## Core Architectural Layers

The application is structured around a classic **Three-Tier Architecture** condensed into a high-performance, lightweight microservices paradigm:

### 1. Request/Response Layer (The Gateway)
The entry point of the application managed via FastAPI decorators (`@app.get`, `@app.post`, `@app.put`, `@app.delete`). This layer handles:
* Dynamic path routing and extraction of Path/Query parameters.
* Generating semantic HTTP Response codes (`201 Created` for insertions, `200 OK` for alterations, `404 Not Found` for missing assets).

### 2. Domain Validation & Business Logic Layer
Driven entirely by Pydantic models. This layer acts as a strict structural firewall:
* **Ingestion Guard:** Enforces strict field typing (`int`, `float`, `str`) and value boundaries (`gt=0`, `lt=120`) before any execution code runs.
* **Feature Engineering Pipeline:** Dynamically generates calculated health metrics (`bmi` and `verdict`) at serialization runtime using `@computed_field` and Python properties.
* **Partial Updates Logic:** Leverages a `PatientUpdate` schema combined with `.model_dump(exclude_unset=True)` to execute granular, partial dictionary patches without accidental state regression.

### 3. Data Access Layer (Persistence)
A file-system abstraction layer utilizing native Python I/O primitives:
* **`load_data()`**: Opens and deserializes the JSON document store into runtime memory state (Python `dict`).
* **`save_data()`**: Marshals runtime memory modifications back into formatted JSON and safely flushes it back to the disk block.

---

## End-to-End Data Flow Diagrams

### Data Ingestion Pipeline (POST `/create`)
[ Client Request ]
│  (Payload: JSON Document)
▼
┌────────────────────────────────┐
│   Pydantic Schema Validation   │ ──(Invalid Matrix)──► [ 422 Unprocessable Entity ]
└────────────────────────────────┘
│  (Validated Payload)
▼
┌────────────────────────────────┐
│     File Ingestion (Read)      │ <─── [ patients.json File Store ]
└────────────────────────────────┘
│
▼
┌────────────────────────────────┐
│     Primary Key Check          │ ──(ID Already Exists)─► [ 400 Bad Request ]
└────────────────────────────────┘
│  (Unique Entry Confirmed)
▼
┌────────────────────────────────┐
│    Disk Write & Persistence    │ ───► [ patients.json File Store ]
└────────────────────────────────┘
│
▼
[ 201 Created JSONResponse ]

### State Modification Pipeline (PUT `/edit/{patient_id}`)
[ Client Request ]
│  (Payload: Optional JSON Fields + Path Parameter)
▼
┌────────────────────────────────┐
│  Verify Resource Existence     │ ──(ID Absent)─────────► [ 404 Not Found ]
└────────────────────────────────┘
│  (Target Dictionary Located)
▼
┌────────────────────────────────┐
│ exclude_unset=True Filtering │ ───► Extracted only user-modified properties
└────────────────────────────────┘
│
▼
┌────────────────────────────────┐
│   Pydantic Object Re-assembly  │ ───► Unpacks combined data to trigger
└────────────────────────────────┘      @computed_field (Recalculates BMI/Verdict)
│
▼
┌────────────────────────────────┐
│    Disk Update & Serialization │ ───► Overwrites JSON Block safely
└────────────────────────────────┘
│
▼
[ 200 OK JSONResponse ]

---

## CI/CD Infrastructure Workflow

The architecture transitions from local testing to global availability through a modern DevOps git-ops pipeline:

1. **Local Working Tree:** Development and edge-case code evaluation run smoothly locally.
2. **Git Commit System:** Local modifications are staged, wrapped in isolated commits, and securely synced to GitHub.
3. **Webhook Subscriptions:** GitHub triggers an automated outbound webhook to the Render hosting stack.
4. **Isolated Virtual Environment Build:** Render boots up an independent builder instance, reads the python metadata