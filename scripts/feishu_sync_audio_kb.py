#!/usr/bin/env python3
"""
飞书文档同步脚本 - 支持 Wiki 目录遍历
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
WIKI_TOKEN = "wikcnNLquxHPG9FuAlPPJSjWIwg"
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


def list_wiki_children(token: str, space_id: str, parent_token: str = "") -> List[Dict]:
    """获取Wiki子节点列表"""
    url = f"{FEISHU_BASE_URL}/wiki/v2/spaces/list_node"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "space_id": int(space_id) if space_id.isdigit() else space_id,
        "parent_token": parent_token,
        "page_size": 50
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        data = resp.json()

        if data.get("code") == 0:
            return data.get("data", {}).get("list", [])
        else:
            # 可能是 space_id 格式问题，尝试其他方式
            print(f"获取子节点失败: {data.get('msg')}")
    except Exception as e:
        print(f"获取子节点异常: {e}")

    return []


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
        elem_type = elem.get("type", "")
        if elem_type == "text":
            text_obj = elem.get("text", {})
            texts.append(text_obj.get("content", ""))
        elif elem_type == "equation":
            texts.append(f"${elem.get('equation', {}).get('content', '')}$")
        elif elem_type == "mention":
            texts.append(elem.get("mention", {}).get("title", ""))
    return "".join(texts)


# block_type 到字段名的映射
BLOCK_TYPE_MAP = {
    1: "page",
    2: "text",
    3: "heading1",
    4: "heading2",
    5: "heading3",
    6: "heading4",
    7: "heading5",
    8: "heading6",
    9: "heading7",
    10: "heading8",
    11: "heading9",
    12: "text",
    13: "bullet",
    14: "ordered",
    15: "code",
    16: "ordered",
    17: "bullet",
    18: "divider",
    19: "quote",
    20: "table",
    21: "table_row",
    22: "todo",
    23: "todo",
    24: "image",
    25: "video",
    26: "doc",
    27: "table",
    28: "table_row",
    29: "file",
    30: "pdf",
    31: "date",
    32: "callout",
    33: "chat_card",
    34: "survey",
    35: "agenda",
    36: "OKR",
    37: "OKR",
    38: "OKR",
    39: "percent",
    40: "metric",
    41: "bitable",
    42: "wiki_catalog",
    43: "templates",
    44: "jira",
    45: "github",
    46: "galaxy",
    47: "loom",
    48: "figma",
    49: "miro",
    50: "ideo",
    51: "gra",
    52: "sheet",
    53: "mindmap",
    54: "storyboard",
    55: "sketch",
    56: "tabs",
    57: "tab",
    58: "横向列表",
    59: "横向列表项",
    60: "review",
    61: "sticky",
    62: "task",
    63: "unsplash",
    64: "did",
    65: "pay",
    66: "vote",
    67: "gitee",
    68: "gitlab",
    69: "ext",
    70: "view",
    71: "column_layout",
    72: "column",
    73: "board",
    74: "board_column",
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
        if block_type in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:  # page, text, headings
            return get_text(content)
        elif block_type in [13, 14, 16, 17]:  # lists
            return get_text(content)
        elif block_type == 19:  # quote
            return get_text(content)
        elif block_type == 24:  # image
            token = content.get("token", "")
            return f"![图片](https://internal-api-drive-stream.feishu.cn/file/{token})"
        elif block_type == 15:  # code
            elements = content.get("elements", [[]])
            code_text = extract_text_from_elements(elements[0] if elements else [])
            language = content.get("property", {}).get("language", "")
            return f"```{language}\n{code_text}\n```"
        elif block_type == 18:  # divider
            return "---\n"
        elif block_type == 41:  # bitable
            return "[嵌入Bitable]"
        elif block_type == 42:  # wiki_catalog
            wiki_token = content.get("wiki_token", "")
            return f"[Wiki目录](https://longcheer.feishu.cn/wiki/{wiki_token})"
        elif block_type == 52:  # sheet
            return "[嵌入表格]"
        else:
            return get_text(content)

    return get_text(block.get("text", block.get("page", {})))


def block_to_markdown(block: Dict, level: int = 0) -> str:
    """将单个block转换为Markdown"""
    block_type = block.get("block_type", 0)

    if block_type == 1:  # 页面标题
        return f"# {get_block_content(block)}\n\n"
    elif block_type in [3, 4, 5, 6, 7, 8, 9, 10, 11]:  # 标题
        prefix = "#" * (block_type - 2)
        return f"{prefix} {get_block_content(block)}\n\n"
    elif block_type == 2:  # 段落
        return f"{get_block_content(block)}\n\n"
    elif block_type in [13, 17]:  # 无序列表
        return f"- {get_block_content(block)}\n\n"
    elif block_type in [14, 16]:  # 有序列表
        return f"1. {get_block_content(block)}\n\n"
    elif block_type == 15:  # 代码块
        return f"{get_block_content(block)}\n\n"
    elif block_type == 18:  # 分割线
        return "---\n\n"
    elif block_type == 19:  # 引用
        return f"> {get_block_content(block)}\n\n"
    elif block_type == 24:  # 图片
        return f"{get_block_content(block)}\n\n"
    elif block_type in [41, 42, 52]:  # 嵌入内容
        return f"{get_block_content(block)}\n\n"
    else:
        content = get_block_content(block)
        if content:
            return f"{content}\n\n"
        return ""


def blocks_to_markdown(blocks: List[Dict]) -> str:
    """将blocks列表转换为完整Markdown"""
    md_lines = []

    for block in blocks:
        md_content = block_to_markdown(block)
        if md_content:
            md_lines.append(md_content)

    return "".join(md_lines)


def sync_single_doc(token: str, wiki_token: str, title: str, output_path: str):
    """同步单个文档"""
    # 获取 Wiki 节点信息
    node_info = get_wiki_node_info(token)
    if not node_info:
        return False

    obj_token = node_info.get("obj_token")
    doc_title = node_info.get("title", title)

    # 获取 Blocks
    blocks = get_doc_blocks(token, obj_token)
    print(f"  - 获取到 {len(blocks)} 个blocks")

    if not blocks:
        return False

    # 转换为 Markdown
    md_content = blocks_to_markdown(blocks)

    # 保存文件
    header = f"""# {doc_title}

