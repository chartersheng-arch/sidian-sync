"""Code Locator - Locate Android Audio source code files and functions."""
import re
import os
import subprocess
from typing import Dict, List, Optional, Any
from urllib.parse import quote


# ============================================================================
# 源码来源配置 (由用户配置)
# ============================================================================
# 本地源码根目录
LOCAL_SOURCE_ROOT = "D:\\android_source"  # 用户可修改

# OpenGrok 服务器地址
OPENGROK_URL = "http://opengrok.example.com"  # 用户可修改


# Component to source file mapping
COMPONENT_MAP = {
    # AudioFlinger
    "AudioFlinger": [
        "frameworks/av/services/audioflinger/AudioFlinger.cpp",
        "frameworks/av/services/audioflinger/Threads.cpp",
        "frameworks/av/services/audioflinger/Tracks.cpp",
        "frameworks/av/services/audioflinger/PlaybackThread.cpp",
        "frameworks/av/services/audioflinger/RecordThread.cpp",
        "frameworks/av/services/audioflinger/MixerThread.cpp",
    ],
    "PlaybackThread": [
        "frameworks/av/services/audioflinger/PlaybackThread.cpp",
        "frameworks/av/services/audioflinger/Threads.cpp",
    ],
    "RecordThread": [
        "frameworks/av/services/audioflinger/RecordThread.cpp",
        "frameworks/av/services/audioflinger/Threads.cpp",
    ],
    "MixerThread": [
        "frameworks/av/services/audioflinger/MixerThread.cpp",
        "frameworks/av/services/audioflinger/Threads.cpp",
    ],

    # AudioPolicy
    "AudioPolicyManager": [
        "frameworks/av/services/audiopolicy/managerdefault/AudioPolicyManager.cpp",
        "frameworks/av/services/audiopolicy/enginedefault/src/EngineDefault.cpp",
    ],
    "AudioPolicyService": [
        "frameworks/av/services/audiopolicy/service/AudioPolicyService.cpp",
    ],
    "getDeviceForStrategy": [
        "frameworks/av/services/audiopolicy/enginedefault/src/EngineDefault.cpp",
        "frameworks/av/services/audiopolicy/managerdefault/AudioPolicyManager.cpp",
    ],
    "getOutputForDevice": [
        "frameworks/av/services/audiopolicy/managerdefault/AudioPolicyManager.cpp",
    ],

    # HAL Interface
    "AudioHW": [
        "hardware/interfaces/audio/core/all-versions/default/streamimpl/OutputStreamAll.cpp",
        "hardware/interfaces/audio/core/all-versions/default/streamimpl/InputStreamAll.cpp",
    ],
    "audio_stream_out": [
        "hardware/interfaces/audio/core/all-versions/default/streamout/allStreamOut.cpp",
    ],
    "audio_stream_in": [
        "hardware/interfaces/audio/core/all-versions/default/streamin/allStreamIn.cpp",
    ],

    # Platform-specific (Qualcomm)
    "qcom_audio": [
        "hardware/qcom/audio/hal/audio_hw.c",
        "hardware/qcom/audio/hal/msm8974/audio_hw.c",
        "vendor/qcom/proprietary/mm-audio/audcal.yaml",
    ],
    "AudioHAL-QCOM": [
        "hardware/qcom/audio/hal/audio_hw.c",
        "hardware/qcom/audio/hal/audio_ext_hdmi.c",
    ],

    # Platform-specific (MTK)
    "mtk_audio": [
        "vendor/mediatek/proprietary/hardware/audio/AudioALSATopology.cpp",
        "vendor/mediatek/proprietary/hardware/audio/AudioALSATransportController.cpp",
    ],
    "AudioHAL-MTK": [
        "vendor/mediatek/proprietary/hardware/audio/AudioALSAHwWriter.cpp",
    ],

    # Platform-specific (Spreadtrum)
    "sprd_audio": [
        "vendor/sprd/modules/libaudio/sprd_audio_hw.c",
    ],
    "AudioHAL-SPRD": [
        "vendor/sprd/modules/libaudio/sprd_audio_hw.cpp",
    ],
}

