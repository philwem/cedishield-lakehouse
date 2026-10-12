# CediShield Lakehouse

An evolving lakehouse project exploring macro-financial analytics for mining and commodity risk, initially using Newmont Corporation as a reference case.

## Objective
CediShield explores how public company financial data, market pricing, and macroeconomic indicators can be brought together for mining and macro-financial analysis. The project’s scope, data sources, and analytical questions may evolve as the implementation and requirements develop.

The repository is structured around the following core question:

> How can a mining company’s financial position and risk profile be modeled using SEC filings, market data, and macroeconomic indicators in one reproducible pipeline?

## Why this project exists
Mining companies operate in a complex environment shaped by:

- commodity price volatility
- exchange-rate movements
- interest-rate and inflation trends
- production and cost structure changes
- public company financial disclosures

CediShield aims to bring these signals together into a data foundation for operational and financial analysis. The current implementation starts with SEC EDGAR facts for Newmont; this is an initial reference case, not a permanent limit on the companies, sources, or use cases the project may support.

## Current scope
The repository is at an early stage. SEC facts and Alpha Vantage daily equity prices can be fetched into pandas DataFrames. Macro data integration and the dbt transformation layer remain future work and may be refined as the project evolves.

### Data sources
1. SEC EDGAR API
   - Retrieves company facts from the SEC XBRL data service
   - Filters to major reporting forms such as 10-K and 10-Q
   - Flattens line-item facts into tabular records for analytics

2. Alpha Vantage
   - Fetches daily equity prices using the standard `TIME_SERIES_DAILY` endpoint
   - Uses raw (unadjusted) open, high, low, close, and volume values
   - The free `compact` response contains only the latest 100 daily observations; retrieving full history requires a Premium key
   - Requests are made sequentially with a 12-second pause between tickers; API errors and rate limits are reported without automatic retries
   - The standard daily endpoint is for equity symbols, not Yahoo-style futures symbols such as `GC=F`

3. World Bank API
   - A potential source of macroeconomic context such as GDP, inflation, and interest rate trends; integration is not yet implemented

## Technology stack
- Python for ingestion and transformation orchestration
- Pandas for tabular processing
- Requests for API access
- DuckDB as the lakehouse storage layer
- dbt for versioned transformation models
- Docker and VS Code dev containers for local reproducibility

## Repository layout
```text
cedishield-lakehouse/
├── .devcontainer/              # Dev container setup for local development
├── dags/                       # Airflow-style orchestration scaffolding
├── dbt_cedishield/             # dbt project and model directories
│   └── models/
│       ├── marts/
│       └── staging/
├── docs/                       # Architecture and project documentation
│   └── architecture.md
├── scripts/
│   └── ingest_lakehouse.py     # SEC ingestion script and data flattening logic
├── .env                        # Local environment variables
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Local service orchestration
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview and usage guidance
└── test_sec_api.py             # Simple SEC API validation script
```

## What the code currently does
The core ingestion script in [scripts/ingest_lakehouse.py](scripts/ingest_lakehouse.py) performs the following:

- builds the SEC company facts URL using a zero-padded CIK
- requests the EDGAR company facts JSON
- extracts the us-gaap facts payload
- filters for 10-K and 10-Q filings
- flattens nested observation records into a DataFrame
- returns a row-oriented table for downstream modeling

This is the first stage of the lakehouse pipeline and provides the input layer for dbt transformations and downstream analytical marts.

The same script also includes `fetch_market_prices`, which retrieves daily OHLCV equity observations from Alpha Vantage and returns them as a pandas DataFrame. Set `ALPHA_VANTAGE_API_KEY` in your local `.env` file or environment before running market ingestion.

## Intended data flow
1. Source APIs fetch raw financial, market, and macro data.
2. Python scripts normalize and flatten the payloads.
3. Data is loaded into DuckDB for lakehouse storage and exploration.
4. dbt models structure staging and analytic layers.
5. Analysts query curated models for operational and macro-financial insight.

This describes the target direction, not a fully working end-to-end pipeline today. At present, SEC facts and Alpha Vantage equity prices are returned as pandas DataFrames; the script does not yet write results to DuckDB or run dbt models.

## Development setup

### Using the VS Code Dev Container (recommended)
This repository is configured to run inside a VS Code Dev Container. When you see a prompt such as:

```text
root@<container-id>:/workspaces/cedishield-lakehouse#
```

you are in the container, not directly in your host machine's shell. `root` is the configured container user, and `/workspaces/cedishield-lakehouse` is the project directory mounted into the container.

Open the repository in VS Code and choose **Reopen in Container** (or **Dev Containers: Reopen in Container** from the Command Palette). The container is built from the [Dockerfile](Dockerfile), and the devcontainer's `postCreateCommand` installs `requirements.txt`. The configured default Python interpreter is `/usr/local/bin/python`, so a separate virtual environment is not required inside the container. Run the ingestion script from the project directory:

Running the script without options fetches market prices only, so SEC output does not obscure the market-price run:

```bash
python scripts/ingest_lakehouse.py
```

Choose a source explicitly when needed:

```bash
python scripts/ingest_lakehouse.py --source market
python scripts/ingest_lakehouse.py --source sec
python scripts/ingest_lakehouse.py --source both
```

### Running directly on your host (without the Dev Container)
If you intentionally run the project in your host's Python environment instead, create and activate a virtual environment there, then install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/ingest_lakehouse.py
```

The host virtual environment and the container's Python installation are separate environments. Installing packages in one does not install them in the other.

SEC requests (used by `--source sec` or `--source both`) require `SEC_CONTACT_EMAIL` in the environment or local `.env` file so requests include an identifiable User-Agent, for example:

```text
SEC_CONTACT_EMAIL=you@example.com
```

Market requests (used by `--source market` or `--source both`) require `ALPHA_VANTAGE_API_KEY` in the environment or local `.env` file. Alpha Vantage provides API keys through its [API key page](https://www.alphavantage.co/support/#api-key).

Do not commit API keys, personal contact details, or other local environment values.

## Implementation status
This repository is a developing data engineering and analytics workspace, not a finished business-facing application. Its objective is a guiding direction rather than a frozen specification: the data model, sources, tools, and analytical use cases can change as the project grows. Documentation should distinguish what is implemented now from what is planned or under consideration.

## Next steps
Planned work for the project includes:

- expanding the ingestion layer for market and macro data
- defining dbt staging and mart models for company and macro dimensions
- validating schema quality and data quality tests
- building orchestration around scheduled refreshes
- adding portfolio and scenario analysis views for mining exposure monitoring