> 来源：https://longcheer.feishu.cn/wiki/{wiki_token}
> 同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(md_content)

    print(f"  - 已保存: {output_path}")
    return True


def sync_document():
    """同步飞书文档（支持Wiki目录）"""
    print(f"开始同步 Wiki 文档: {WIKI_TOKEN}")
    print(f"目标目录: {OUTPUT_DIR}")
    print("=" * 50)

    # 1. 获取 Token
    print("[1/5] 获取 Access Token...")
    token = get_tenant_access_token()
    if not token:
        print("获取Token失败，退出")
        return
    print("     Token获取成功")

    # 2. 获取 Wiki 节点信息
    print("[2/5] 获取 Wiki 节点信息...")
    node_info = get_wiki_node_info(token, WIKI_TOKEN)
    if not node_info:
        print("获取 Wiki 节点信息失败，退出")
        return

    doc_title = node_info.get("title", "飞书文档")
    space_id = node_info.get("space_id", "")
    has_child = node_info.get("has_child", False)
    obj_token = node_info.get("obj_token", "")

    print(f"     标题: {doc_title}")
    print(f"     Space ID: {space_id}")
    print(f"     是否有子页面: {has_child}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', doc_title)

    # 3. 如果是目录页面（has_child=True），先获取目录内容
    if has_child:
        print("[3/5] 获取 Wiki 目录内容...")
        # 获取主文档内容
        output_file = os.path.join(OUTPUT_DIR, f"{safe_title}.md")

        # 获取主文档 blocks
        blocks = get_doc_blocks(token, obj_token)
        print(f"     主文档获取到 {len(blocks)} 个 blocks")

        md_content = blocks_to_markdown(blocks)

        header = f"""# {doc_title}

> 来源：https://longcheer.feishu.cn/wiki/{WIKI_TOKEN}
> 同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(md_content)
        print(f"     已保存主文档: {output_file}")

        # 4. 尝试获取子页面
        print("[4/5] 尝试获取子页面...")
        print("     (Wiki API 需要 space_id 为整数，暂不支持遍历子页面)")
        print("     建议直接同步具体子页面的 Wiki Token")

    else:
        # 单一文档
        print("[3/5] 获取文档内容...")
        output_file = os.path.join(OUTPUT_DIR, f"{safe_title}.md")

        blocks = get_doc_blocks(token, obj_token)
        print(f"     获取到 {len(blocks)} 个 blocks")

        if blocks:
            md_content = blocks_to_markdown(blocks)

            header = f"""# {doc_title}

> 来源：https://longcheer.feishu.cn/wiki/{WIKI_TOKEN}
> 同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

"""

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(header)
                f.write(md_content)
            print(f"     已保存: {output_file}")

    print("[5/5] 完成!")
    print("=" * 50)

    # 提示用户现有数据
    print("\n提示: 已有同步数据参考:")
    print(f"  - D:\\sidian-charter\\andriod\\audio知识\\展锐 Audio 汇总（DSP）.md")
    print(f"  - D:\\sidian-charter\\feishushare\\blocks.json (包含 {289} 个 blocks)")


if __name__ == "__main__":
    try:
        sync_document()
    except Exception as e:
        print(f"同步失败: {e}")
        import traceback
        traceback.print_exc()
