# sync_webflow_fields_from_schema_id_based.py
import json
import httpx

# 填入你的参数
WEBFLOW_TOKEN = "Bearer e7ba9a7f3eb7faf3ccab30f1e3cb9e06c4d1958d69f795fdc001f2a91c0abd63"
COLLECTION_ID = "67fdc803e92c61467c5c011f"  # posts collection
SCHEMA_PATH = "schema_store/posts.json"

headers = {
    "Authorization": WEBFLOW_TOKEN,
    "accept": "application/json",
    "content-type": "application/json"
}

def get_existing_fields(collection_id):
    url = f"https://api.webflow.com/v2/collections/{collection_id}"
    r = httpx.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    return {f["displayName"]: f["type"] for f in data.get("fields", [])}

def notion_type_to_webflow(notion_type):
    mapping = {
        "title": "PlainText",
        "rich_text": "PlainText",
        "number": "Number",
        "date": "Date",
        "select": "Option",
        "multi_select": "MultiOption",
        "url": "Link",
        "files": "File",
        "checkbox": "Boolean"
    }
    return mapping.get(notion_type, None)

def sync_fields():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        notion_schema = json.load(f)

    existing_fields = get_existing_fields(COLLECTION_ID)

    for field_name, spec in notion_schema.items():
        notion_type = spec["type"]

        # 特殊处理 title → Name
        if notion_type == "title":
            webflow_field_name = "Name"
            webflow_type = "PlainText"
        elif notion_type == "relation":
            target_id = spec.get("target")
            if not target_id:
                print(f"⚠️  Skipped relation without target: {field_name}")
                continue
            webflow_field_name = field_name
            webflow_type = "MultiReference"  # 默认使用多项引用
        else:
            webflow_field_name = field_name
            webflow_type = notion_type_to_webflow(notion_type)

        if not webflow_type:
            print(f"⚠️  Skipping unsupported field type: {field_name} ({notion_type})")
            continue

        if webflow_field_name in existing_fields:
            current_type = existing_fields[webflow_field_name]
            if current_type != webflow_type:
                print(f"⚠️  Field exists but type mismatch: {webflow_field_name} ({current_type} vs {webflow_type})")
            else:
                print(f"✅ Field already exists and matches: {webflow_field_name}")
            continue

        print(f"🔧 Creating field: {webflow_field_name} ({webflow_type})")

        payload = {
            "displayName": webflow_field_name,
            "slug": webflow_field_name.lower().replace(" ", "-"),
            "type": webflow_type,
            "required": False
        }

        if notion_type == "relation":
            payload["reference"] = {
                "collectionId": spec["target"]
            }

        url = f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/fields"
        r = httpx.post(url, headers=headers, json=payload)
        if r.status_code in [200, 201]:
            print(f"✅ Created field: {webflow_field_name}")
        else:
            print(f"❌ Error creating field {webflow_field_name}: {r.status_code}")
            print(r.text)

if __name__ == "__main__":
    sync_fields()