# assign_tag_type_to_all_tags.py

import json
import httpx
from main import WEBFLOW_HEADERS

# collection IDs
TAGS_COLLECTION_ID = "67fdc82b88d4440b0005dabe"       # tags
TAG_TYPE_ID_TO_ASSIGN = "67fe18f01ed77d98048031d5"     # e.g. "Location" 的 ID

# slug name
FIELD_SLUG = "tag-type-7"  # from tags.json

# 读取 tag mapping
with open("mapping/tags.json", "r", encoding="utf-8") as f:
    tag_mapping = json.load(f)

def patch_webflow_item(collection_id, item_id, field_data):
    url = f"https://api.webflow.com/v2/collections/{collection_id}/items/{item_id}"
    payload = {
        "fieldData": field_data
    }
    r = httpx.patch(url, headers=WEBFLOW_HEADERS, json=payload, timeout=30)
    if r.status_code in [200, 201, 202]:
        print(f"✅ Updated item {item_id}")
    else:
        print(f"❌ Failed to update item {item_id}: {r.status_code}")
        print(r.text)

# 批量更新所有 tag 项
for notion_id, entry in tag_mapping.items():
    webflow_id = entry.get("webflowID")
    if not webflow_id:
        print(f"⚠️  Skipping {notion_id}, no webflowID")
        continue

    patch_webflow_item(
        collection_id=TAGS_COLLECTION_ID,
        item_id=webflow_id,
        field_data={
            FIELD_SLUG: TAG_TYPE_ID_TO_ASSIGN
        }
    )
