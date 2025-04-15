# schema_extractor.py

from notion_client import Client
import json
from pathlib import Path

notion = Client(auth="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")  # TODO: 替换为你的 token

notion_database_ids = {
    "posts": "1d6d4d6cbd3d8084b0beece3bef13eb8",
    "tags": "1d6d4d6cbd3d80b8a509f5a9b78d8c14",
    "tag_types": "1d6d4d6cbd3d80a0bd1cd3e0023e9aea"
}

schema_store_path = Path("schema_store")
schema_store_path.mkdir(exist_ok=True)

def extract_notion_schema(db_id):
    db_info = notion.databases.retrieve(database_id=db_id)
    properties = db_info.get("properties", {})

    schema = {}

    for field_name, field_info in properties.items():
        field_type = field_info.get("type")
        schema[field_name] = { "type": field_type }

        # 如果是 relation，还记录目标 database
        if field_type == "relation":
            schema[field_name]["target"] = field_info["relation"].get("database_id")

    return schema

def save_schema(db_name, schema):
    path = schema_store_path / f"{db_name}.json"
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

# 主流程
if __name__ == "__main__":
    for db_name, db_id in notion_database_ids.items():
        print(f"Extracting schema for: {db_name}")
        schema = extract_notion_schema(db_id)
        save_schema(db_name, schema)
        print(f"Saved to schema_store/{db_name}.json")