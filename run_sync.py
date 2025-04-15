from main import DATABASE_MAPPING, NOTION_TOKEN, WEBFLOW_HEADERS
from schema_ops import pull_and_save_schema_if_changed
from mapping_ops import load_mapping, save_mapping
from notion_utils import fetch_all_items
from diff_ops import get_item_diff
from sync_ops import sync_fields_to_webflow, sync_items_to_webflow

def run_full_sync():
    print("🚀 Starting full sync process...")

    schema_dict = {}
    slug_map_dict = {}
    notion_items_dict = {}
    mapping_dict = {}
    create_dict = {}
    update_dict = {}
    delete_dict = {}

    # Phase 1: sync schema & fields
    for key, ids in DATABASE_MAPPING.items():
        print(f"\n📑 Phase 1 - Syncing schema for: {key}")
        notion_db_id = ids["notion_db_id"]
        webflow_collection_id = ids["webflow_collection_id"]

        schema, _ = pull_and_save_schema_if_changed(key, notion_db_id, NOTION_TOKEN)
        schema_dict[key] = schema

        slug_map = sync_fields_to_webflow(schema, webflow_collection_id, WEBFLOW_HEADERS)
        slug_map_dict[key] = slug_map

    # Phase 2: fetch items and handle CREATE
    for key, ids in DATABASE_MAPPING.items():
        print(f"\n🛠 Phase 2 - Creating items for: {key}")
        notion_db_id = ids["notion_db_id"]
        webflow_collection_id = ids["webflow_collection_id"]

        mapping = load_mapping(key)
        notion_items = fetch_all_items(notion_db_id, NOTION_TOKEN)
        create_list, update_list, delete_list = get_item_diff(notion_items, mapping)

        print(f"🟩 Create: {len(create_list)} | 🟦 Update: {len(update_list)} | 🟥 Delete: {len(delete_list)}")

        # store for phase 3
        mapping_dict[key] = mapping
        notion_items_dict[key] = notion_items
        create_dict[key] = create_list
        update_dict[key] = update_list
        delete_dict[key] = delete_list

        # Only run create here
        mapping = sync_items_to_webflow(
            create_list=create_list,
            update_list=[],
            delete_list=[],
            mapping=mapping,
            schema=schema_dict[key],
            collection_id=webflow_collection_id,
            headers=WEBFLOW_HEADERS,
            slug_map=slug_map_dict[key]
        )

        save_mapping(key, mapping)
        mapping_dict[key] = mapping

    # Phase 3: run update (after all items are created)
    for key, ids in DATABASE_MAPPING.items():
        print(f"\n🖊 Phase 3 - Updating items for: {key}")
        webflow_collection_id = ids["webflow_collection_id"]

        mapping = mapping_dict[key]
        update_list = update_dict[key]

        mapping = sync_items_to_webflow(
            create_list=[],
            update_list=update_list,
            delete_list=[],
            mapping=mapping,
            schema=schema_dict[key],
            collection_id=webflow_collection_id,
            headers=WEBFLOW_HEADERS,
            slug_map=slug_map_dict[key]
        )

        save_mapping(key, mapping)

if __name__ == "__main__":
    run_full_sync()