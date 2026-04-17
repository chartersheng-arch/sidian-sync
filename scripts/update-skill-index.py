# -*- coding: utf-8 -*-
"""更新 Skill Index - 保留已有类型和中文说明"""
import os
import re
import sys

SKILLS_DIR = "D:/sidian-charter/skills/01-claude-skills"
INDEX_FILE = "D:/sidian-charter/skills/00-Skill Index.md"

def get_description(skill_md_path):
    """从 SKILL.md 提取 description"""
    try:
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for line in content.split('\n'):
            if line.strip().startswith('description:'):
                desc = line.split('description:', 1)[1].strip()
                desc = desc.strip('"').strip("'").strip()
                if desc and len(desc) > 3:
                    if len(desc) > 80:
                        return desc[:77] + "..."
                    return desc
    except:
        pass
    return ""

def has_chinese(text):
    return any('\u4e00' <= c <= '\u9fff' for c in text)

def parse_existing_index():
    """解析现有索引，提取已有类型和中文说明"""
    types = {}
    descs = {}

    if not os.path.exists(INDEX_FILE):
        return types, descs

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配行: | [[skills/01-claude-skills/NAME/SKILL.md|NAME]] | TYPE | DESC |
    pattern = r'\[\[skills/01-claude-skills/([^/]+)/SKILL\.md\\\|([^\]]+)\]\]'
    for match in re.finditer(pattern, content):
        name = match.group(1)

        # 找到该 wikilink 所在行的完整内容
        line_start = content.rfind('\n', 0, match.start()) + 1
        line_end = content.find('\n', match.end())
        if line_end == -1:
            line_end = len(content)
        line = content[line_start:line_end]

        # 分割表格列（处理转义的 |）
        parts = []
        current = ""
        i = 0
        while i < len(line):
            if i < len(line) - 1 and line[i:i+2] == '\\|':
                current += '|'
                i += 2
            elif line[i] == '|':
                parts.append(current.strip())
                current = ""
                i += 1
            else:
                current += line[i]
                i += 1

        if len(parts) >= 3:
            type_val = parts[1].strip()
            desc_val = parts[2].strip()
            if type_val:
                types[name] = type_val
            if has_chinese(desc_val) and desc_val:
                descs[name] = desc_val

    return types, descs

def generate_index():
    """生成新索引"""
    existing_types, existing_descs = parse_existing_index()
    print(f"检测到已有类型: {len(existing_types)} 个")
    print(f"检测到已有中文说明: {len(existing_descs)} 个")

    lines = []
    lines.append("# Skill Index")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🤖 Claude Code Skills")
    lines.append("")
    lines.append("> 来源：`skills/01-claude-skills/`（Obsidian vault 内）")
    lines.append("")
    lines.append("| 名称 | 类型 | 说明 |")
    lines.append("|------|--------|------|")

    count = 0
    for skill_name in sorted(os.listdir(SKILLS_DIR)):
        skill_path = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_path):
            continue
        if skill_name.startswith('.'):
            continue

        skill_md = os.path.join(skill_path, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue

        desc = get_description(skill_md)

        # 优先使用已有的中文说明
        if skill_name in existing_descs:
            desc = existing_descs[skill_name]
        elif not desc or len(desc) < 5:
            desc = skill_name

        # 获取类型
        skill_type = existing_types.get(skill_name, "")

        # 生成行
        line = f"| [[skills/01-claude-skills/{skill_name}/SKILL.md\\|{skill_name}]] | {skill_type} | {desc} |"
        lines.append(line)
        count += 1

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*自动生成于 2026-04-17*")

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"[OK] 索引已更新: {INDEX_FILE}")
    print(f"  共 {count} 个 skills")
    print(f"  保留已有类型: {len(existing_types)} 个")
    print(f"  保留已有中文说明: {len(existing_descs)} 个")

if __name__ == "__main__":
    generate_index()
