from notion_client import Client
import json
from datetime import datetime
from pathlib import Path
from notion_utils import extract_title  # 使用外部工具模块

# Notion 初始化
notion = Client(auth="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")  # TODO: 替换为你的 token

# Database ID 配置
notion_database_ids = {
    "posts": "1d6d4d6cbd3d8084b0beece3bef13eb8",
    "tags": "1d6d4d6cbd3d80b8a509f5a9b78d8c14",
    "tag_types": "1d6d4d6cbd3d80a0bd1cd3e0023e9aea"
}

# 路径定义
mapping_root = Path("mapping")
schema_root = Path("schema_store")

# 工具函数
def parse_iso_time(iso_str):
    return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ")

def load_mapping(db_name):
    path = mapping_root / f"{db_name}.json"
    return json.loads(path.read_text()) if path.exists() else {}

def save_mapping(db_name, mapping):
    path = mapping_root / f"{db_name}.json"
    path.write_text(json.dumps(mapping, indent=2))

def diff_items(notion_items, mapping):
    notion_ids = {item["id"] for item in notion_items}
    mapped_ids = set(mapping.keys())

    create_list = []
    update_list = []
    delete_list = []

    for item in notion_items:
        nid = item["id"]
        last_edited = parse_iso_time(item["last_edited_time"])

        if nid not in mapping:
            create_list.append(item)
            update_list.append(item)  # 新建后需要写入字段
        else:
            last_synced = parse_iso_time(mapping[nid]["lastSyncedAt"])
            if last_edited > last_synced:
                update_list.append(item)

    for nid in mapped_ids:
        if nid not in notion_ids:
            delete_list.append({
                "notionID": nid,
                "webflowID": mapping[nid]["webflowID"]
            })

    return create_list, update_list, delete_list

# 主流程
for db_name, db_id in notion_database_ids.items():
    print(f"\n📦 Checking database: {db_name}")
    
    response = notion.databases.query(database_id=db_id)
    notion_items = response["results"]

    mapping = load_mapping(db_name)
    create_list, update_list, delete_list = diff_items(notion_items, mapping)

    print(f"🟩 Create list ({len(create_list)}):")
    for i in create_list:
        print(f"  - {extract_title(i)} ({i['id']})")

    print(f"🟦 Update list ({len(update_list)}):")
    for i in update_list:
        print(f"  - {extract_title(i)} ({i['id']})")

    print(f"🟥 Delete list ({len(delete_list)}):")
    for i in delete_list:
        print(f"  - {i['notionID']} → {i['webflowID']}")