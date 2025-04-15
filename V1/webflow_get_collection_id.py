import httpx

headers = {
    "Authorization": "Bearer e7ba9a7f3eb7faf3ccab30f1e3cb9e06c4d1958d69f795fdc001f2a91c0abd63",  # 注意 Bearer 要加
    "accept": "application/json"
}

site_id = "63e68fda1277704c5d9c5f9c"  # 你之前获取到的站点 ID
url = f"https://api.webflow.com/v2/sites/{site_id}/collections"

resp = httpx.get(url, headers=headers)
resp.raise_for_status()
data = resp.json()

print(f"\n📦 Collections under site {site_id}:")
for col in data.get("collections", []):
    print(f"- {col['displayName']} (slug: {col['slug']}, id: {col['id']})")
