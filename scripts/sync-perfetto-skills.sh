#!/bin/bash
# sync-perfetto-skills.sh - 将 .claude/skills/ 同步到 sidian-charter/skills/01-claude skills/
# 用法: ./sync-perfetto-skills.sh

set -e

SOURCE_DIR="C:/Users/nijiasheng1/.claude/skills"
TARGET_DIR="D:/sidian-charter/skills/01-claude-skills"
INDEX_FILE="D:/sidian-charter/skills/00-Skill Index.md"
SCRIPTS_DIR="D:/sidian-charter/scripts"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}开始同步 Perfetto Skills...${NC}"

# 1. 创建目标目录（如果不存在）
mkdir -p "$TARGET_DIR"

# 2. 删除镜像副本目录（会导致混淆）
DUPLICATE_DIR="$TARGET_DIR/skills"
if [ -d "$DUPLICATE_DIR" ]; then
    echo -e "${YELLOW}删除镜像副本目录: $DUPLICATE_DIR${NC}"
    rm -rf "$DUPLICATE_DIR"
fi

# 3. 同步 skills（rsync 风格：复制并删除目标端多余文件）
# 先删除目标中不在源里的目录
for dir in "$TARGET_DIR"/*/; do
    if [ -d "$dir" ]; then
        name=$(basename "$dir")
        if [ ! -d "$SOURCE_DIR/$name" ]; then
            echo -e "${YELLOW}删除不存在于源端的目录: $name${NC}"
            rm -rf "$dir"
        fi
    fi
done

# 复制源端到目标端
for skill_dir in "$SOURCE_DIR"/*/; do
    if [ -d "$skill_dir" ]; then
        name=$(basename "$skill_dir")
        echo -e "${GREEN}同步: $name${NC}"
        rm -rf "$TARGET_DIR/$name"
        cp -r "$skill_dir" "$TARGET_DIR/$name"
    fi
done

echo -e "${GREEN}✓ 同步完成${NC}"

# 4. 更新索引（调用 Python 版）
if [ -f "$SCRIPTS_DIR/update-skill-index.py" ]; then
    echo -e "${GREEN}更新 Skill Index...${NC}"
    python "$SCRIPTS_DIR/update-skill-index.py"
else
    echo -e "${YELLOW}警告: update-skill-index.py 不存在${NC}"
fi

echo -e "${GREEN}✓ 全部完成${NC}"
