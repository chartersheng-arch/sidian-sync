# Claude Skills 知识库索引

> 本库收录本地 Claude Code 全部 skills 的内容与功能简述。

---

## Skills 总览表

| 序号  | 技能名称                                     | 分类          | 功能简述                            |
| :-: | ---------------------------------------- | ----------- | ------------------------------- |
|  1  | [[agent-browser]]                        | 自动化         | 浏览器自动化 CLI，支持网页交互、表单填写、截图等      |
|  2  | [[api-designer]]                         | API设计       | REST/GraphQL API 架构设计专家         |
|  3  | [[api-documenter]]                       | 文档          | OpenAPI/Swagger 规范文档生成          |
|  4  | [[architecting-solutions]]               | 架构          | 技术方案设计与 PRD 文档创建                |
|  5  | [[auto-trigger]]                         | 自动化         | Skill 间自动触发钩子配置                 |
|  6  | [[code-reviewer]]                        | 代码质量        | PR 与代码变更的全面审查                   |
|  7  | [[commit-helper]]                        | Git         | Conventional Commits 规范提交信息撰写   |
|  8  | [[context-ZH]]                           | 中文          | 中文语境增强，专业术语保留与语义优化              |
|  9  | [[create-pr]]                            | Git         | 双语文档自动同步的 PR 创建流程               |
| 10  | [[defuddle]]                             | 工具          | 网页内容提取，生成干净 Markdown            |
| 11  | [[debugger]]                             | 调试          | 系统性诊断与修复代码错误                    |
| 12  | [[deployment-engineer]]                  | DevOps      | CI/CD 流水线与部署自动化                 |
| 13  | [[documentation-engineer]]               | 文档          | README、技术文档编写专家                 |
| 14  | [[feishudoc-skill]]                      | 文档          | 飞书 Audio 类需求文档格式规范              |
| 15  | [[figma-designer]]                       | 设计          | Figma 设计分析与可视化规格 PRD 生成         |
| 16  | [[find-skills]]                          | 元技能         | 发现和安装 agent skills              |
| 17  | [[hz-perfetto-debug]]                    | VR/Perfetto | Meta Quest VR 性能调试（帧时间/CPU/GPU） |
| 18  | [[json-canvas]]                          | Obsidian    | JSON Canvas 文件创建与编辑             |
| 19  | [[long-task-coordinator]]                | 编排          | 多会话、长任务状态持久化与恢复                 |
| 20  | [[obsidian-bases]]                       | Obsidian    | Obsidian Bases 数据库视图            |
| 21  | [[obsidian-charter]]                     | 知识管理        | Obsidian 仓库连接与操作                |
| 22  | [[obsidian-cli]]                         | Obsidian    | Obsidian CLI 命令行工具              |
| 23  | [[obsidian-markdown]]                    | Obsidian    | Obsidian 风格 Markdown 语法         |
| 24  | [[perfetto-audio]]                       | Perfetto    | 音频卡顿、underrun 分析                |
| 25  | [[perfetto-binder-latency]]              | Perfetto    | Binder 事务延迟分析                   |
| 26  | [[perfetto-command-playbook]]            | Perfetto    | perfetto-mcp 首次工具选择引导           |
| 27  | [[perfetto-cpu-scheduler-stall]]         | Perfetto    | CPU 饥饿与调度延迟分析                   |
| 28  | [[perfetto-history-issue-matcher]]       | Perfetto    | 历史案例库检索                         |
| 29  | [[perfetto-jank-frame-analysis]]         | Perfetto    | 帧丢失、卡顿分析                        |
| 30  | [[perfetto-priority]]                    | Perfetto    | 线程优先级异常分析                       |
| 31  | [[perfetto-report-writer]]               | Perfetto    | 中文 Perfetto 分析报告生成              |
| 32  | [[perfetto-root-cause-classifier]]       | Perfetto    | 性能问题根因机制分类                      |
| 33  | [[perfetto-stack-evidence-hunter]]       | Perfetto    | 深层执行证据（调用链）挖掘                   |
| 34  | [[perfetto-startup-latency]]             | Perfetto    | 启动延迟分析                          |
| 35  | [[perfetto-system-mitigation-advisor]]   | Perfetto    | Android 系统级缓解建议生成               |
| 36  | [[perfetto-trace-intake]]                | Perfetto    | Perfetto trace 调查输入验证           |
| 37  | [[perfetto-trace-observability-auditor]] | Perfetto    | trace 可观测性上限审计                  |
| 38  | [[perfetto-triage-reasoner]]             | Perfetto    | perfetto-mcp 结果推理与迭代决策          |
| 39  | [[performance-engineer]]                 | 性能          | 应用性能分析与优化                       |
| 40  | [[permission]]                           | 系统          | Claude Code 权限自动放行规范            |
| 41  | [[planning-with-files]]                  | 方法论         | 基于持久化 Markdown 的任务规划            |
| 42  | [[prd-implementation-precheck]]          | PRD         | PRD 实现前的预检审查                    |
| 43  | [[prd-planner]]                          | PRD         | 4文件模式 PRD 创建工作流                 |
| 44  | [[qa-expert]]                            | 测试          | 测试策略与质量门控                       |
| 45  | [[refactoring-specialist]]               | 重构          | 代码重构与可维护性改进                     |
| 46  | [[report-generator]]                     | 报告          | 专业数据报告（含图表）生成                   |
| 47  | [[security-auditor]]                     | 安全          | OWASP Top 10 安全漏洞审计             |
| 48  | [[self-improving-agent]]                 | 元技能         | 多记忆架构自我进化代理                     |
| 49  | [[session-logger]]                       | 日志          | 对话历史持久化保存                       |
| 50  | [[skill-creator]]                        | 元技能         | 创建、测试与优化 skills                 |
| 51  | [[skill-router]]                         | 元技能         | 智能路由用户请求到最合适的 skill             |
| 52  | [[skywork-ppt]]                          | PPT         | PowerPoint 生成、模板模仿、编辑           |
| 53  | [[test-automator]]                       | 测试          | 自动化测试框架与用例编写                    |
| 54  | [[translation]]                          | 翻译          | 翻译工作流、术语表与质量控制                  |
| 55  | [[using-superpowers]]                    | 元技能         | skills 使用方法与优先级规则               |
| 56  | [[workflow-orchestrator]]                | 编排          | 多 skill 工作流自动编排                 |

