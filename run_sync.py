# from schema_ops import pull_and_save_schema
# from diff_ops import get_item_diff
# from sync_ops import sync_fields_to_webflow
# from mapping_ops import load_mapping, save_mapping

# def run_full_sync(DATABASE_MAPPING, NOTION_TOKEN, WEBFLOW_TOKEN):
#     for key, ids in DATABASE_MAPPING.items():
#         notion_db_id = ids["notion_db_id"]
#         webflow_collection_id = ids["webflow_collection_id"]

#         # 拉 schema 并保存为文件
#         schema = pull_and_save_schema(key, notion_db_id, NOTION_TOKEN)

#         # 读取 mapping 文件
#         mapping = load_mapping(key)

#         # 拉当前 notion 数据库 items
#         notion_items = fetch_all_items(notion_db_id, NOTION_TOKEN)  # schema_ops 或单独抽出来

#         # 得到 create/update/delete 列表
#         create_list, update_list, delete_list = get_item_diff(notion_items, mapping)

#         # 同步字段结构到 Webflow
#         sync_fields_to_webflow(schema, webflow_collection_id, WEBFLOW_TOKEN)

#         # 后续逻辑: create/update/delete item 也会用这些 list 来调 sync_ops


# run_sync.py

from main import DATABASE_MAPPING, NOTION_TOKEN, WEBFLOW_HEADERS
from schema_ops import pull_and_save_schema_if_changed
from mapping_ops import load_mapping, save_mapping
from notion_utils import fetch_all_items
from diff_ops import get_item_diff
from sync_ops import sync_fields_to_webflow  # 使用真实 Webflow 字段同步

def run_full_sync():
    print("🚀 Starting sync...")

    for key, ids in DATABASE_MAPPING.items():
        print(f"\n🔍 Syncing schema for database: {key}")
        notion_db_id = ids["notion_db_id"]
        webflow_collection_id = ids["webflow_collection_id"]

        # Step 1: 拉取并更新 schema
        schema, bSchemaChanged = pull_and_save_schema_if_changed(key, notion_db_id, NOTION_TOKEN)
        if bSchemaChanged:
            print(f"⚠️  Schema changed for {key} – will trigger Webflow field resync")
            sync_fields_to_webflow(schema, webflow_collection_id, WEBFLOW_HEADERS)
        else:
            print(f"✅ Schema is up-to-date for {key}")

        # Step 2: 读取 mapping
        mapping = load_mapping(key)
        print(f"📚 Current mapping entries for {key}: {len(mapping)}")

        # Step 3: 拉取 Notion items
        notion_items = fetch_all_items(notion_db_id, NOTION_TOKEN)

        # Step 4: 计算差异
        create_list, update_list, delete_list = get_item_diff(notion_items, mapping)
        print(f"🟩 Create: {len(create_list)}")
        print(f"🟦 Update: {len(update_list)}")
        print(f"🟥 Delete: {len(delete_list)}")

        # Step 5: 实际同步 Webflow items
        from sync_ops import sync_items_to_webflow
        mapping = sync_items_to_webflow(
            create_list=create_list,
            update_list=update_list,
            delete_list=delete_list,
            mapping=mapping,
            schema=schema,
            collection_id=webflow_collection_id,
            headers=WEBFLOW_HEADERS
        )

        save_mapping(key, mapping)

if __name__ == "__main__":
    run_full_sync()