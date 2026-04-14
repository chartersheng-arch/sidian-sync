# Claude Skills 同步脚本
# 功能：同步本地 skills 到 Obsidian 仓库，并自动更新索引

param(
    [switch]$DryRun,      # 模拟运行，不实际执行
    [switch]$SkipIndex    # 跳过索引更新
)

$ErrorActionPreference = "Stop"

# 路径配置
$SourceDir = "C:\Users\nijiasheng1\.claude\skills"
$DestDir = "D:\sidian-charter\claude skills"
$IndexFile = "$DestDir\00 - Skills Index.md"

# 颜色输出
function Write-Step { param($msg) Write-Host "[同步] $msg" -ForegroundColor Cyan }
function Write-Done { param($msg) Write-Host "[完成] $msg" -ForegroundColor Green }
function Write-Skip { param($msg) Write-Host "[跳过] $msg" -ForegroundColor Yellow }

# ========== Step 1: 同步文件 ==========
Write-Step "开始同步 SKILL.md 文件..."

# 获取源目录所有 skill 目录
$SourceSkills = Get-ChildItem -Path $SourceDir -Directory | Where-Object { $_.Name -notmatch "^superpowers" }
$SyncCount = 0
$SkipCount = 0

foreach ($skill in $SourceSkills) {
    $SKILLMD = $skill.FullName + "\SKILL.md"

    if (-not (Test-Path $SKILLMD)) {
        Write-Skip "$($skill.Name) - 无 SKILL.md"
        $SkipCount++
        continue
    }

    $DestFile = "$DestDir\$($skill.Name).md"

    # 检查是否需要更新（比较修改时间）
    $NeedUpdate = $true
    if (Test-Path $DestFile) {
        $SourceTime = (Get-Item $SKILLMD).LastWriteTime
        $DestTime = (Get-Item $DestFile).LastWriteTime
        if ($SourceTime -le $DestTime) {
            $NeedUpdate = $false
            Write-Skip "$($skill.Name) - 无需更新"
            $SkipCount++
        }
    }

    if ($NeedUpdate) {
        if ($DryRun) {
            Write-Host "[DryRun] 将复制: $($skill.Name)" -ForegroundColor Magenta
        } else {
            Copy-Item -Path $SKILLMD -Destination $DestFile -Force
            Write-Host "[复制] $($skill.Name)" -ForegroundColor Green
        }
        $SyncCount++
    }
}

Write-Done "同步完成: $SyncCount 个文件更新, $SkipCount 个跳过"

# ========== Step 2: 更新索引 ==========
if ($SkipIndex) {
    Write-Step "已跳过索引更新"
} else {
    Write-Step "更新索引文件..."

    # 收集所有 skill 信息
    $Skills = @()
    $DestSkills = Get-ChildItem -Path $DestDir -Filter "*.md" | Where-Object { $_.Name -ne "00 - Skills Index.md" }

    foreach ($file in $DestSkills) {
        $name = $file.BaseName
        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue

        # 提取 description
        if ($content -match '(?s)description:\s*\|?\s*\n?(.*?)(?=\n---|\n#)') {
            $desc = $matches[1] -replace '\s+', ' ' -replace '\n', ' ' -replace '\|', '' | ForEach-Object { $_.Trim() }
        } else {
            $desc = "（无描述）"
        }

        # 简单分类（基于名称关键字）
        $category = "其他"
        if ($name -match "perfetto|hz-perfetto") { $category = "Perfetto" }
        elseif ($name -match "obsidian") { $category = "Obsidian" }
        elseif ($name -match "prd|planning") { $category = "PRD" }
        elseif ($name -match "git|commit|create-pr") { $category = "Git" }
        elseif ($name -match "test|qa") { $category = "测试" }
        elseif ($name -match "doc|report") { $category = "文档" }
        elseif ($name -match "ppt|skywork") { $category = "PPT" }
        elseif ($name -match "translate|context") { $category = "翻译/中文" }
        elseif ($name -match "api") { $category = "API" }
        elseif ($name -match "skill|meta") { $category = "元技能" }
        elseif ($name -match "browser|agent") { $category = "自动化" }
        elseif ($name -match "debug|perf|security|refactor") { $category = "开发" }

        $Skills += [PSCustomObject]@{
            Name = $name
            Description = $desc.Substring(0, [Math]::Min(60, $desc.Length))
            Category = $category
        }
    }

    # 按名称排序
    $Skills = $Skills | Sort-Object Name

    # 生成索引内容
    $IndexContent = @"
# Claude Skills 知识库索引

> 本库收录本地 Claude Code 全部 skills 的内容与功能简述。
> 自动同步于 $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

---

## Skills 总览表

| 序号 | 技能名称 | 分类 | 功能简述 |
| :-: | ---------------------------------------- | ----------- | ------------------------------- |
$($Skills | ForEach-Object { $i = [array]::IndexOf($Skills, $_) + 1; "| $i | [[$($_.Name)]] | $($_.Category) | $($_.Description) |" } | Out-String)

---

## 按分类索引

### 🔧 开发技能
$((($Skills | Where-Object { $_.Category -eq "开发" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 🎨 设计
$((($Skills | Where-Object { $_.Category -eq "设计" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 📐 架构与 DevOps
$((($Skills | Where-Object { $_.Category -eq "API" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 📋 PRD 与规划
$((($Skills | Where-Object { $_.Category -eq "PRD" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 📚 文档与报告
$((($Skills | Where-Object { $_.Category -eq "文档" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 🧪 测试与 QA
$((($Skills | Where-Object { $_.Category -eq "测试" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 🧠 Perfetto 性能分析
$((($Skills | Where-Object { $_.Category -eq "Perfetto" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 💬 Obsidian 知识管理
$((($Skills | Where-Object { $_.Category -eq "Obsidian" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 🌐 工具类
$((($Skills | Where-Object { $_.Category -eq "自动化" -or $_.Category -eq "PPT" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 🔄 Git 工作流
$((($Skills | Where-Object { $_.Category -eq "Git" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 🀄 翻译与中文
$((($Skills | Where-Object { $_.Category -eq "翻译/中文" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

### 📦 Meta 技能
$((($Skills | Where-Object { $_.Category -eq "元技能" }).Name | ForEach-Object { "[[$_]]" }) -join " · ")

---

## 同步信息

| 项目 | 值 |
| ---- | - |
| **同步日期** | $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") |
| **Skill 总数** | $($Skills.Count) |
| **源路径** | $SourceDir |
| **目标路径** | $DestDir |
"@

    if ($DryRun) {
        Write-Host "[DryRun] 将更新索引文件" -ForegroundColor Magenta
    } else {
        $IndexContent | Out-File -FilePath $IndexFile -Encoding UTF8 -Force
        Write-Done "索引已更新: $($Skills.Count) 个 skills"
    }
}

Write-Host ""
Write-Host "========== 同步完成 ==========" -ForegroundColor Green
if ($DryRun) {
    Write-Host "(DryRun 模式，未实际执行)" -ForegroundColor Yellow
}
