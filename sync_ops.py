import datetime
from webflow_utils import create_webflow_item, get_webflow_fields, create_webflow_field, update_webflow_item
from main import NOTION_TO_WEBFLOW_LOOKUP

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

def sync_fields_to_webflow(schema: dict, collection_id: str, webflow_headers: dict) -> dict:
    existing_fields = get_webflow_fields(collection_id, webflow_headers)
    slug_map = {}

    displayName_to_slug = {f["displayName"]: f["slug"] for f in existing_fields}
    displayName_to_type = {f["displayName"]: f["type"] for f in existing_fields}

    for field_name, spec in schema.items():
        notion_type = spec["type"]

        if notion_type == "title":
            display_name = "Name"
            webflow_type = "PlainText"
        elif notion_type == "relation":
            display_name = field_name
            webflow_type = "MultiReference"
        else:
            display_name = field_name
            webflow_type = notion_type_to_webflow(notion_type)

        if not webflow_type:
            print(f"⚠️  Skipping unsupported field: {field_name} ({notion_type})")
            continue

        # 使用 Webflow 返回的真实 slug
        slug = displayName_to_slug.get(display_name)
        if not slug:
            slug = display_name.lower().replace(" ", "-")

        slug_map[field_name] = slug

        if display_name in displayName_to_type:
            current_type = displayName_to_type[display_name]
            if current_type != webflow_type:
                print(f"⚠️  Type mismatch for field '{display_name}': existing={current_type}, expected={webflow_type}")
            else:
                print(f"✅ Field '{display_name}' already exists and matches type")
            continue

        payload = {
            "displayName": display_name,
            "slug": slug,
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

        print(f"➕ Creating Webflow field: {display_name} ({webflow_type})")
        create_webflow_field(
            collection_id=collection_id,
            webflow_headers=webflow_headers,
            payload=payload
        )

    return slug_map

def sync_items_to_webflow(create_list, update_list, delete_list, mapping, schema, collection_id, headers, slug_map):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

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

        fields = { "name": name }
        webflow_id = create_webflow_item(collection_id, fields, headers)
        if webflow_id:
            mapping[notion_id] = {
                "webflowID": webflow_id,
                "lastSyncedAt": now
            }
            print(f"✅ Created Webflow item for '{name}' → {webflow_id}")
        else:
            print(f"❌ Failed to create item for Notion ID {notion_id}")

    for item in update_list:
        notion_id = item["id"]
        if notion_id not in mapping:
            print(f"❌ Skipping update: Notion ID {notion_id} not in mapping")
            continue

        webflow_id = mapping[notion_id]["webflowID"]
        field_data = {}

        for field_name, spec in schema.items():
            slug = slug_map.get(field_name)
            if not slug:
                continue

            notion_type = spec["type"]
            if notion_type in ["title", "rich_text"]:
                val = item["properties"].get(field_name, {})
                text_fragments = val.get(notion_type, [])
                if text_fragments:
                    field_data[slug] = text_fragments[0].get("plain_text", "")

            elif notion_type == "relation":
                val = item["properties"].get(field_name, {}).get("relation", [])
                target_ids = [v["id"] for v in val]
                wf_ids = [mapping[tid]["webflowID"] for tid in target_ids if tid in mapping and "webflowID" in mapping[tid]]
                if wf_ids:
                    field_data[slug] = wf_ids if len(wf_ids) > 1 else wf_ids[0]

        success = update_webflow_item(
            webflow_id=webflow_id,
            collection_id=collection_id,
            field_data=field_data,
            headers=headers
        )

        if success:
            mapping[notion_id]["lastSyncedAt"] = now

    return mapping