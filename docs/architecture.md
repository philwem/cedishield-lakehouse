# CediShield Architecture

## Overview
CediShield is an evolving lakehouse-style project exploring mining and macro-financial analysis. Its current direction is to combine public financial disclosures, market data, and macroeconomic indicators in a layered workflow. The architecture is provisional and can adapt as project requirements and implementation change.

## Architectural layers

### 1. Source layer
The intended source layer may acquire data from external APIs such as:

- SEC EDGAR for company financial facts
- Alpha Vantage for daily equity prices
- World Bank for macroeconomic time-series indicators (planned; not yet integrated)

### 2. Ingestion and normalization layer
Python scripts are intended to process raw API payloads and reshape them into tabular structures suitable for analytics. The current reference implementation is in [scripts/ingest_lakehouse.py](../scripts/ingest_lakehouse.py), which fetches SEC company facts and returns a pandas DataFrame.

The same script fetches raw daily equity OHLCV data from Alpha Vantage's standard daily endpoint. The free compact response is limited to the latest 100 observations; full history is a Premium feature. Market data retrieval requires `ALPHA_VANTAGE_API_KEY` and spaces sequential requests to reduce request bursts.

Key responsibilities:

- validate and format CIK identifiers
- request and parse SEC JSON responses
- filter to relevant reporting forms such as 10-K and 10-Q
- flatten nested XBRL facts into row-based fact tables
- prepare data for downstream storage and analysis; DuckDB loading is not yet implemented by the current SEC script

### 3. Storage layer
DuckDB is the intended embedded analytical database and lakehouse storage layer. The current ingestion script does not yet persist its results to DuckDB.

### 4. Transformation layer
The dbt project scaffold under [dbt_cedishield](../dbt_cedishield) is intended to provide versioned transformations for staging and mart models. This layer may evolve and, when implemented, is expected to:

- standardize naming and data types
- create reusable dimensions and facts
- enforce logical relationships
- add tests and data-quality checks

### 5. Analytics and reporting layer
The future analytics layer may support exploration and decision-making across areas such as:

- mining-company financial health
- commodity sensitivity
- currency and macro exposures
- broader operational risk characterization

## Intended data flow
```text
SEC / Alpha Vantage / World Bank
            |
            v
Python ingestion scripts
            |
            v
Normalized tabular records
            |
            v
DuckDB lakehouse
            |
            v
dbt staging + marts
            |
            v
Analytical reporting and exploration
```

## Why this architecture fits the objective
The project is exploring a way to bring financial and external market data into one analytical foundation. Separating acquisition, standardization, and modeling provides a starting point that can remain understandable and testable as the architecture changes.

## Current implementation status
The repository currently includes SEC facts and Alpha Vantage daily equity-price ingestion that return pandas DataFrames, plus project scaffolding. Persistence to DuckDB, World Bank integration, implemented dbt models, and orchestration are not yet present as an end-to-end pipeline. These are possible future steps, not fixed commitments; update this document as the project’s scope and implementation evolve.
