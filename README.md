# HNG Stage 2 — Intelligence Query Engine

A FastAPI service that stores demographic profile data and exposes a queryable
intelligence engine with advanced filtering, sorting, pagination, and natural
language search.

## Features

- Advanced filtering by gender, age, age group, country, and probability scores
- Sorting by age, created date, or gender probability
- Pagination with configurable page size
- Natural language query parsing (rule-based, no LLMs)
- Idempotent database seeding from JSON
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
│   ├── parser.py
│   ├── clients.py
│   ├── database.py
│   ├── seed.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_parser.py
│   └── test_profiles.py
├── seed_profiles.json
├── TRADEOFFS.md
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
git clone https://github.com/DanielPopoola/hng-stage-2
cd hng-stage-2
```

**2. Install dependencies**

```bash
uv sync
```

**3. Create a `.env` file**

```env
DATABASE_URL=sqlite:///./hng.db
```

**4. Seed the database**

```bash
uv run python -m app.seed
```

**5. Run the server**

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Docker Setup

**1. Create a `.env` file**

```env
DATABASE_URL=sqlite:////app/hng.db
```

**2. Build and run**

```bash
docker compose up --build
```

**3. Seed the database inside the container**

```bash
docker compose exec api uv run python -m app.seed
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## API Reference

### `GET /api/profiles`

Returns profiles with optional filtering, sorting, and pagination.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `gender` | string | `male` or `female` |
| `age_group` | string | `child`, `teenager`, `adult`, `senior` |
| `country_id` | string | ISO 2-letter code e.g. `NG` |
| `min_age` | int | Minimum age inclusive |
| `max_age` | int | Maximum age inclusive |
| `min_gender_probability` | float | Minimum gender confidence score |
| `min_country_probability` | float | Minimum country confidence score |
| `sort_by` | string | `age`, `created_at`, `gender_probability` |
| `order` | string | `asc` or `desc` |
| `page` | int | Page number, default `1` |
| `limit` | int | Results per page, default `10`, max `50` |

**Example**

```
GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc
```

**Success response (200)**

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 120,
  "data": [
    {
      "id": "01900000-0000-7000-8000-000000000001",
      "name": "Kwame Mensah",
      "gender": "male",
      "age": 25,
      "age_group": "adult",
      "country_id": "NG"
    }
  ]
}
```

---

### `GET /api/profiles/search`

Accepts a plain English query and converts it into filters.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `q` | string | Natural language query |
| `page` | int | Page number, default `1` |
| `limit` | int | Results per page, default `10`, max `50` |

**Example queries**

| Query | Interpreted as |
|---|---|
| `young males from nigeria` | gender=male, min_age=16, max_age=24, country_id=NG |
| `females above 30` | gender=female, min_age=30 |
| `people from angola` | country_id=AO |
| `adult males from kenya` | gender=male, age_group=adult, country_id=KE |
| `male and female teenagers above 17` | age_group=teenager, min_age=17 |

**Example**

```
GET /api/profiles/search?q=young males from nigeria&page=1&limit=10
```

**Success response (200)**

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 45,
  "data": [...]
}
```

**Uninterpretable query (422)**

```json
{ "status": "error", "message": "Unable to interpret query" }
```

---

### `GET /api/profiles/{id}`

Returns a single profile by UUID.

**Success response (200)**

```json
{
  "status": "success",
  "data": {
    "id": "01900000-0000-7000-8000-000000000001",
    "name": "Kwame Mensah",
    "gender": "male",
    "gender_probability": 0.95,
    "age": 25,
    "age_group": "adult",
    "country_id": "NG",
    "country_name": "Nigeria",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

---

### `POST /api/profiles`

Accepts a name, fetches enriched profile data from external APIs, and stores it.

**Request body**

```json
{ "name": "ella" }
```

**Success response (201)**

```json
{
  "status": "success",
  "data": { "...profile..." }
}
```

---

### `DELETE /api/profiles/{id}`

Deletes a profile by UUID. Returns `204 No Content` on success.

---

## Natural Language Parsing

The search endpoint uses rule-based parsing — no AI or LLMs involved. Queries
are tokenized and matched against lookup tables for gender, age groups, age
range signals, and country names. Multi-word countries like "south africa" are
matched as bigrams.

Supported signals:

- **Gender:** male, males, men, man, female, females, women, woman
- **Age groups:** child, teenager, adult, senior (and plurals)
- **Special age:** "young" maps to ages 16–24
- **Range signals:** above/over/older + number, below/under/younger + number
- **Countries:** all 63 countries present in the dataset by full name

## Error Responses

All errors follow this structure:

```json
{ "status": "error", "message": "<error message>" }
```

| Status Code | Reason |
|---|---|
| 400 | Missing or empty parameter |
| 422 | Invalid parameter type or uninterpretable query |
| 404 | Profile not found |
| 502 | External API failure |
| 500 | Unexpected server error |

## Age Group Classification

| Age Range | Group |
|---|---|
| 0 – 12 | child |
| 13 – 19 | teenager |
| 20 – 59 | adult |
| 60+ | senior |