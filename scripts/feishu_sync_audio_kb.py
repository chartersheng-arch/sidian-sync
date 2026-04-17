#!/usr/bin/env python3
"""
飞书文档同步脚本 - 支持批量同步多个 Wiki 页面
使用飞书开放平台 API 获取文档并转换为Markdown

依赖: requests (pip install requests)
运行: python feishu_sync_audio_kb.py
"""

import requests
import json
import os
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

# ============== 配置 ==============
APP_ID = "cli_a95df12efebb5cb1"
APP_SECRET = "7he9IYCwNoy34ntRs1WSvdZrIN1Z6N28"
WIKI_TOKENS = [
    "DLyEwYJifidA7lkuiqIcPA3unQK",  # 展锐LOG专题 (67 blocks)
]
OUTPUT_DIR = r"D:\sidian-charter\andriod\audio知识"
# ============== 配置 ==============

FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"


def get_tenant_access_token() -> Optional[str]:
    """获取 Tenant Access Token"""
    url = f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}

    try:
        resp = requests.post(url, json=payload, timeout=30)
        data = resp.json()

        if data.get("code") == 0:
            return data.get("tenant_access_token")
        else:
            print(f"获取Token失败: {data.get('msg')}")
    except Exception as e:
        print(f"获取Token异常: {e}")

    return None


def get_wiki_node_info(access_token: str, wiki_token: str) -> Optional[Dict]:
    """获取Wiki节点信息"""
    url = f"{FEISHU_BASE_URL}/wiki/v2/spaces/get_node"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"token": wiki_token}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        data = resp.json()

        if data.get("code") == 0:
            return data.get("data", {}).get("node", {})
        else:
            print(f"获取Wiki节点信息失败: {data.get('msg')}")
    except Exception as e:
        print(f"获取Wiki节点信息异常: {e}")

    return None


def get_doc_blocks(token: str, doc_id: str) -> List[Dict]:
    """获取文档所有blocks"""
    all_blocks = []
    page_token = None
    headers = {"Authorization": f"Bearer {token}"}

    while True:
        url = f"{FEISHU_BASE_URL}/docx/v1/documents/{doc_id}/blocks"
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            data = resp.json()

            if data.get("code") != 0:
                print(f"获取Blocks失败: {data.get('msg')}")
                break

            items = data.get("data", {}).get("items", [])
            all_blocks.extend(items)

            if data.get("data", {}).get("has_more"):
                page_token = data.get("data", {}).get("page_token")
            else:
                break

        except Exception as e:
            print(f"获取Blocks异常: {e}")
            break

    return all_blocks


def extract_text_from_elements(elements: List[Dict]) -> str:
    """从elements中提取文本"""
    texts = []
    for elem in elements:
        # 飞书elements结构: {"text_run": {...}} 或 {"mention": {...}}
        # 检查是哪种类型
        if "text_run" in elem:
            text_obj = elem.get("text_run", {})
            texts.append(text_obj.get("content", ""))
        elif "text" in elem:
            text_obj = elem.get("text", {})
            texts.append(text_obj.get("content", ""))
        elif "equation" in elem:
            texts.append(f"${elem.get('equation', {}).get('content', '')}$")
        elif "mention" in elem:
            texts.append(elem.get("mention", {}).get("title", ""))
        elif "mention_doc" in elem:
            texts.append(elem.get("mention_doc", {}).get("title", ""))
        elif "inline_block" in elem:
            # 嵌入块，保留引用
            texts.append("[嵌入内容]")
    return "".join(texts)


BLOCK_TYPE_MAP = {
    1: "page", 2: "text", 3: "heading1", 4: "heading2", 5: "heading3",
    6: "heading4", 7: "heading5", 8: "heading6", 9: "heading7",
    10: "heading8", 11: "heading9", 12: "text", 13: "bullet",
    14: "ordered", 15: "code", 16: "ordered", 17: "bullet",
    18: "divider", 19: "quote", 20: "table", 21: "table_row",
    22: "todo", 23: "todo", 24: "image", 25: "video",
    26: "doc", 27: "table", 28: "table_row", 29: "file",
    30: "pdf", 31: "date", 32: "callout", 33: "chat_card",
    34: "survey", 35: "agenda", 36: "OKR", 37: "OKR", 38: "OKR",
    39: "percent", 40: "metric", 41: "bitable", 42: "wiki_catalog",
    43: "templates", 44: "jira", 45: "github", 46: "galaxy",
    47: "loom", 48: "figma", 49: "miro", 50: "ideo",
    51: "gra", 52: "sheet", 53: "mindmap", 54: "storyboard",
    55: "sketch", 56: "tabs", 57: "tab", 58: "横向列表",
    59: "横向列表项", 60: "review", 61: "sticky", 62: "task",
    63: "unsplash", 64: "did", 65: "pay", 66: "vote",
    67: "gitee", 68: "gitlab", 69: "ext", 70: "view",
    71: "column_layout", 72: "column", 73: "board", 74: "board_column",
}


