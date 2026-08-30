# Docs

This folder is meant to hold the project context that does not belong in the code itself: architecture notes, trade-offs, and the design thinking behind the ETL structure.

The important idea is that the repo remains readable without burying the story in code comments. The docs here are a companion to the implementation rather than a formal deliverable detached from it.

## Included documents

- [architecture.md](architecture.md): conceptual system view and medallion pipeline overview
- [code-structure.md](code-structure.md): clean-code architecture view of the pipeline logic layer

## How to use this folder

When you are looking at the data flow, start with the architecture notes. If you want to understand why the logic is split into controllers, adapters, and strategy-like transformations, jump to the code structure document.