# Function location hints
FUNCTION_HINTS = {
    "out_write": {
        "qcom": "hardware/qcom/audio/hal/audio_hw.c",
        "mtk": "vendor/mediatek/proprietary/hardware/audio/AudioALSAStreamOut.cpp",
        "sprd": "vendor/sprd/modules/libaudio/sprd_audio_hw.c",
        "default": "hardware/interfaces/audio/core/all-versions/default/streamimpl/OutputStreamAll.cpp"
    },
    "in_read": {
        "qcom": "hardware/qcom/audio/hal/audio_hw.c",
        "mtk": "vendor/mediatek/proprietary/hardware/audio/AudioALSAStreamIn.cpp",
        "sprd": "vendor/sprd/modules/libaudio/sprd_audio_hw.c",
        "default": "hardware/interfaces/audio/core/all-versions/default/streamimpl/InputStreamAll.cpp"
    },
    "out_standby": {
        "qcom": "hardware/qcom/audio/hal/audio_hw.c",
        "mtk": "vendor/mediatek/proprietary/hardware/audio/AudioALSAStreamOut.cpp",
        "default": "hardware/interfaces/audio/core/all-versions/default/streamimpl/OutputStreamAll.cpp"
    },
    "get_input_frames_read": {
        "default": "hardware/interfaces/audio/core/all-versions/default/streamimpl/InputStreamAll.cpp"
    },
}

# Customization points per platform
CUSTOMIZATION_POINTS = {
    "qcom": [
        {
            "path": "device/qcom/{BOARD}/audio/audio_policy_configuration.xml",
            "description": "QCOM设备路由策略配置"
        },
        {
            "path": "hardware/qcom/audio/hal/audio_hw.c",
            "description": "QCOM Audio HAL实现，重点关注 out_standby 和 out_write"
        },
        {
            "path": "vendor/qcom/proprietary/audio-ext/routing/routing.cpp",
            "description": "QCOM动态路由管理"
        }
    ],
    "mtk": [
        {
            "path": "vendor/mediatek/{CHIP}/audio/audio_policy_configuration.xml",
            "description": "MTK设备路由策略配置"
        },
        {
            "path": "vendor/mediatek/proprietary/hardware/audio/AudioALSAHwWriter.cpp",
            "description": "MTK ALSA硬件抽象层"
        },
        {
            "path": "vendor/mediatek/proprietary/hardware/audio/AudioSpeechEnhance.cpp",
            "description": "MTK语音增强模块"
        }
    ],
    "sprd": [
        {
            "path": "vendor/sprd/{CHIP}/audio/audio_policy_configuration.xml",
            "description": "展锐设备路由策略配置"
        },
        {
            "path": "vendor/sprd/modules/libaudio/sprd_audio_hw.c",
            "description": "展锐Audio HAL实现"
        }
    ],
    "default": [
        {
            "path": "frameworks/av/services/audiopolicy/config/audio_policy_configuration.xml",
            "description": "默认AudioPolicy配置"
        },
        {
            "path": "frameworks/av/services/audioflinger/config/audio_policy.conf",
            "description": "AudioFlinger配置"
        }
    ]
}

# Common error keywords to component mapping
ERROR_COMPONENT_MAP = {
    "pcm_write error": "AudioFlinger/PlaybackThread",
    "pcm_read error": "AudioFlinger/RecordThread",
    "standby": "AudioFlinger/PlaybackThread",
    "underrun": "AudioFlinger/MixerThread",
    "overrun": "AudioFlinger/RecordThread",
    "-ENODEV": "AudioHAL",
    "-EINVAL": "AudioHAL",
    "routing": "AudioPolicy",
    "setOutputDevice": "AudioPolicy",
    "getDeviceForStrategy": "AudioPolicyManager",
}


def locate_by_error_keyword(error_keyword: str) -> List[Dict[str, Any]]:
    """Locate components related to error keyword."""
    results = []

    for error, components in ERROR_COMPONENT_MAP.items():
        if error.lower() in error_keyword.lower():
            for component in components.split("/"):
                if component in COMPONENT_MAP:
                    results.extend(COMPONENT_MAP[component])

    return list(set(results))


