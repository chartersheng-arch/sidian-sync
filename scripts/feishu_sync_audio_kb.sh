#!/bin/bash
# 飞书文档同步脚本 - 展锐Audio知识库
# 目标：wikcnNLquxHPG9FuAlPPJSjWIwg

# 配置
APP_ID="cli_a95df12efebb5cb1"
APP_SECRET="7he9IYCwNoy34ntRs1WSvdZrIN1Z6N28"
DOC_TOKEN="wikcnNLquxHPG9FuAlPPJSjWIwg"
OUTPUT_DIR="D:/sidian-charter/andriod/audio知识"

# 获取 Tenant Access Token
echo "[1/4] 获取 Access Token..."
TOKEN_RESP=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\": \"$APP_ID\", \"app_secret\": \"$APP_SECRET\"}")

TOKEN=$(echo $TOKEN_RESP | grep -o '"tenant_access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "获取Token失败: $TOKEN_RESP"
  exit 1
fi
echo "Token获取成功"

# 获取文档元信息
echo "[2/4] 获取文档元信息..."
META_RESP=$(curl -s -X GET "https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token=$DOC_TOKEN" \
  -H "Authorization: Bearer $TOKEN")

echo "$META_RESP" | grep -o '"title":"[^"]*"' || echo "获取标题失败，使用默认标题"

# 获取文档内容 (Markdown格式)
echo "[3/4] 获取文档内容..."
CONTENT_RESP=$(curl -s -X GET "https://open.feishu.cn/open-apis/doc/v2/docs/$DOC_TOKEN" \
  -H "Authorization: Bearer $TOKEN")

# 使用 wiki blocks API 获取更完整内容
echo "[4/4] 获取Blocks内容并转换..."
BLOCKS_RESP=$(curl -s -X GET "https://open.feishu.cn/open-apis/doc/v1/documents/$DOC_TOKEN/blocks?page_size=500" \
  -H "Authorization: Bearer $TOKEN")

# 提取 title
DOC_TITLE=$(echo $META_RESP | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$DOC_TITLE" ]; then
  DOC_TITLE="展锐Audio知识库"
fi

# 输出文件
OUTPUT_FILE="$OUTPUT_DIR/${DOC_TITLE}.md"

# 写入文件头
cat > "$OUTPUT_FILE" << EOF
# $DOC_TITLE

> 来源：https://longcheer.feishu.cn/wiki/$DOC_TOKEN
> 同步时间：$(date '+%Y-%m-%d %H:%M')

---

EOF

echo "文档已保存到: $OUTPUT_FILE"
echo ""
echo "注意: 如需完整Markdown转换，建议使用 @feishu/docx-sdk 或直接使用飞书开放平台导出功能"
