#!/usr/bin/env python3
"""
Android Audio Diagnosis MCP Server

This server provides tools for diagnosing Android audio issues:
- audio_log_parser: Parse and analyze audio logs
- code_locator: Locate relevant source files
- device_collector: Execute ADB commands
- case_matcher: Match historical cases
- report_builder: Generate diagnosis reports

Usage:
    python mcp_audio_server.py

For Claude Desktop integration, add to claude_desktop_config.json:
{
  "mcpServers": {
    "android-audio": {
      "command": "python",
      "args": ["path/to/mcp_audio_server.py"]
    }
  }
}
"""

import json
import asyncio
from typing import Any, Dict, List, Optional

# MCP Server imports
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
except ImportError:
    print("Warning: MCP library not installed. Install with: pip install mcp>=0.10.0")
    # Fallback to dummy for testing without MCP
    Server = None

# Import our modules
from audio_log_parser import parse_log
from code_locator import locate
from device_collector import collect as device_collect, execute_bundle, collect_device_info
from case_matcher import match as case_match, add_case
from report_builder import build_report, build_simple_report


# Server instance
SERVER_NAME = "android-audio-diagnosis"
server = Server(SERVER_NAME)


# Tool definitions
def get_tool_definitions():
    """Return list of MCP tool definitions."""
    return [
        {
            "name": "audio_log_parser",
            "description": "Parse Android audio logs and extract structured information per layer (App, AudioFlinger, HAL, Kernel). Extracts errors, state changes, and builds timeline.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "log_text": {
                        "type": "string",
                        "description": "Raw log text to parse"
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["qcom", "mtk", "sprd", "auto"],
                        "default": "auto",
                        "description": "Platform type for platform-specific parsing"
                    },
                    "time_range_start": {
                        "type": "string",
                        "description": "Optional start time filter (HH:MM:SS)"
                    },
                    "time_range_end": {
                        "type": "string",
                        "description": "Optional end time filter (HH:MM:SS)"
                    }
                },
                "required": ["log_text"]
            }
        },
        {
            "name": "code_locator",
            "description": "Locate Android audio source files based on component name or error keyword. Returns file paths, call chains, and platform customization points.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "android_version": {
                        "type": "string",
                        "description": "Android version (e.g., '13', '14')"
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["qcom", "mtk", "sprd", "auto"],
                        "default": "auto",
                        "description": "Platform type"
                    },
                    "component": {
                        "type": "string",
                        "description": "Component name (e.g., 'AudioFlinger', 'getDeviceForStrategy')"
                    },
                    "error_keyword": {
                        "type": "string",
                        "description": "Error keyword or message"
                    }
                }
            }
        },
        {
            "name": "device_collector",
            "description": "Execute ADB commands on Android device to collect diagnostic information. Can execute custom commands or predefined diagnostic bundles.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "device_serial": {
                        "type": "string",
                        "description": "Device serial number (optional, uses default device)"
                    },
                    "commands": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of shell commands to execute"
                    },
                    "bundle": {
                        "type": "string",
                        "enum": ["audio_full", "audio_playback", "audio_capture", "kernel_audio", "audio_properties"],
                        "description": "Predefined diagnostic bundle to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30,
                        "description": "Command timeout in seconds"
                    }
                    }
                }
        },
        {
            "name": "case_matcher",
            "description": "Match problem features against historical case library. Returns ranked matches with similarity scores, root causes, and solutions.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "error_code": {
                        "type": "string",
                        "description": "Error code (e.g., '-22', 'ETIMEDOUT')"
                    },
                    "module": {
                        "type": "string",
                        "description": "Module name (e.g., 'AudioFlinger', 'AudioHAL')"
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["qcom", "mtk", "sprd", "通用"],
                        "description": "Platform type"
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keyword strings"
                    },
                    "android_version": {
                        "type": "string",
                        "description": "Android version"
                    }
                }
            }
        },
        {
            "name": "report_builder",
            "description": "Generate structured Markdown diagnosis report with evidence chain, hypothesis table, root cause, and fix suggestions.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "default": "Android Audio 问题诊断报告",
                        "description": "Report title"
                    },
                    "device_info": {
                        "type": "string",
                        "description": "Device information"
                    },
                    "phenomenon": {
                        "type": "string",
                        "description": "Problem phenomenon description"
                    },
                    "problem_type": {
                        "type": "string",
                        "enum": ["无声", "杂音", "延迟", "爆音", "断续", "其他"],
                        "description": "Problem type"
                    },
                    "root_cause": {
                        "type": "string",
                        "description": "Root cause description"
                    },
                    "root_cause_analysis": {
                        "type": "string",
                        "description": "Detailed root cause analysis"
                    },
                    "fix_suggestions": {
                        "type": "array",
                        "description": "List of fix suggestions with priority, solution, scope, risk"
                    },
                    "verification_plan": {
                        "type": "array",
                        "description": "List of verification steps"
                    },
                    "matched_cases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Matched historical cases"
                    }
                },
                "required": ["phenomenon", "root_cause"]
            }
        }
    ]


