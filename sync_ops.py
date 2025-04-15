# sync_ops.py

import datetime
from webflow_utils import create_webflow_item, get_webflow_fields, create_webflow_field
from main import NOTION_TO_WEBFLOW_LOOKUP
from webflow_utils import update_webflow_item

def normalize_notion_id(id_str: str) -> str:
    if "-" in id_str:
        return id_str
    return f"{id_str[0:8]}-{id_str[8:12]}-{id_str[12:16]}-{id_str[16:20]}-{id_str[20:]}"

def notion_type_to_webflow(notion_type: str) -> str | None:
    mapping = {
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

def sync_fields_to_webflow(schema: dict, collection_id: str, webflow_headers: dict):
    existing_fields = get_webflow_fields(collection_id, webflow_headers)

    for field_name, spec in schema.items():
        notion_type = spec["type"]

        if notion_type == "title":
            webflow_field_name = "Name"
            webflow_type = "PlainText"
        elif notion_type == "relation":
            webflow_field_name = field_name
            webflow_type = "MultiReference"
        else:
            webflow_field_name = field_name
            webflow_type = notion_type_to_webflow(notion_type)

        if not webflow_type:
            print(f"⚠️  Skipping unsupported field: {field_name} ({notion_type})")
            continue

        if webflow_field_name in existing_fields:
            current_type = existing_fields[webflow_field_name]
            if current_type != webflow_type:
                print(f"⚠️  Type mismatch for field '{webflow_field_name}': existing={current_type}, expected={webflow_type}")
            else:
                print(f"✅ Field '{webflow_field_name}' already exists and matches type")
            continue

        payload = {
            "displayName": webflow_field_name,
            "slug": webflow_field_name.lower().replace(" ", "-"),
            "type": webflow_type,
            "required": False
        }

        if notion_type == "relation":
            raw_target_id = spec.get("target", "")
            normalized_id = normalize_notion_id(raw_target_id)
            target_collection_id = NOTION_TO_WEBFLOW_LOOKUP.get(normalized_id)
            if not target_collection_id:
                print(f"❌ Cannot create relation field '{field_name}': unknown target {normalized_id}")
                continue
            payload["metadata"] = {
                "collectionId": target_collection_id
            }

        print(f"➕ Creating Webflow field: {webflow_field_name} ({webflow_type})")
        create_webflow_field(
            collection_id=collection_id,
            webflow_headers=webflow_headers,
            payload=payload
        )

def sync_items_to_webflow(create_list, update_list, delete_list, mapping, schema, collection_id, headers):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Step 1: Create new items with just Name field
    for item in create_list:
        notion_id = item["id"]
        title_property = [v for v in item["properties"].values() if v["type"] == "title"]
        name = ""
        if title_property:
            title_text = title_property[0]["title"]
            if title_text and len(title_text) > 0 and "plain_text" in title_text[0]:
                name = title_text[0]["plain_text"]
        if not name:
            print(f"❌ Skipping create: Notion item {notion_id} has no name")
            continue

        fields = {
            "name": name
        }

        webflow_id = create_webflow_item(collection_id, fields, headers)
        if webflow_id:
            mapping[notion_id] = {
                "webflowID": webflow_id,
                "lastSyncedAt": now
            }
            print(f"✅ Created Webflow item for '{name}' → {webflow_id}")
        else:
            print(f"❌ Failed to create item for Notion ID {notion_id}")


    # Step 2: Update existing items
    for item in update_list:
        notion_id = item["id"]
        if notion_id not in mapping:
            print(f"❌ Skipping update: Notion ID {notion_id} not in mapping")
            continue

        webflow_id = mapping[notion_id]["webflowID"]
        field_data = {}

        for field_name, spec in schema.items():
            notion_type = spec["type"]

            if notion_type in ["title", "rich_text"]:
                val = item["properties"].get(field_name, {})
                text_fragments = val.get(notion_type, [])
                if text_fragments:
                    field_data[field_name.lower().replace(" ", "-")] = text_fragments[0].get("plain_text", "")

            elif notion_type == "relation":
                val = item["properties"].get(field_name, {}).get("relation", [])
                target_ids = [v["id"] for v in val]
                wf_ids = []
                for tid in target_ids:
                    if tid in mapping and "webflowID" in mapping[tid]:
                        wf_ids.append(mapping[tid]["webflowID"])
                if wf_ids:
                    field_data[field_name.lower().replace(" ", "-")] = wf_ids if len(wf_ids) > 1 else wf_ids[0]

        success = update_webflow_item(
            webflow_id=webflow_id,
            collection_id=collection_id,
            field_data=field_data,
            headers=headers
        )

        if success:
            mapping[notion_id]["lastSyncedAt"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return mapping
