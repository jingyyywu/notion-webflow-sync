# main.py
from pathlib import Path

# ✅ Webflow 网站站点 ID（如有需要可用于 Site 查询）
WEBFLOW_SITE_ID = "63e68fda1277704c5d9c5f9c"

# ✅ Notion 和 Webflow 数据库之间的映射关系
DATABASE_MAPPING = {
    "posts": {
        "notion_db_id": "1d6d4d6c-bd3d-8084-b0be-ece3bef13eb8",
        "webflow_collection_id": "67fdc803e92c61467c5c011f"
    },
    "tags": {
        "notion_db_id": "1d6d4d6c-bd3d-80b8-a509-f5a9b78d8c14",
        "webflow_collection_id": "67fdc82b88d4440b0005dabe"
    },
    "tag_types": {
        "notion_db_id": "1d6d4d6c-bd3d-80a0-bd1c-d3e0023e9aea",
        "webflow_collection_id": "67fdc83506a0b970529cfe34"
    }
}

# ✅ 反向映射：Notion DB ID → Webflow Collection ID
NOTION_TO_WEBFLOW_LOOKUP = {
    config["notion_db_id"]: config["webflow_collection_id"]
    for config in DATABASE_MAPPING.values()
}

# ✅ 存放 schema 文件和 ID mapping 的目录
SCHEMA_DIR = Path("schema_store")
MAPPING_DIR = Path("mapping")

# ✅ Webflow v2 API token（带 Bearer 前缀）
WEBFLOW_TOKEN = "Bearer e7ba9a7f3eb7faf3ccab30f1e3cb9e06c4d1958d69f795fdc001f2a91c0abd63"
WEBFLOW_HEADERS = {
    "Authorization": WEBFLOW_TOKEN,
    "accept": "application/json",
    "content-type": "application/json"
}

# ✅ Notion API token
NOTION_TOKEN = "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"