# schema_ops.py

import json
from notion_client import Client
from main import SCHEMA_DIR

def pull_schema(key: str, notion_db_id: str, notion_token: str) -> dict:
    notion = Client(auth=notion_token)
    db_info = notion.databases.retrieve(database_id=notion_db_id)
    props = db_info.get("properties", {})

    schema = {}
    for name, prop in props.items():
        f_type = prop.get("type")
        field = { "type": f_type }

        if f_type == "relation":
            target_db = prop["relation"].get("database_id")
            field["target"] = target_db

        schema[name] = field

    return schema

def compare_and_update_schema(key: str, new_schema: dict) -> bool:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    path = SCHEMA_DIR / f"{key}.json"

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            old_schema = json.load(f)
        if old_schema == new_schema:
            print(f"✅ Schema unchanged for {key}")
            return False

    # 如果文件不存在或结构不同，写入新 schema
    path.write_text(json.dumps(new_schema, indent=2), encoding="utf-8")
    print(f"📄 Schema updated for {key} → {path.name}")
    return True

def pull_and_save_schema_if_changed(key: str, notion_db_id: str, notion_token: str) -> tuple[dict, bool]:
    new_schema = pull_schema(key, notion_db_id, notion_token)
    bChanged = compare_and_update_schema(key, new_schema)
    return new_schema, bChanged