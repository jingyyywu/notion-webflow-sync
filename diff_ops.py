# diff_ops.py

from datetime import datetime

def parse_iso_time(iso_str: str) -> datetime:
    try:
        return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")

def get_item_diff(notion_items: list, mapping: dict) -> tuple[list, list, list]:
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
            update_list.append(item)  # 新建后也要填充字段
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