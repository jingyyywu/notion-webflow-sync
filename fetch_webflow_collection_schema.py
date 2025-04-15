import httpx
import json
from main import WEBFLOW_HEADERS, DATABASE_MAPPING

def fetch_webflow_schema(collection_id: str):
    url = f"https://api.webflow.com/v2/collections/{collection_id}"
    r = httpx.get(url, headers=WEBFLOW_HEADERS)
    r.raise_for_status()
    return r.json()

def save_schema_to_file(db_key: str, schema_data: dict):
    path = f"_debug_schema_{db_key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema_data, f, indent=2)
    print(f"✅ Saved schema for '{db_key}' to {path}")

if __name__ == "__main__":
    for db_key, config in DATABASE_MAPPING.items():
        collection_id = config["webflow_collection_id"]
        print(f"🔍 Fetching schema for '{db_key}' ({collection_id})...")
        schema = fetch_webflow_schema(collection_id)
        save_schema_to_file(db_key, schema)