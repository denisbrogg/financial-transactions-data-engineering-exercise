# Architecture

The overall setup is intentionally simple: a source file is loaded into a landing zone, transformed through a medallion pipeline, and then exposed through a small reporting layer.

```mermaid
flowchart LR
    A[Datasource] --> B[Landing Zone]
    B --> C[Bronze]
    C --> D[Silver]
    D --> E[Gold]
    E --> F[DuckDB Storage]
    F --> G[Dashboard / Reporting]
    G --> H[Business Questions]

    subgraph Pipeline[Pipeline Layer]
        B
        C
        D
        E
        F
    end

    classDef source fill:#e8f0fe,stroke:#1a73e8,color:#111827;
    classDef layer fill:#e6f4ea,stroke:#188038,color:#111827;
    classDef output fill:#fff4e5,stroke:#b26a00,color:#111827;

    class A source;
    class B,C,D,E,F layer;
    class G,H output;
```

## Zoom: pipeline component

```mermaid
flowchart TB
    S[Source data] --> LZ[Landing Zone]
    LZ --> BR[Bronze: raw ingestion]
    BR --> SI[Silver: cleaning + normalization]
    SI --> GO[Gold: analytics-ready tables]
    GO --> DB[DuckDB storage]
    DB --> DASH[Dashboard]

    subgraph Medallion[Medallion Architecture]
        LZ
        BR
        SI
        GO
        DB
    end
```

## Why this shape

The design follows a common warehouse pattern because it separates concerns in a useful way:

- the landing zone is a raw capture area
- bronze keeps the ingest footprint simple
- silver focuses on data quality and consistency
- gold prepares the tables for analytics and quick review

This makes the system easier to reason about when the project grows, and it also gives a clean place to add extra sources or transformations without turning everything into one huge pipeline.

## Data flow

The pipeline is built around a small, repeatable sequence:

1. source file is fetched into the landing zone
2. the bronze ingestor materializes the raw records into DuckDB
3. silver cleaners and standardizers prepare the data for use
4. gold loaders build dimension and fact tables
5. the dashboard reads the resulting analytical tables

That layering matters because the data quality decisions happen in a controlled place, instead of being mixed into the storage and reporting layers.

## Operational notes

This is a lightweight architecture designed for a personal or small-team environment. It is intentionally readable and easy to extend, but it is not a fully productionized warehouse stack. In a larger setup, I would add externalized configuration, schema governance, stronger data quality checks, and more formal monitoring around the medallion layers.
