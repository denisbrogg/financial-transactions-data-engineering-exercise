# Financial Transactions ETL

This project is a small data-engineering exercise built around personal financial transaction data. The goal is simple: ingest a raw CSV, clean and standardize it, model it in a medallion-style warehouse, and then make the result easy to explore in a lightweight dashboard.

It is intentionally practical rather than overly academic: the pipeline is structured so it can be extended without fighting the orchestration layer, and the dashboard is there to surface the questions that matter in day-to-day portfolio review.

## What is in here

- `pipelines/` holds the ETL logic and Dagster orchestration
- `ui/` contains the Streamlit dashboard that reads from the DuckDB warehouse
- `data/` stores the source files and the generated database artifacts
- `docs/` is the working archive for architecture notes and technical decisions
- `docker/` includes the local container setup used for the project runtime

## Documentation

The most useful references are here:

- [docs/README.md](docs/README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/code-structure.md](docs/code-structure.md)
- [WRITEUP.md](WRITEUP.md)

## Local setup (devcontainer-friendly)

This repository is set up to work well inside the provided devcontainer. The expected flow is:

1. Open the project in the devcontainer.
2. From the repo root, sync the workspace dependencies:

```bash
uv sync --all-groups --all-packages
```

3. Activate the environment if needed, then run the relevant tooling from the package folders.

### Dagster pipeline

```bash
cd pipelines
uv run dg dev
```

This starts the Dagster dev server and exposes the pipeline in the browser.

### Dashboard

```bash
cd ui
uv run streamlit run src/ui/main.py --server.headless true --server.port 8502
```

The dashboard reads directly from the DuckDB database at `data/db/transactions.duckdb`.

## The idea behind the architecture

The pipeline follows a medallion pattern:

- Landing zone: raw source files as they arrive
- Bronze: minimally ingested raw data in the database
- Silver: cleaned, normalized, curated records
- Gold: analytical tables ready for reporting and dashboards

This keeps the logic modular: the runtime orchestrator can change without forcing the entire data model to change. If a new source is added, the project is designed so the new work lands in a dedicated connector and transformer path rather than by rewriting the whole stack.

## Notes

This is a working project, not a polished enterprise platform. It is a clean starting point for analyzing transaction flows, spotting anomalies, and exploring how a small data stack can be organized around maintainable business logic.
