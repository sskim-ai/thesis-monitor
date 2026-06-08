# Architecture

Thesis Monitor is organized around a simple flow:

1. A user or Custom GPT calls the FastAPI server with a ticker.
2. Provider classes collect raw source events.
3. The classifier maps raw events into normalized `event_type` values.
4. The scoring service applies rule-based thesis relevance scoring.
5. API routes return JSON with facts, implications, and unknowns separated.

## Layers

- `app/api`: FastAPI route definitions.
- `app/models`: SQLModel database tables.
- `app/schemas`: Pydantic API request and response models.
- `app/providers`: Data provider interfaces and mock implementations.
- `app/services`: Business logic for collection, classification, scoring, and watchlists.
- `app/jobs`: Scheduled collection entry points.
- `app/utils`: Shared helpers.

## Database

The default database is SQLite through SQLModel and SQLAlchemy. The database URL is configured through `DATABASE_URL`, so PostgreSQL can be introduced later by changing the URL and adding a PostgreSQL driver dependency.

## Fact Discipline

Events deliberately separate:

- `confirmed_facts`: directly supported by the source.
- `inferred_implications`: analytical implications that may matter to the thesis.
- `unknowns`: important missing data.

Confirmed facts should never include unsupported inference.

## Scoring

The initial version uses rule-based scoring only. It does not call an LLM. Events with `relevance_score >= 40` set `requires_review=true`.

