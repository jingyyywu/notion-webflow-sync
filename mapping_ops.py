# mapping_ops.py

import json
from main import MAPPING_DIR

def load_mapping(key: str) -> dict:
    path = MAPPING_DIR / f"{key}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_mapping(key: str, mapping: dict):
    MAPPING_DIR.mkdir(parents=True, exist_ok=True)
    path = MAPPING_DIR / f"{key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"💾 Mapping saved for {key} → {path.name}")