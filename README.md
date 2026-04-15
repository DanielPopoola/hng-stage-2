# HNG Stage 1 — Profile Inference API

A FastAPI service that accepts a name, enriches it with gender, age, and nationality data from three external APIs, and persists the result.

## Features

- Concurrent external API calls (Genderize, Agify, Nationalize)
- Age group classification
- Idempotent profile creation
- SQLite persistence
- UUID v7 identifiers
- Dockerized

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api.py
│   ├── models.py
│   ├── service.py
│   ├── clients.py
│   ├── database.py
│   └── config.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env
```

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker & Docker Compose (for containerized setup)

## Local Setup

**1. Clone the repository**

```bash
git clone https://github.com/DanielPopoola/hng-stage-1
cd hng-stage-1
```

**2. Install dependencies**

```bash
uv sync
```

**3. Create a `.env` file**

```env
DATABASE_URL=sqlite:///./hng.db
GENDERIZE_BASE_URL=https://api.genderize.io
AGIFY_BASE_URL=https://api.agify.io
NATIONALIZE_BASE_URL=https://api.nationalize.io
```

**4. Run the server**

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Docker Setup

**1. Create a `.env` file**

```env
DATABASE_URL=sqlite:////app/hng.db
GENDERIZE_BASE_URL=https://api.genderize.io
AGIFY_BASE_URL=https://api.agify.io
NATIONALIZE_BASE_URL=https://api.nationalize.io
```

**2. Build and run**

```bash
docker compose up --build
```

## API Reference

### `POST /api/profiles`

Accepts a name, fetches enriched profile data, and stores the result.

**Request body**

```json
{ "name": "ella" }
```

**Success response (201 — new profile)**

```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "DRC",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

**Existing profile response (200)**

```json
{
  "status": "success",
  "message": "Profile already exists",
  "data": { "...existing profile..." }
}
```

---

### `GET /api/profiles`

Returns all profiles. Supports optional case-insensitive query filters.

**Query parameters**

| Parameter | Type | Example |
|-----------|------|---------|
| `gender` | string | `?gender=male` |
| `country_id` | string | `?country_id=NG` |
| `age_group` | string | `?age_group=adult` |

**Success response (200)**

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": "id-1",
      "name": "emmanuel",
      "gender": "male",
      "age": 25,
      "age_group": "adult",
      "country_id": "NG"
    },
    {
      "id": "id-2",
      "name": "sarah",
      "gender": "female",
      "age": 28,
      "age_group": "adult",
      "country_id": "US"
    }
  ]
}
```

---

### `GET /api/profiles/{id}`

Returns a single profile by UUID.

**Success response (200)**

```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "emmanuel",
    "gender": "male",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 25,
    "age_group": "adult",
    "country_id": "NG",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

---

### `DELETE /api/profiles/{id}`

Deletes a profile by UUID. Returns `204 No Content` on success.

---

## Error Responses

All errors follow this structure:

```json
{ "status": "error", "message": "<error message>" }
```

| Status Code | Reason |
|-------------|--------|
| 400 | Missing or empty `name` |
| 422 | `name` is not a string |
| 404 | Profile not found |
| 502 | External API returned unusable data |
| 500 | Unexpected server error |

---

## Age Group Classification

| Age Range | Group |
|-----------|-------|
| 0 – 12 | child |
| 13 – 19 | teenager |
| 20 – 59 | adult |
| 60+ | senior |