---

## 按分类索引

### 🔧 开发技能 (Development)
- [[code-reviewer]] · [[debugger]] · [[refactoring-specialist]] · [[test-automator]]

### 🎨 设计 (Design & UX)
- [[figma-designer]]

### 📐 架构与 DevOps
- [[api-designer]] · [[api-documenter]] · [[architecting-solutions]] · [[deployment-engineer]] · [[performance-engineer]] · [[security-auditor]]

### 📋 PRD 与规划
- [[prd-planner]] · [[prd-implementation-precheck]] · [[planning-with-files]]

### 📚 文档与报告
- [[documentation-engineer]] · [[report-generator]] · [[feishudoc-skill]]

### 🧪 测试与 QA
- [[qa-expert]] · [[test-automator]]

### 🚀 编排与自动化
- [[auto-trigger]] · [[workflow-orchestrator]] · [[long-task-coordinator]]

### 🧠 Perfetto VR/Android 性能分析
- [[hz-perfetto-debug]] · [[perfetto-audio]] · [[perfetto-binder-latency]] · [[perfetto-command-playbook]] · [[perfetto-cpu-scheduler-stall]] · [[perfetto-history-issue-matcher]] · [[perfetto-jank-frame-analysis]] · [[perfetto-priority]] · [[perfetto-report-writer]] · [[perfetto-root-cause-classifier]] · [[perfetto-stack-evidence-hunter]] · [[perfetto-startup-latency]] · [[perfetto-system-mitigation-advisor]] · [[perfetto-trace-intake]] · [[perfetto-trace-observability-auditor]] · [[perfetto-triage-reasoner]]

### 🌐 工具类
- [[agent-browser]] · [[skywork-ppt]] · [[translation]] · [[defuddle]]

### 🔄 Git 工作流
- [[commit-helper]] · [[create-pr]]

### 📦 Meta 技能 (Skills 本身)
- [[find-skills]] · [[self-improving-agent]] · [[session-logger]] · [[skill-creator]] · [[skill-router]] · [[using-superpowers]] · [[permission]]

### 💬 Obsidian 知识管理
- [[obsidian-charter]] · [[obsidian-cli]] · [[obsidian-markdown]] · [[obsidian-bases]] · [[json-canvas]]

### 🀄 中文语境
- [[context-ZH]]

---

## 同步流程说明

### 本地 → Obsidian 同步步骤

1. **同步 SKILL.md 文件**
   - 源路径：`C:\Users\nijiasheng1\.claude\skills\`
   - 目标路径：`D:\sidian-charter\claude skills\`
   - 使用 `robocopy` 或直接复制

2. **更新索引**
   - 编辑 `00 - Skills Index.md`
   - 添加新 skill 到总览表
   - 更新分类索引
   - 更新 Skill 数量

3. **检查清单**
   - [ ] 新增 skill 文件已复制
   - [ ] 索引总览表已更新
   - [ ] 分类索引已更新
   - [ ] Skill 总数已更新

---

## 创建信息

- **创建日期**: 2026-04-09
- **最后更新**: 2026-04-10
- **Skill 数量**: 56
- **来源路径**: `C:\Users\nijiasheng1\.claude\skills\`
- **同步路径**: `D:\sidian-charter\claude skills\`