def locate_by_component(
    component: str,
    platform: str = "auto"
) -> List[Dict[str, Any]]:
    """
    Locate source files for a component.

    Args:
        component: Component name (e.g., "AudioFlinger", "getDeviceForStrategy")
        platform: Platform type (qcom/mtk/sprd/auto)

    Returns:
        List of file information dictionaries
    """
    results = []

    # Direct component match
    if component in COMPONENT_MAP:
        files = COMPONENT_MAP[component]
        for f in files:
            results.append({
                "path": f,
                "type": "component_direct",
                "reason": f"Direct match for {component}"
            })

    # Function hints
    if component in FUNCTION_HINTS:
        hints = FUNCTION_HINTS[component]
        if platform in hints:
            results.append({
                "path": hints[platform],
                "type": "function_platform",
                "reason": f"{component} implementation for {platform}"
            })
        elif "default" in hints:
            results.append({
                "path": hints["default"],
                "type": "function_default",
                "reason": f"{component} default implementation"
            })

    # Partial match
    for comp, files in COMPONENT_MAP.items():
        if component.lower() in comp.lower():
            for f in files:
                if f not in [r["path"] for r in results]:
                    results.append({
                        "path": f,
                        "type": "partial_match",
                        "reason": f"Partial match: {component} in {comp}"
                    })

    return results


def get_customization_points(platform: str) -> List[Dict[str, str]]:
    """
    Get customization points for a platform.

    Args:
        platform: Platform type (qcom/mtk/sprd)

    Returns:
        List of customization point dictionaries
    """
    if platform in CUSTOMIZATION_POINTS:
        return CUSTOMIZATION_POINTS[platform]
    return CUSTOMIZATION_POINTS["default"]


def generate_call_chain(error_keyword: str) -> List[str]:
    """
    Generate typical call chain for an error.

    Args:
        error_keyword: Error keyword or component name

    Returns:
        List of call chain steps
    """
    error_lower = error_keyword.lower()

    if "playback" in error_lower or "out_write" in error_lower:
        return [
            "AudioTrack::write()",
            "→ AudioFlinger::PlaybackThread::write()",
            "→ AudioStreamOut::write()",
            "→ audio_stream_out->write() [HAL]",
            "→ Kernel DMA write"
        ]
    elif "record" in error_lower or "in_read" in error_lower:
        return [
            "AudioRecord::read()",
            "→ AudioFlinger::RecordThread::read()",
            "→ AudioStreamIn::read()",
            "→ audio_stream_in->read() [HAL]",
            "→ Kernel DMA read"
        ]
    elif "standby" in error_lower:
        return [
            "AudioFlinger::PlaybackThread::standby()",
            "→ AudioStreamOut::standby()",
            "→ audio_stream_out->standby() [HAL]",
            "→ Kernel DMA stop"
        ]
    elif "routing" in error_lower or "device" in error_lower:
        return [
            "AudioPolicyService::setOutputDevice()",
            "→ AudioPolicyManager::setOutputDevice()",
            "→ getDeviceForStrategy()",
            "→ AudioFlinger::setParameters()"
        ]

    return [
        "App (AudioTrack/AudioRecord)",
        "→ AudioFlinger",
        "→ Audio HAL",
        "→ Kernel (ASoC/DMA)"
    ]


# ============================================================================
# 源码搜索功能
# ============================================================================

