# Code structure

The project is organized around a clean separation of responsibilities. The idea is that the orchestration layer should be replaceable without forcing the business logic to change when the runtime changes.

## Core pattern

The most important idea lives under `pipelines/src/pipelines/logic`.

- `controllers/` orchestrate a stage in the pipeline
- `abstractions/` define interfaces and contracts
- `impl/` contains the concrete implementations for connectors, ingestors, cleaners, normalizers, and loaders
- `models/` contains the domain data structures used by the pipeline

This model follows a clean architecture style: the code is built around interfaces and implementation details instead of hardcoding everything into a single monolith.

## Controller layer

The controller classes handle the lifecycle of each stage:

- `LandingZoneController` fetches raw source data into the landing area
- `BronzeController` ingests that raw file into the bronze tables
- `SilverController` applies cleaning, standardization, and deduplication steps
- `GoldController` creates the analytical tables and loads facts/dimensions

The controllers do not know about the full pipeline runtime. They simply orchestrate the relevant stage and delegate to the implementations behind abstract interfaces.

## Abstractions and implementations

The project separates interfaces from concrete behavior:

- a connector knows how to fetch a source
- an ingestor knows how to load raw data into bronze
- a cleaner fixes quality problems in the transaction data
- a normalizer standardizes values into consistent domains
- a loader turns curated records into gold tables

That boundary matters because it keeps the logic testable and makes a new source or a new stage easier to add without rewriting the core pipeline.

## Why this is scalable

If I wanted to add a new datasource, the pattern is straightforward:

1. create a new connector for the source
2. create the specific ingestor if the raw format differs
3. add new cleaners or normalizers if the semantics differ
4. add a new gold table loader if the reporting model needs another dimension or fact

The runtime remains the same. The orchestration contracts remain the same. That means the code can remain maintainable even as the source count grows.

## Why this matters for future runtime choices

The important architectural advantage is that the runtime layer is intentionally decoupled from the logic layer.

If I wanted to move away from Dagster and use a different orchestrator, the code under `logic/` would remain largely unchanged. I could swap the runtime entrypoints while keeping the same business logic and transformation design. The same goes for moving to a more service-oriented setup with FastAPI or another scheduler.

That is the real value of this structure: it isolates the data-engineering decisions from the execution framework.
