# Tradeoffs & Design Decisions

## SQLite over PostgreSQL

The spec implies a production-grade database but the dataset is 2026 records.
SQLite handles millions of rows efficiently and eliminates operational complexity
(no separate DB service, no connection pooling, no driver differences).
Switch to PostgreSQL only if dataset size or concurrent write requirements grow.

## Bulk upsert over SELECT-then-INSERT for seeding

Seeding uses SQLite's INSERT OR IGNORE with all 2026 records in a single
statement rather than looping and checking existence per record. This reduces
2026 potential round trips to one, and correctness is guaranteed by the UNIQUE
constraint on name rather than application-level logic.

## Rule-based NLP over LLM-based parsing

The search endpoint parses plain English queries using tokenization and lookup
tables rather than an LLM or NLP library. For a closed, well-defined vocabulary
(63 countries, 4 age groups, 2 genders, a handful of signal words) this is O(n)
on query length, fully deterministic, requires no external dependency, and has
no latency overhead. An LLM would add cost, latency, and unpredictability for
no measurable gain on this input space.

## ProfileQuery Pydantic model for query parameter grouping

Instead of listing all 10 filter/sort/pagination parameters directly on the
endpoint function, they are grouped into a ProfileQuery Pydantic model and
injected via FastAPI's Query dependency. This keeps the endpoint signature
clean and makes the parameter contract explicit and reusable.

## Sync SQLAlchemy over async

The read-heavy query endpoints have no I/O concurrency benefit from async DB
calls since each request runs one or two sequential queries. Sync SQLAlchemy
is simpler, easier to test, and avoids the complexity of async session
management. The POST endpoint remains async only because it makes concurrent
external HTTP calls via httpx.

## Service layer returns dict over Pydantic model

get_profiles() returns a plain dict with page, limit, total, and data keys
rather than a typed response model. The API layer owns serialization via
ProfileListItem. This keeps the service layer free of HTTP concerns and
makes it straightforward to call from both the filter endpoint and the
search endpoint without duplicating serialization logic.