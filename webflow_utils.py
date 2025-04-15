import httpx


def get_webflow_fields(collection_id: str, headers: dict) -> list:
    url = f"https://api.webflow.com/v2/collections/{collection_id}"
    r = httpx.get(url, headers=headers)
    r.raise_for_status()
    return r.json()["fields"]


def create_webflow_field(collection_id: str, webflow_headers: dict, payload: dict) -> str | None:
    url = f"https://api.webflow.com/v2/collections/{collection_id}/fields"
    try:
        r = httpx.post(url, headers=webflow_headers, json=payload, timeout=30.0)
        if r.status_code in [200, 201]:
            data = r.json()
            print(f"✅ Created field: {payload['displayName']} → slug: {data.get('slug')}")
            return data.get("slug")
        else:
            print(f"❌ Failed to create field '{payload['displayName']}': {r.status_code}")
            print(r.text)
            return None
    except Exception as e:
        print(f"❌ Exception when creating field '{payload['displayName']}': {e}")
        return None


def create_webflow_item(collection_id: str, fields: dict, headers: dict) -> str | None:
    url = f"https://api.webflow.com/v2/collections/{collection_id}/items"
    payload = {
        "isArchived": False,
        "isDraft": False,
        "fieldData": fields,
    }
    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        if r.status_code in [200, 201, 202]:
            data = r.json()
            return data.get("id")
        else:
            print(f"❌ Failed to create item: {r.status_code}")
            print(r.text)
            return None
    except Exception as e:
        print(f"❌ Exception when creating item: {e}")
        return None


def update_webflow_item(webflow_id: str, collection_id: str, field_data: dict, headers: dict) -> bool:
    url = f"https://api.webflow.com/v2/collections/{collection_id}/items/{webflow_id}"
    payload = {
        "fieldData": field_data,
    }
    try:
        r = httpx.patch(url, headers=headers, json=payload, timeout=30.0)
        if r.status_code in [200, 201, 202]:
            print(f"✅ Updated Webflow item {webflow_id}")
            return True
        else:
            print(f"❌ Failed to update item {webflow_id}: {r.status_code}")
            print(r.text)
            return False
    except Exception as e:
        print(f"❌ Exception when updating item {webflow_id}: {e}")
        return False
