import argparse
import os
import time
from datetime import date

import requests
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

SEC_FACT_COLUMNS = [
    "cik",
    "entity_name",
    "concept",
    "unit",
    "value",
    "start_date",
    "end_date",
    "filed_date",
    "form_type",
    "fiscal_year",
    "fiscal_period",
    "accession_number",
]


def fetch_sec_facts(cik: str) -> pd.DataFrame:
    """
    Fetches, flattens, and returns historical US-GAAP financial facts
    for a given corporate CIK from the SEC EDGAR API.
    """
    cik_value = str(cik).strip()
    if not cik_value.isascii() or not cik_value.isdecimal() or len(cik_value) > 10:
        raise ValueError("CIK must contain between 1 and 10 ASCII digits.")

    contact_email = os.getenv("SEC_CONTACT_EMAIL", "").strip()
    if not contact_email:
        raise ValueError(
            "SEC_CONTACT_EMAIL must be set to a contact email for SEC API requests."
        )

    padded_cik = cik_value.zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{padded_cik}.json"
    headers = {"User-Agent": f"CediShieldAnalytics {contact_email}"}

    print(f"Connecting to SEC EDGAR API for CIK {padded_cik}...")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to SEC API: {e}")
        raise

    data = response.json()
    entity_name = data.get("entityName", "Unknown")
    facts = data.get("facts", {}).get("us-gaap", {})

    rows = []

    # Flatten the deeply nested JSON tree
    for concept_name, concept_data in facts.items():
        units_dict = concept_data.get("units", {})
        for unit_name, observations in units_dict.items():
            for obs in observations:
                # Production filter: Keep only primary SEC reporting forms
                form_type = obs.get("form")
                if form_type in ["10-K", "10-Q"]:
                    rows.append(
                        {
                            "cik": padded_cik,
                            "entity_name": entity_name,
                            "concept": concept_name,
                            "unit": unit_name,
                            "value": obs.get("val"),
                            "start_date": obs.get("start"),
                            "end_date": obs.get("end"),
                            "filed_date": obs.get("filed"),
                            "form_type": form_type,
                            "fiscal_year": obs.get("fy"),
                            "fiscal_period": obs.get("fp"),
                            "accession_number": obs.get("accn"),
                        }
                    )

    sec_df = pd.DataFrame(rows, columns=SEC_FACT_COLUMNS)

    print(
        f"Successfully extracted {len(sec_df):,} flattened records for {entity_name}."
    )
    return sec_df




MARKET_PRICE_COLUMNS = [
    "market_date",
    "ticker",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume",
]

MARKET_REQUEST_DELAY_SECONDS = 12


def fetch_market_prices(
    tickers: list[str], start_date: str = "2020-01-01"
) -> pd.DataFrame:
    """Fetch Alpha Vantage daily OHLCV data into a normalized DataFrame."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY must be set in the environment.")

    if not tickers or any(not ticker.strip() for ticker in tickers):
        raise ValueError("At least one non-empty ticker symbol is required.")
    tickers = [ticker.strip() for ticker in tickers]
    try:
        date.fromisoformat(start_date)
    except ValueError as exc:
        raise ValueError("start_date must use YYYY-MM-DD format.") from exc

    print(f"Fetching market data from Alpha Vantage for tickers: {tickers}...")
    rows = []
    for ticker_index, ticker in enumerate(tickers):
        if ticker_index:
            time.sleep(MARKET_REQUEST_DELAY_SECONDS)

        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "TIME_SERIES_DAILY",
                    "symbol": ticker,
                    "outputsize": "compact",
                    "apikey": api_key,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError) as exc:
            print(
                f"ERROR: Alpha Vantage request failed for {ticker}: {exc}"
            )
            continue

        if not isinstance(data, dict):
            print(f"ERROR: Alpha Vantage returned an invalid response for {ticker}.")
            continue

        api_issue = (
            data.get("Error Message")
            or data.get("Note")
            or data.get("Information")
        )
        if api_issue:
            print(f"WARNING: Alpha Vantage reported an issue for {ticker}: {api_issue}")
            continue

        time_series = data.get("Time Series (Daily)", {})
        if not isinstance(time_series, dict) or not time_series:
            print(
                f"WARNING: Alpha Vantage returned no daily time series for {ticker}."
            )
            continue

        for market_date, metrics in time_series.items():
            if market_date < start_date:
                continue
            rows.append(
                {
                    "market_date": market_date,
                    "ticker": ticker,
                    "open_price": metrics.get("1. open"),
                    "high_price": metrics.get("2. high"),
                    "low_price": metrics.get("3. low"),
                    "close_price": metrics.get("4. close"),
                    "volume": metrics.get("5. volume"),
                }
            )

    market_df = pd.DataFrame(rows, columns=MARKET_PRICE_COLUMNS)
    for column in (
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
    ):
        market_df[column] = pd.to_numeric(market_df[column], errors="coerce")

    market_df = market_df.dropna(subset=["close_price"])

    if market_df.empty:
        print(
            "WARNING: No usable Alpha Vantage market observations were returned."
        )
        return market_df

    market_df = market_df.sort_values(
        ["ticker", "market_date"]
    ).reset_index(drop=True)
    print(
        f"Successfully fetched {len(market_df):,} market observation records "
        "from Alpha Vantage."
    )
    return market_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch CediShield source data.")
    parser.add_argument(
        "--source",
        choices=("market", "sec", "both"),
        default="market",
        help="Data source to fetch (default: market).",
    )
    args = parser.parse_args()

    if args.source in ("market", "both"):
        # The standard daily endpoint is for equity symbols, not Yahoo futures symbols.
        test_tickers = ["NEM"]
        df_market = fetch_market_prices(test_tickers)
        print("\n--- MARKET PRICE SAMPLE ---")
        print(df_market.head())

    if args.source in ("sec", "both"):
        df_sec = fetch_sec_facts("0001164727")

        print("\n--- SEC DATA FRAME SAMPLE ---")
        print(df_sec.head(5))

        print("\n--- UNIQUE FINANCIAL CONCEPTS FOUND ---")
        if df_sec.empty:
            print("No 10-K or 10-Q US-GAAP facts found.")
        else:
            print(df_sec["concept"].unique()[:10])

        print("\n--- SEC SUMMARY STATS ---")
        print(f"Total rows extracted: {len(df_sec):,}")
