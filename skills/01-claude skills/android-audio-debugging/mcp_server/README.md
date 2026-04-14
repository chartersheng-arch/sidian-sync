# Android Audio Diagnosis MCP Server

## 安装

```bash
cd mcp_server
pip install -r requirements.txt
```

## 启动

```bash
python mcp_audio_server.py
```

## 配置Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "android-audio": {
      "command": "python",
      "args": ["C:/Users/nijiasheng1/.claude/skills/android-audio-debugging/mcp_server/mcp_audio_server.py"]
    }
  }
}
```

## 工具列表

| 工具 | 功能 |
|------|------|
| audio_log_parser | 解析Android audio日志，分层提取错误 |
| code_locator | 定位Android audio相关源码 |
| device_collector | 通过ADB获取设备诊断信息 |
| case_matcher | 匹配历史案例库 |
| report_builder | 生成Markdown诊断报告 |
