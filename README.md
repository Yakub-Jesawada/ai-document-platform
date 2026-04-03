# AI Document Processing Platform

An event-driven, scalable backend platform for ingesting, processing, and intelligently querying large collections of documents. Built with a Kafka-based async pipeline, OCR via AWS Textract, pgvector-powered semantic search, and an MCP-based AI agent layer.

---

## Overview

This platform accepts document uploads (PDFs, scanned images, etc.), routes them through a multi-stage processing pipeline, and surfaces structured intelligence through a REST API. The pipeline is fully decoupled — each stage publishes an event, and the next stage consumes it independently.

```
Upload → [Kafka] → OCR Worker → [Kafka] → Chunk Worker → [Kafka] → Embedding Worker
                                                                          ↓
                                                                    pgvector (semantic search)
```

Documents can be queried individually or across collections, with support for semantic similarity search over embedded chunks.

---

## Architecture

### Services

| Service | Role |
|---|---|
| `document_api` | FastAPI REST service — handles uploads, auth, collections, and search |
| `ocr_worker` | Consumes upload events, runs AWS Textract, publishes extracted text |
| `chunk_worker` | Consumes OCR events, splits text into logical chunks, persists to DB |
| `embedding_worker` | Consumes chunk events, generates vector embeddings, stores in pgvector |
| `shared` | Internal library — Kafka client, event schemas, embedding provider |

### Infrastructure

| Component | Purpose |
|---|---|
| PostgreSQL + pgvector | Structured storage and vector similarity search |
| Kafka | Async event bus decoupling all pipeline stages |
| AWS S3 | Raw document storage |
| AWS Textract | Managed OCR for PDFs and images |
| Docker Compose | Local orchestration of all services |

---

## Processing Pipeline

Each stage in the pipeline is triggered by a Kafka event and publishes the next:

```
document_uploaded  →  ocr_worker  →  document_textracted
                                              ↓
                                       chunk_worker  →  document_chunked
                                                               ↓
                                                      embedding_worker  →  [done]
```

**Document lifecycle states:**

```
uploaded → ocr_processing → ocr_done → chunking → chunk_done → embedding → embedding_done
                                                                                   ↓
                                                                             (or *_failed)
```

Failures at any stage are caught, logged, and the document status is marked accordingly — no silent failures.

---

## API Reference

All routes require JWT authentication unless noted.

### Auth

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Obtain a JWT token |

### Documents

| Method | Path | Description |
|---|---|---|
| `POST` | `/documents/` | Upload one or more documents |
| `GET` | `/documents/` | List all documents for the current user |
| `GET` | `/documents/{uuid}` | Get document detail and status |
| `DELETE` | `/documents/{uuid}` | Delete document (removes from S3 + DB) |
| `POST` | `/documents/{uuid}/ocr` | Re-trigger OCR for a document |
| `POST` | `/documents/{uuid}/chunk` | Re-trigger chunking (skips OCR) |
| `POST` | `/documents/{uuid}/embed` | Re-trigger embedding (skips OCR + chunking) |
| `POST` | `/documents/embedded_search` | Semantic similarity search over embedded chunks |

### Collections

| Method | Path | Description |
|---|---|---|
| `POST` | `/collections/` | Create a named collection |
| `GET` | `/collections/` | List collections |
| `GET` | `/collections/{uuid}` | Get collection with linked documents |
| `DELETE` | `/collections/{uuid}` | Delete a collection |

Documents uploaded without a target collection are automatically placed in a `default_collection`.

### Semantic Search

`POST /documents/embedded_search` accepts:

```json
{
  "query": "what were the key findings?",
  "top_k": 5,
  "collection_uuid": "<optional>",
  "document_uuid": "<optional>"
}
```

Returns the top-K most similar text chunks with cosine distance scores, scoped to the authenticated user's data.

---

## Tech Stack

