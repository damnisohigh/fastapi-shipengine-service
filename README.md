# FastAPI ShipEngine Service (Test Assignment)

Async microservice demo inspired by the ShipEngine API, implemented using **FastAPI**, **SQLAlchemy (asyncpg)**, **PostgreSQL**, and **ARQ (Redis)**.

The goal of this project is to demonstrate:

- Clean FastAPI application structure
- Async end-to-end request handling
- Transactional database operations
- Background processing with ARQ
- Batch-based API design (sync + async modes)

⚠️ This is a **test assignment**, not a full ShipEngine implementation.  

---

## 🧱 Tech Stack

- **Python 3.13**
- **FastAPI**
- **SQLAlchemy 2.x (async)**
- **PostgreSQL**
- **asyncpg**
- **Alembic**
- **Redis**
- **ARQ (async task queue)**
- **Docker / Docker Compose**

---

## 🗂 Project Structure (simplified)

```
src/
├── app/
│   ├── api/v1/endpoints/     # FastAPI route handlers
│   ├── services/             # Business logic layer
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic schemas
│   ├── crud/                 # DB helpers (where applicable)
│   ├── workers/              # ARQ worker + jobs
│   └── core/config.py        # Environment & settings
├── alembic/                  # Database migrations
└── main.py
```

---

## 🚀 How to Run

### 1️⃣ Environment

Create `.env` from sample:

```bash
cp .env.sample .env
```

Example `.env`:

```env
ENVIRONMENT=local

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_DB=shipengine

REDIS_URL=redis://redis:6379/0
SQL_ECHO=false
```

---

### 2️⃣ Run with Docker

```bash
docker compose up --build
```

#### What happens on startup:

- PostgreSQL & Redis containers start
- Alembic migrations are applied automatically
- FastAPI API starts on port `8000`
- ARQ worker starts in a separate container

---

## 📖 API Documentation

Swagger UI is available at:

```
http://localhost:8000/docs
```

No separate documentation is provided — all behavior is described below.

---

## ✨ Implemented Endpoints

### 1️⃣ Address Validation

Inspired by `POST /addresses/validate` from ShipEngine.

#### Endpoint

```
POST /v1/addresses/validate
```

#### Modes

**Sync mode (default)**  
Validates addresses immediately and stores results in the database.

**Async mode**  
Queues validation as a background job via ARQ.

```
POST /v1/addresses/validate?async=true
```

Returns:

- `202 Accepted`
- Empty body
- `X-Validation-Batch-Id` header

#### Poll results

```
GET /v1/addresses/validate/{batch_id}
```

#### Batch management

```
GET    /v1/validation-batches
GET    /v1/validation-batches/{batch_id}
POST   /v1/validation-batches/{batch_id}/requeue
DELETE /v1/validation-batches/{batch_id}
```

Each batch is transactional, idempotent, and safely re-runnable.

---

### 2️⃣ Address Recognition

Inspired by `PUT /addresses/recognize` from ShipEngine.

Demonstrates text → structured address recognition with async batch support.

#### Endpoint

```
PUT /v1/addresses/recognize
```

#### Async mode

```
PUT /v1/addresses/recognize?async=true
```

Returns:

- `202 Accepted`
- `X-Recognition-Id` header

#### Poll results

```
GET /v1/addresses/recognize/{recognition_id}
```

---

## 🔁 Async Processing (ARQ)

- Jobs are enqueued via Redis
- Worker processes jobs transactionally
- Batch status transitions:
  - queued
  - processing
  - completed
  - failed

---

## 🧪 Example Payloads

### Address Validation

```json
[
  {
    "name": "John Doe",
    "address_line1": "123 Main St",
    "city_locality": "New York",
    "state_province": "NY",
    "postal_code": "10001",
    "country_code": "US"
  }
]
```

### Address Recognition

```json
[
  {
    "text": "John Doe, 123 Main St, New York, NY 10001, US",
    "address": {
      "name": "John Doe",
      "address_line1": "123 Main St",
      "city_locality": "New York",
      "state_province": "NY",
      "postal_code": "10001",
      "country_code": "US"
    }
  }
]
```

---

## 🧠 Notes for Reviewer

- Test assignment, not a full ShipEngine clone
- Focus on architecture, async flow, transactional safety
- Tests intentionally minimal
- Fully runnable and extensible

---

## ✅ Summary

✔ Async FastAPI microservice  
✔ PostgreSQL + SQLAlchemy (async)  
✔ Background jobs via ARQ  
✔ Batch-based API design  
✔ Dockerized setup
