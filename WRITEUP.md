# Write-up

This is a small personal ETL project for financial transaction analysis. The goal was to build a simple pipeline from raw CSV data to a useable analytical layer, then make it easy to explore in a dashboard.

## Missing

- The database is not containerized yet; it currently runs as a local DuckDB file.
- Currency normalization to CHF is still missing; exchange-rate data would be the next important addition.
- Outlier detection is still hardcoded and not yet a proper data-quality layer.
- Cleaning and normalization logic is still mostly explicit rule-based logic rather than a more general strategy setup.
- All the key pipeline settings are currently hardcoded in `assets.py`; I would move those into config files and environment variables using Hydra or a similar pattern.
- The side quests are intentionally exploratory; they can reveal both opportunities and inefficiencies in the system.
- Documentation is still lighter than I would want in a bigger setup.

The overall structure is still useful: the source data flows through a landing zone, bronze, silver, and gold layers, and the reporting layer reads from the final analytical tables. It is intentionally simple, modular, and easy to extend without tying the logic too tightly to the orchestration tool.