def search_local_source(
    keyword: str,
    source_root: Optional[str] = None,
    file_patterns: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search for keyword in local source code.

    Args:
        keyword: Search keyword (function name, error message, etc.)
        source_root: Local source code root directory (uses LOCAL_SOURCE_ROOT if not provided)
        file_patterns: File patterns to search (e.g., ["*.cpp", "*.h"])

    Returns:
        List of search results with file path and line matches
    """
    results = []

    if file_patterns is None:
        file_patterns = ["*.cpp", "*.h", "*.c", "*.hpp"]

    # Use provided source_root or fall back to default
    if source_root is None:
        source_root = LOCAL_SOURCE_ROOT

    # Convert to Windows-compatible path
    source_root = source_root.replace("/", "\\")

    if not source_root or not os.path.exists(source_root):
        return [{
            "error": "Source root not specified or not found",
            "tip": "Provide source_root parameter or configure LOCAL_SOURCE_ROOT"
        }]

    try:
        for pattern in file_patterns:
            # Use grep-like search via Python for cross-platform compatibility
            for root, dirs, files in os.walk(source_root):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in [
                    ".git", "out", "target", "node_modules", ".repo"
                ]]

                for file in files:
                    if file.endswith(tuple(pattern.replace("*", ""))):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_no, line in enumerate(f, 1):
                                    if keyword.lower() in line.lower():
                                        rel_path = os.path.relpath(filepath, source_root)
                                        results.append({
                                            "file": rel_path.replace("\\", "/"),
                                            "line": line_no,
                                            "content": line.strip()[:150],
                                            "full_path": filepath
                                        })
                        except (PermissionError, IOError):
                            continue

                        # Limit results
                        if len(results) >= 100:
                            return results

    except Exception as e:
        return [{"error": str(e)}]

    return results[:100]  # Limit to 100 results


def generate_opengrok_url(
    keyword: str,
    opengrok_url: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate OpenGrok search URLs for a keyword.

    Args:
        keyword: Search keyword
        opengrok_url: OpenGrok server URL (uses OPENGROK_URL if not provided)

    Returns:
        Dictionary with different search URL types
    """
    if opengrok_url is None:
        opengrok_url = OPENGROK_URL
    encoded_keyword = quote(keyword)

    # Standard full-text search
    fulltext_url = f"{opengrok_url}/search?q={encoded_keyword}&defs=&refs=&path=audio"

    # Symbol/definition search
    symbol_url = f"{opengrok_url}/search?q={encoded_keyword}&type=symbol"

    # Path-constrained search for audio
    audio_url = f"{opengrok_url}/search?q={encoded_keyword}&path=audio&name="

    # Common Android audio paths
    paths = [
        "frameworks/av/services/audioflinger",
        "frameworks/av/services/audiopolicy",
        "hardware/interfaces/audio",
        "system/audio",
    ]

    path_urls = {}
    for path in paths:
        encoded_path = quote(path)
        path_urls[path] = f"{opengrok_url}/search?q={encoded_keyword}&path={encoded_path}"

    return {
        "keyword": keyword,
        "fulltext": fulltext_url,
        "symbol": symbol_url,
        "audio_scope": audio_url,
        "path_searches": path_urls,
        "tip": "OpenGrok URLs - paste in browser to search"
    }


def locate(
    android_version: Optional[str] = None,
    platform: str = "auto",
    component: Optional[str] = None,
    error_keyword: Optional[str] = None,
    source_root: str = LOCAL_SOURCE_ROOT,
    opengrok_url: str = OPENGROK_URL,
    search_local: bool = False,
    generate_opengrok: bool = False
) -> Dict[str, Any]:
    """
    Locate audio source code based on component or error keyword.

    Args:
        android_version: Android version (e.g., "13", "14")
        platform: Platform type (qcom/mtk/sprd/auto)
        component: Component name
        error_keyword: Error keyword or message
        source_root: Local source code root directory
        opengrok_url: OpenGrok server URL
        search_local: Whether to search local source
        generate_opengrok: Whether to generate OpenGrok URLs

    Returns:
        Dictionary with files, call_chain, customization_points, and source URLs
    """
    files = []
    call_chain = []
    customization_points = []
    local_search_results = []
    opengrok_urls = {}

    # By component
    if component:
        files = locate_by_component(component, platform)

    # By error keyword
    search_term = error_keyword or component
    if search_term:
        error_files = locate_by_error_keyword(search_term)
        for f in error_files:
            if f not in [r.get("path") or r for r in files]:
                files.append({"path": f, "type": "error_keyword"})
        call_chain = generate_call_chain(search_term)

        # Search local source if enabled
        if search_local:
            local_search_results = search_local_source(search_term, source_root)

        # Generate OpenGrok URLs if enabled
        if generate_opengrok:
            opengrok_urls = generate_opengrok_url(search_term, opengrok_url)

    # Get customization points
    if platform != "auto":
        customization_points = get_customization_points(platform)

    return {
        "files": files,
        "call_chain": call_chain,
        "customization_points": customization_points,
        "android_version": android_version,
        "platform": platform,
        "source_root": source_root,
        "local_search": local_search_results,
        "opengrok": opengrok_urls
    }
