#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用百度翻译 API 翻译 skill description 为中文"""
import os
import re
import sys
import hashlib
import urllib.parse
import urllib.request
import json
import random
import time

sys.stdout.reconfigure(encoding='utf-8')

# 百度翻译 API 配置
APP_ID = "20260417002596316"
SECRET_KEY = "QyqyuqU8RIJ5eCEFGtyn"

SKILLS_DIR = "D:/sidian-charter/skills/01-claude-skills"
INDEX_FILE = "D:/sidian-charter/skills/00-Skill Index.md"

def translate_text(text):
    """翻译文本（百度翻译 API）"""
    if not text or len(text.strip()) < 5:
        return text

    try:
        time.sleep(1.1)  # 百度翻译API限制每秒1次
        salt = str(random.randint(1000000000, 9999999999))
        q = text[:2000]  # 截断到合理长度
        sign_str = APP_ID + q + salt + SECRET_KEY
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

        params = {
            'q': q,
            'from': 'en',
            'to': 'zh',
            'appid': APP_ID,
            'salt': salt,
            'sign': sign
        }

        data = urllib.parse.urlencode(params).encode('utf-8')
        url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))

        if 'trans_result' in result and len(result['trans_result']) > 0:
            return result['trans_result'][0]['dst']
        elif 'error_code' in result:
            print(f"  API错误: {result.get('error_code')} - {result.get('error_msg', '')}")
            return text
        else:
            return text
    except Exception as e:
        print(f"  翻译失败: {e}")
        return text

def get_skill_descriptions():
    """从 SKILL.md 提取 description"""
    descriptions = {}
    if not os.path.exists(SKILLS_DIR):
        return descriptions

    for skill_name in os.listdir(SKILLS_DIR):
        skill_path = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_path):
            continue

        skill_md = os.path.join(skill_path, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            for line in content.split('\n'):
                if line.strip().startswith('description:'):
                    desc = line.split('description:', 1)[1].strip()
                    desc = desc.strip('"').strip("'").strip()
                    descriptions[skill_name] = desc
                    break
        except Exception as e:
            print(f"  读取 {skill_name} 失败: {e}")
    return descriptions

def is_chinese(text):
    """检查是否包含中文"""
    return any('\u4e00' <= c <= '\u9fff' for c in text)

def translate_index():
    """翻译索引文件"""
    descriptions = get_skill_descriptions()
    print(f"找到 {len(descriptions)} 个 skills，开始翻译...")

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    translated_count = 0

    lines = content.split('\n')
    new_lines = []

    for line in lines:
        match = re.search(r'(\[\[skills/01-claude-skills/([^/]+)/SKILL\.md\\\|([^]]+)\]\])', line)
        if match:
            skill_name = match.group(2)
            if skill_name in descriptions:
                en_desc = descriptions[skill_name]
                if en_desc and not is_chinese(en_desc):
                    zh_desc = translate_text(en_desc)
                    print(f"  {skill_name}: {zh_desc}")

                    parts = line.rsplit(' | ', 1)
                    if len(parts) == 2:
                        line = parts[0] + ' | ' + zh_desc
                        translated_count += 1

        new_lines.append(line)

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"\n翻译完成！共翻译 {translated_count} 个 skills")

if __name__ == "__main__":
    translate_index()
