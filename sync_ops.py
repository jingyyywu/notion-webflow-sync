import datetime
import httpx
import json
from pathlib import Path
from webflow_utils import (
    create_webflow_item,
    get_webflow_fields,
    create_webflow_field,
    update_webflow_item,
    delete_webflow_item,
    fetch_webflow_item,
    patch_field_to_remove_reference,
)

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

def load_slug_map(db_name: str) -> dict:
    path = Path("slug_store") / f"{db_name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

def save_slug_map(db_name: str, slug_map: dict):
    path = Path("slug_store") / f"{db_name}.json"
    path.write_text(json.dumps(slug_map, indent=2), encoding="utf-8")

def sync_fields_to_webflow(schema: dict, collection_id: str, webflow_headers: dict, db_name: str) -> dict:
    existing_fields = get_webflow_fields(collection_id, webflow_headers)
    slug_map = load_slug_map(db_name)

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

        # 优先使用已有 slug_map 中记录的 slug
        if field_name in slug_map:
            continue

        slug = displayName_to_slug.get(display_name)
        if not slug:
            slug = display_name.lower().replace(" ", "-")

        if display_name in displayName_to_type:
            current_type = displayName_to_type[display_name]
            print(f"🌐 Webflow field: {display_name} (type: {current_type}, slug: {slug})")

            if current_type != webflow_type:
                print(f"⚠️  Type mismatch for field '{display_name}': expected={webflow_type}")
            else:
                print(f"✅ Field '{display_name}' already exists and matches type")

            slug_map[field_name] = slug
            print(f"📝 Recorded slug: {field_name} → {slug}")
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
        returned_slug = create_webflow_field(
            collection_id=collection_id,
            webflow_headers=webflow_headers,
            payload=payload
        )
        if returned_slug:
            slug_map[field_name] = returned_slug

    save_slug_map(db_name, slug_map)
    print(f"📁 Final slug map for {db_name}:", slug_map)
    return slug_map

def sync_items_to_webflow(create_list, update_list, delete_list, mapping, schema, collection_id, headers, slug_map, all_mappings=None):
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
                print(f"❌ No slug found for {field_name}, skipping")
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
                wf_ids = []
                for tid in target_ids:
                    found = False
                    if tid in mapping and "webflowID" in mapping[tid]:
                        wf_ids.append(mapping[tid]["webflowID"])
                        print(f"   ✅ Target ID {tid} exists in mapping with Webflow ID {mapping[tid]['webflowID']}")
                        found = True
                    elif all_mappings:
                        for k, other_map in all_mappings.items():
                            if tid in other_map and "webflowID" in other_map[tid]:
                                wf_ids.append(other_map[tid]["webflowID"])
                                print(f"   ✅ Target ID {tid} found in mapping[{k}] with Webflow ID {other_map[tid]['webflowID']}")
                                found = True
                                break
                    if not found:
                        print(f"   ❌ Target ID {tid} does not exist in any mapping")
                if wf_ids:
                    field_data[slug] = wf_ids if len(wf_ids) > 1 else wf_ids[0]

        success = update_webflow_item(
            webflow_id=webflow_id,
            collection_id=collection_id,
            field_data=field_data,
            headers=headers,
        )

        if success:
            mapping[notion_id]["lastSyncedAt"] = now

    
    for item in delete_list:
        notion_id = item["notionID"]
        webflow_id = item["webflowID"]

        print(f"🗑️ Deleting item: Notion ID = {notion_id} → Webflow ID = {webflow_id}")
        success = delete_webflow_item(webflow_id, collection_id, headers)
        if not success:
            try:
                import json
                r = httpx.delete(f"https://api.webflow.com/v2/collections/{collection_id}/items/{webflow_id}", headers=headers, timeout=30.0)
                if r.status_code == 409:
                    error_json = r.json()
                    conflicts = error_json["details"][0].get("conflicts", [])
                    for c in conflicts:
                        ref = c.get("ref", {})
                        ref_id = ref.get("id")
                        ref_col = ref.get("collectionId")
                        ref_name = ref.get("name")
                        print(f"🔗 Removing reference in: {ref_name} ({ref_id}) in collection {ref_col}")
                        # brute force: try all fields
                        ref_item = fetch_webflow_item(ref_id, ref_col, headers)
                        if ref_item:
                            for slug, value in ref_item.get("fieldData", {}).items():
                                if isinstance(value, list) and webflow_id in value:
                                    patch_field_to_remove_reference(ref_id, ref_col, slug, webflow_id, headers)
                                elif isinstance(value, str) and value == webflow_id:
                                    patch_field_to_remove_reference(ref_id, ref_col, slug, webflow_id, headers)
                    # retry delete
                    success = delete_webflow_item(webflow_id, collection_id, headers)
            except Exception as e:
                print(f"❌ Force delete error: {e}")

        if success and notion_id in mapping:
            del mapping[notion_id]


    return mapping
