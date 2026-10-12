import os
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
    
    
if __name__ == "__main__":
    # Test the function with Newmont Corporation's CIK
    df_sec = fetch_sec_facts("0001164727")

    print("\n--- DATA FRAME SAMPLE ---")
    print(df_sec.head(5))

    print("\n--- UNIQUE FINANCIAL CONCEPTS FOUND ---")
    if df_sec.empty:
        print("No 10-K or 10-Q US-GAAP facts found.")
    else:
        print(df_sec["concept"].unique()[:10])

    print("\n--- SUMMARY STATS ---")
    print(f"Total rows extracted: {len(df_sec):,}")
