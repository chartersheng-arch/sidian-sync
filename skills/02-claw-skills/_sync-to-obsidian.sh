#!/bin/bash
# 同步 OpenClaw skills 到 Obsidian 资料库
# 用法: bash _sync-to-obsidian.sh

OWNCLOWS="/mnt/e/AIopen/openclaws/skills"
SKILLS_DIR="/mnt/e/AIopen/sidian-charter/skills"
INDEX="$SKILLS_DIR/Skill Index.md"

# 中文描述映射
declare -A cn_desc=(
  ["agent-browser-clawdbot"]="无头浏览器自动化，支持 accessibility tree 快照和元素定位"
  ["agent-reach"]="Agent reach 自动化工具"
  ["bibigpt-skill"]="BibiGPT 内容总结，提取视频/音频/文章要点"
  ["cloudflare-deploy"]="部署应用到 Cloudflare Workers 和 Pages"
  ["develop-web-game"]="网页游戏开发，Codex 迭代 + Playwright 测试"
  ["doc"]="Word .docx 文档阅读与编辑"
  ["excel-xlsx"]="Excel .xlsx 读写、公式、格式化、模板填充"
  ["feishu-messaging"]="飞书消息收发，支持文本、富媒体、卡片"
  ["find-skills-skill"]="搜索 ClawHub 安装新 skill"
  ["frontend"]="React/Next.js 前端开发，构建页面和组件"
  ["frontend_design"]="高质量 UI 界面设计，生成精美前端代码"
  ["github"]="GitHub 操作，管理 issues/PR/CI runs"
  ["gog"]="Google Workspace CLI，Gmail/Drive/Calendar/Sheets/Docs"
  ["memory-setup"]="OpenClaw 长期记忆配置，MEMORY.md 和向量搜索"
  ["minimax-tts-cn"]="MiniMax 语音合成，文字转语音 / 声音克隆"
  ["multi-search-engine"]="16 搜索引擎聚合搜索（7 国内 + 9 海外）"
  ["obsidian"]="Obsidian 笔记库操作，自动化笔记管理"
  ["pdf"]="PDF 阅读、创建、可视化渲染检查"
  ["react-best-practices"]="React 性能优化指南，Vercel 工程实践"
  ["react-best-practices-2"]="React 18+ 架构、Hooks、状态管理优化"
  ["react-expert"]="React 18+ 全面指南，Server Components 和新特性"
  ["remotion-video-toolkit"]="程序化视频制作，Remotion + React 动画"
  ["seedance-2-prompt-engineering-skill"]="Seedance 2.0 提示词工程技巧"
  ["seedance-2-video-gen"]="Seedance 2.0 文生视频、图生视频"
  ["skill-creator"]="创建新的 OpenClaw skill"
  ["skill-vetter"]="安装前安全审查，排查风险和权限问题"
  ["spreadsheet"]="CSV/TSV 表格处理，数据分析和格式化"
  ["summarize-pro"]="内容总结，本地处理不调用外部 API"
  ["tavily"]="网页搜索，获取最新信息和来源"
  ["using-superpowers"]="OpenClaw skill 使用指南"
  ["weather"]="天气查询，当前天气和预报"
  ["web-design-guidelines"]="UI/UX 设计规范审查和可访问性检查"
  ["word-docx"]="Word 文档处理和生成"
  ["xiucheng-self-improving-agent"]="自我优化分析，持续改进对话策略"
)

# 分类映射
declare -A cats=(
  ["find-skills-skill"]="🔍 搜索" ["skill-vetter"]="🔍 搜索" ["tavily"]="🔍 搜索"
  ["multi-search-engine"]="🔍 搜索" ["summarize-pro"]="🔍 搜索"
  ["weather"]="🌤️ 工具" ["using-superpowers"]="⚡ 引导"
  ["doc"]="📁 文档" ["pdf"]="📁 文档" ["excel-xlsx"]="📁 文档"
  ["spreadsheet"]="📁 文档" ["word-docx"]="📁 文档" ["obsidian"]="📁 文档"
  ["frontend"]="💻 前端" ["frontend_design"]="💻 前端"
  ["react-best-practices"]="💻 前端" ["react-best-practices-2"]="💻 前端"
  ["react-expert"]="💻 前端" ["web-design-guidelines"]="💻 前端" ["develop-web-game"]="💻 前端"
  ["agent-reach"]="🤖 AI/Agent" ["agent-browser-clawdbot"]="🤖 AI/Agent"
  ["xiucheng-self-improving-agent"]="🤖 AI/Agent" ["bibigpt-skill"]="🤖 AI/Agent"
  ["cloudflare-deploy"]="☁️ 部署"
  ["remotion-video-toolkit"]="🎬 媒体" ["seedance-2-video-gen"]="🎬 媒体"
  ["seedance-2-prompt-engineering-skill"]="🎬 媒体" ["minimax-tts-cn"]="🎬 媒体"
  ["github"]="📱 平台" ["feishu-messaging"]="📱 平台" ["gog"]="📱 平台"
  ["memory-setup"]="🧠 记忆" ["skill-creator"]="🔒 安全"
)

cat_order=("🔍 搜索" "🌤️ 工具" "⚡ 引导" "📁 文档" "💻 前端" "🤖 AI/Agent" "🎬 媒体" "☁️ 部署" "📱 平台" "🧠 记忆" "🔒 安全")

# 排除同步脚本自身
total=$(ls "$OWNCLOWS" | grep -v "^_sync-to-obsidian.sh$" | wc -l)

declare -A cat_members
for name in $(ls "$OWNCLOWS" | grep -v "^_sync-to-obsidian.sh$" | sort); do
  cat="${cats[$name]:-🔧 其他}"
  cat_members["$cat"]+=" [[$name]]"
done

# 写入索引
{
  echo "---"
  echo "uid: skill-index"
  echo "created: 2026-04-12"
  echo "tags: [skill, index]"
  echo "---"
  echo ""
  echo "# Skill 索引"
  echo ""
  echo "> 共 **$total** 个 skill | 由守岸人同步"
  echo ""
  echo "---"
  echo ""
  echo "## 📋 Skill 总表"
  echo ""
  echo "| Skill | 分类 | 功能 |"
  echo "|-------|------|------|"
  for name in $(ls "$OWNCLOWS" | grep -v "^_sync-to-obsidian.sh$" | sort); do
    cat="${cats[$name]:-🔧 其他}"
    desc="${cn_desc[$name]:-（无描述）}"
    echo "| [[$name]] | $cat | $desc |"
  done
  echo ""
  echo "---"
  echo ""
  echo "## 📂 分类导航"
  echo ""
  for cat in "${cat_order[@]}"; do
    members="${cat_members[$cat]}"
    if [ -n "$members" ]; then
      echo "### $cat"
      echo "$members" | sed 's/^ //' | fold -s -w 120
      echo ""
    fi
  done
  echo "---"
  echo "_由守岸人同步于 $(date +%Y-%m-%d_%H:%M)_"
} > "$INDEX"

echo "同步完成: $total skills → $INDEX"
