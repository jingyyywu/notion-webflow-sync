# notion_utils.py

from notion_client import Client

def fetch_all_items(notion_db_id: str, notion_token: str) -> list:
    notion = Client(auth=notion_token)
    all_results = []
    next_cursor = None

    while True:
        response = notion.databases.query(
            database_id=notion_db_id,
            start_cursor=next_cursor
        ) if next_cursor else notion.databases.query(database_id=notion_db_id)

        results = response.get("results", [])
        all_results.extend(results)

        if response.get("has_more"):
            next_cursor = response.get("next_cursor")
        else:
            break

    return all_results