# Tool handlers
async def handle_audio_log_parser(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle audio_log_parser tool call."""
    result = parse_log(
        log_text=arguments.get("log_text", ""),
        platform=arguments.get("platform", "auto"),
        time_range_start=arguments.get("time_range_start"),
        time_range_end=arguments.get("time_range_end")
    )
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}


async def handle_code_locator(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle code_locator tool call."""
    result = locate(
        android_version=arguments.get("android_version"),
        platform=arguments.get("platform", "auto"),
        component=arguments.get("component"),
        error_keyword=arguments.get("error_keyword")
    )
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}


async def handle_device_collector(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle device_collector tool call."""
    device_serial = arguments.get("device_serial")
    timeout = arguments.get("timeout", 30)

    # Execute bundle if specified
    if arguments.get("bundle"):
        results = execute_bundle(arguments["bundle"], device_serial, timeout)
    # Execute custom commands
    elif arguments.get("commands"):
        results = device_collect(arguments["commands"], device_serial, timeout)
    else:
        # Collect basic device info
        results = collect_device_info(device_serial)

    return {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False, indent=2)}]}


async def handle_case_matcher(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle case_matcher tool call."""
    result = case_match(
        error_code=arguments.get("error_code"),
        module=arguments.get("module"),
        platform=arguments.get("platform"),
        keywords=arguments.get("keywords"),
        android_version=arguments.get("android_version")
    )
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}


async def handle_report_builder(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle report_builder tool call."""
    # Check if simple report
    if arguments.get("simple"):
        report = build_simple_report(
            title=arguments.get("title", "Android Audio 问题诊断报告"),
            phenomenon=arguments.get("phenomenon", ""),
            root_cause=arguments.get("root_cause", ""),
            solution=arguments.get("solution", "")
        )
    else:
        report = build_report(
            title=arguments.get("title", "Android Audio 问题诊断报告"),
            device_info=arguments.get("device_info"),
            phenomenon=arguments.get("phenomenon", ""),
            problem_type=arguments.get("problem_type", ""),
            impact_scope=arguments.get("impact_scope", ""),
            reproduction_rate=arguments.get("reproduction_rate", ""),
            evidence_chain=arguments.get("evidence_chain"),
            hypothesis_table=arguments.get("hypothesis_table"),
            matched_cases=arguments.get("matched_cases"),
            root_cause=arguments.get("root_cause", ""),
            root_cause_analysis=arguments.get("root_cause_analysis", ""),
            fix_suggestions=arguments.get("fix_suggestions"),
            verification_plan=arguments.get("verification_plan")
        )

    return {"content": [{"type": "text", "text": report}]}


# Server handlers
if Server:

    @server.list_tools()
    async def handle_list_tools():
        """List available tools."""
        return get_tool_definitions()

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]):
        """Handle tool call."""
        handlers = {
            "audio_log_parser": handle_audio_log_parser,
            "code_locator": handle_code_locator,
            "device_collector": handle_device_collector,
            "case_matcher": handle_case_matcher,
            "report_builder": handle_report_builder
        }

        if name in handlers:
            return await handlers[name](arguments)
        else:
            return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}]}


async def main():
    """Main entry point."""
    if Server:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=SERVER_NAME,
                    server_version="1.0.0",
                    notification_options=NotificationOptions()
                )
            )
    else:
        # Demo mode without MCP
        print("MCP library not available. Running in demo mode.")
        print("\n=== Demo: audio_log_parser ===")
        sample_log = """
01-15 10:23:45.123 AudioFlinger: PlaybackThread::threadLoop()
01-15 10:23:45.124 AudioFlinger: track(0x1234): start()
01-15 10:23:45.130 audio_hw: out_write: bytes=4096
01-15 10:23:45.200 AudioFlinger: track(0x1234): underrun
01-15 10:23:45.201 AudioPolicy: setOutputDevice(0x2)
"""
        result = parse_log(sample_log)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        print("\n=== Demo: case_matcher ===")
        match_result = case_match(
            error_code="-ENODEV",
            module="AudioFlinger",
            platform="qcom",
            keywords=["standby", "no sound"]
        )
        print(json.dumps(match_result, indent=2, ensure_ascii=False))

        print("\n=== Demo: report_builder ===")
        report = build_simple_report(
            title="测试报告",
            phenomenon="播放时无声",
            root_cause="路由策略返回空设备",
            solution="增加fallback逻辑"
        )
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