def get_block_content(block: Dict) -> str:
    """从block中获取对应类型的内容"""
    block_type = block.get("block_type", 0)
    field_name = BLOCK_TYPE_MAP.get(block_type, None)

    def get_text(content: Dict) -> str:
        if not content:
            return ""
        elements = content.get("elements", [])
        return extract_text_from_elements(elements)

    if field_name and field_name in block:
        content = block.get(field_name, {})
        if block_type in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
            return get_text(content)
        elif block_type in [13, 14, 16, 17]:
            return get_text(content)
        elif block_type == 19:
            return get_text(content)
        elif block_type == 24:
            token = content.get("token", "")
            return f"![图片](https://internal-api-drive-stream.feishu.cn/file/{token})"
        elif block_type == 15:
            elements = content.get("elements", [[]])
            code_text = extract_text_from_elements(elements[0] if elements else [])
            language = content.get("property", {}).get("language", "")
            return f"```{language}\n{code_text}\n```"
        elif block_type == 18:
            return "---\n"
        elif block_type == 41:
            return "[嵌入Bitable]"
        elif block_type == 42:
            wiki_token = content.get("wiki_token", "")
            return f"[Wiki目录](https://longcheer.feishu.cn/wiki/{wiki_token})"
        elif block_type == 52:
            return "[嵌入表格]"
        else:
            return get_text(content)

    return get_text(block.get("text", block.get("page", {})))


def block_to_markdown(block: Dict) -> str:
    """将单个block转换为Markdown"""
    block_type = block.get("block_type", 0)

    if block_type == 1:
        return f"# {get_block_content(block)}\n\n"
    elif block_type in [3, 4, 5, 6, 7, 8, 9, 10, 11]:
        prefix = "#" * (block_type - 2)
        return f"{prefix} {get_block_content(block)}\n\n"
    elif block_type == 2:
        return f"{get_block_content(block)}\n\n"
    elif block_type in [13, 17]:
        return f"- {get_block_content(block)}\n\n"
    elif block_type in [14, 16]:
        return f"1. {get_block_content(block)}\n\n"
    elif block_type == 15:
        return f"{get_block_content(block)}\n\n"
    elif block_type == 18:
        return "---\n\n"
    elif block_type == 19:
        return f"> {get_block_content(block)}\n\n"
    elif block_type == 24:
        return f"{get_block_content(block)}\n\n"
    elif block_type in [41, 42, 52]:
        return f"{get_block_content(block)}\n\n"
    else:
        content = get_block_content(block)
        if content:
            return f"{content}\n\n"
        return ""


def blocks_to_markdown(blocks: List[Dict]) -> str:
    """将blocks列表转换为完整Markdown"""
    return "".join(block_to_markdown(block) for block in blocks if block_to_markdown(block))


def sync_document():
    """同步飞书文档（支持多页面）"""
    print(f"开始同步 {len(WIKI_TOKENS)} 个 Wiki 文档")
    print(f"目标目录: {OUTPUT_DIR}")
    print("=" * 50)

    # 1. 获取 Token
    print("[1/4] 获取 Access Token...")
    token = get_tenant_access_token()
    if not token:
        print("获取Token失败，退出")
        return
    print(f"     Token获取成功")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    success_count = 0

    for wiki_token in WIKI_TOKENS:
        print(f"\n--- 同步: {wiki_token} ---")

        # 2. 获取 Wiki 节点信息
        print("[2/4] 获取 Wiki 节点信息...")
        node_info = get_wiki_node_info(token, wiki_token)
        if not node_info:
            print(f"     获取 Wiki 节点信息失败")
            continue

        doc_title = node_info.get("title", "飞书文档")
        obj_token = node_info.get("obj_token", "")
        obj_type = node_info.get("obj_type", "")

        print(f"     标题: {doc_title}")
        print(f"     类型: {obj_type}")

        if obj_type != "docx":
            print(f"     跳过非文档类型")
            continue

        # 3. 获取 Blocks
        print("[3/4] 获取文档内容...")
        blocks = get_doc_blocks(token, obj_token)
        print(f"     获取到 {len(blocks)} 个 blocks")

        if not blocks:
            print(f"     无内容，跳过")
            continue

        # 4. 保存文件
        print("[4/4] 保存文件...")
        md_content = blocks_to_markdown(blocks)
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', doc_title)
        output_file = os.path.join(OUTPUT_DIR, f"{safe_title}.md")

        header = f"""# {doc_title}

> 来源：https://longcheer.feishu.cn/wiki/{wiki_token}
> 同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(md_content)

        print(f"     已保存: {output_file}")
        success_count += 1

    print("\n" + "=" * 50)
    print(f"同步完成! 成功: {success_count}/{len(WIKI_TOKENS)}")


if __name__ == "__main__":
    try:
        sync_document()
    except Exception as e:
        print(f"同步失败: {e}")
        import traceback
        traceback.print_exc()
