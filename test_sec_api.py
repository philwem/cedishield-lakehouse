import requests

cik = "0001164727"
url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"

headers = {"User-Agent": "CediShieldDataEngineer philipwemgah990@gmail.com"}

print(f"Connecting to SEC EDGAR API for CIK {cik}...")
response = requests.get(url, headers=headers, timeout=30)

print("Status Code:", response.status_code)
response.raise_for_status()  # Raise an error for bad responses

data = response.json()
print("Company" , data.get("entityName"))
print("Top-level keys:", list(data.keys()))
print("Available taxonomies:", list(data.get("facts", {}).keys()))