- **API:** FastAPI, Pydantic v2, SQLModel
- **Database:** PostgreSQL 16 + pgvector extension, Alembic migrations
- **Messaging:** Kafka via `aiokafka`
- **Storage:** AWS S3 (boto3)
- **OCR:** AWS Textract
- **Auth:** JWT (python-jose), bcrypt
- **Containerisation:** Docker, Docker Compose

---

## Project Structure

```
.
├── alembic/                    # DB migration scripts
├── docker-compose.yaml         # Local infra (Postgres + pgvector)
├── services/
│   ├── document_api/           # FastAPI REST service
│   │   └── app/
│   │       ├── routes/         # Auth, users, documents, collections
│   │       ├── models/         # SQLModel ORM models
│   │       ├── schemas/        # Pydantic request/response schemas
│   │       ├── kafka/          # Kafka event publishers
│   │       └── core/           # Embedding provider integration
│   ├── workers/
│   │   ├── ocr_worker/         # AWS Textract extraction
│   │   ├── chunk_worker/       # Text chunking + persistence
│   │   └── embedding_worker/   # Vector embedding generation
│   ├── shared/                 # Internal shared library
│   │   ├── events/             # Typed Kafka event schemas
│   │   ├── embeddings/         # Embedding provider abstraction
│   │   └── kafka/              # Shared Kafka producer/consumer client
│   └── infra/                  # Docker Compose for supporting services
└── ROADMAP.md                  # Engineering phase plan
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- AWS credentials (for S3 and Textract)
- Kafka (can be run via Docker)

### Local Setup

**1. Start infrastructure**

```bash
docker compose up -d
```

This starts PostgreSQL with the pgvector extension.

**2. Configure environment variables**

Create `.env` files in each service directory. Key variables:

```env
# document_api
DATABASE_URL=postgresql+asyncpg://ai_docs_user:ai_docs_pass@localhost:5434/ai_docs
SECRET_KEY=your-secret-key
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=...
S3_BUCKET_NAME=...
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
BASE_FILE_PATH=/tmp/uploads
```

**3. Run DB migrations**

```bash
cd alembic
alembic upgrade head
```

**4. Start the API**

```bash
cd services/document_api
pip install -e .
uvicorn app.main:app --reload --port 8000
```

**5. Start workers** (each in a separate terminal)

```bash
cd services/workers
python -m ocr_worker.main
python -m chunk_worker.main
python -m embedding_worker.main
```

**6. Access the API docs**

```
http://localhost:8000/docs
```

---

## Roadmap

The platform is being built in phases:

| Phase | Description | Status |
|---|---|---|
| 0 | Foundations & project setup | Done |
| 1 | Document upload API + DB schema | Done |
| 2 | Kafka async pipeline | Done |
| 3 | OCR + text extraction | Done |
| 4 | Chunking + pgvector semantic search | Done |
| 5 | Entity extraction pipeline | Done |
| 6 | MCP-based AI agent | In Progress |
| 7 | Collection-level multi-document reasoning | Upcoming |
| 8 | Redis caching + performance | Upcoming |
| 9 | Production infrastructure | Upcoming |
| 10 | Hardening + reliability | Upcoming |

See [ROADMAP.md](ROADMAP.md) for full engineering detail per phase.

---

## Design Decisions

**Why event-driven?**
OCR and embedding are slow, blocking operations. Kafka decouples ingestion from processing so the API stays fast and each worker scales independently.

**Why pgvector?**
Keeps vector search co-located with relational data — no external vector DB to manage. pgvector's cosine distance support is sufficient for semantic chunk retrieval at this scale.

**Why per-stage re-trigger endpoints?**
`/ocr`, `/chunk`, `/embed` endpoints allow re-processing a document from any stage without re-uploading. Useful during development and for targeted failure recovery.

**Why a shared library?**
`services/shared` holds Kafka client code, typed event schemas, and the embedding provider abstraction. Workers and the API import from it to avoid drift between producers and consumers.
