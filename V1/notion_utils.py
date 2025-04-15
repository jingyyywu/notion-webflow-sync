# notion_utils.py
# 通用工具函数，用于解析 Notion 页面结构、提取字段值等

def extract_title(item):
    """
    提取 Notion 页面中的标题字段值（唯一一个 type == "title" 的字段）

    参数:
        item (dict): 从 Notion API 返回的单个页面对象

    返回:
        str: 提取到的标题文本，若为空则返回空字符串
    """
    props = item.get("properties", {})

    for key, value in props.items():
        if value.get("type") == "title":
            texts = value.get("title", [])
            if texts and len(texts) > 0:
                return texts[0].get("plain_text", "")
            else:
                return ""
    
    return ""