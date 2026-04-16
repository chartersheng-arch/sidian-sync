"""Case Matcher - Match historical cases for audio problems."""
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Skill base directory for loading user_config.md
SKILL_BASE_DIR = Path(__file__).parent.parent


@dataclass
class CaseMatch:
    """Matched case result."""
    title: str
    similarity: float
    root_cause: str
    solution: str
    platform: str
    keywords: List[str]
    notes: str = ""


# Built-in case library
BUILTIN_CASES = [
    CaseMatch(
        title="高通平台空路由导致AudioStreamOut永久standby",
        similarity=0.0,  # Will be calculated
        root_cause="AudioPolicyManager::getDeviceForStrategy在耳机拔出后返回空设备，上层未处理fallback，导致AudioStreamOut无法退出standby",
        solution="在getDeviceForStrategy最后增加fallback到DEVICE_OUT_SPEAKER",
        platform="qcom",
        keywords=["standby", "no sound", "playback", "-ENODEV", "routing", "device NULL"],
        notes="影响SM8450及后续平台"
    ),
    CaseMatch(
        title="高通平台FastMixer CPU占用过高导致延迟",
        similarity=0.0,
        root_cause="FastMixer线程被低优先级任务抢占，调度延迟累积",
        solution="调整FastMixer线程优先级为RT，绑定到特定CPU核心",
        platform="qcom",
        keywords=["latency", "FastMixer", "CPU", "scheduling", "delay"],
        notes="VoIP通话延迟可达500ms+"
    ),
    CaseMatch(
        title="MTK扬声器保护触发误报导致无声",
        similarity=0.0,
        root_cause="Speaker Protection算法将正常语音判定为异常，过温保护误触发",
        solution="调整Speaker Protection阈值，增加确认机制避免误触发",
        platform="mtk",
        keywords=["speaker protection", "no sound", "temperature", "overheat", "muted"],
        notes="通话场景常见"
    ),
    CaseMatch(
        title="MTK录音Buffer Overflow导致断续",
        similarity=0.0,
        root_cause="RecordThread buffer配置过小，CPU繁忙时无法及时读取",
        solution="增加RecordThread buffer size从960帧到1920帧",
        platform="mtk",
        keywords=["buffer overflow", "recording", "dropout", "overrun", "gap"],
        notes="周期性断续，每隔固定时间丢失音频"
    ),
    CaseMatch(
        title="展锐DMA传输错误导致杂音",
        similarity=0.0,
        root_cause="DMA descriptor配置错误，burst size与FIFO大小不匹配",
        solution="修正DMA descriptor的burst size配置",
        platform="sprd",
        keywords=["DMA", "noise", "distortion", "transfer error", "burst", "杂音"],
        notes="24bit/96kHz高采样率更明显"
    ),
    CaseMatch(
        title="Bluetooth A2DP断连后路由未恢复",
        similarity=0.0,
        root_cause="AudioPolicy未正确处理BT设备断开事件，output device未更新",
        solution="在BT断开时强制清除路由缓存，重新计算有效设备",
        platform="通用",
        keywords=["Bluetooth", "A2DP", "disconnect", "routing", "BT", "no sound"],
        notes="BT断开后音频无法切换到扬声器"
    ),
    CaseMatch(
        title="HAL write返回成功但数据未送出",
        similarity=0.0,
        root_cause="DMA clock未使能或路由配置正确但Codec路径未切换",
        solution="检查DAPM状态，确认Clock门控和Power状态",
        platform="通用",
        keywords=["DMA", "clock", "write success", "no sound", "routing", "DAPM"],
        notes="write返回字节数正常但实际无声音"
    ),
    CaseMatch(
        title="AudioFlinger MixerThread underrun导致播放断续",
        similarity=0.0,
        root_cause="Mixer buffer配置过小，系统CPU繁忙时发生underrun",
        solution="增加output buffer size或启用deep buffer模式",
        platform="通用",
        keywords=["underrun", "MixerThread", "dropout", "buffer", "CPU"],
        notes="系统高负载时更易触发"
    ),
]


def calculate_similarity(features: Dict[str, Any], case: CaseMatch) -> float:
    """
    Calculate similarity between problem features and a case.

    Args:
        features: Problem features (error_code, module, platform, keywords)
        case: Historical case to compare

    Returns:
        Similarity score (0.0 to 1.0)
    """
    score = 0.0
    max_score = 0.0

    # Platform match (weight: 0.3)
    max_score += 0.3
    if features.get("platform") and case.platform != "通用":
        if features["platform"].lower() in case.platform.lower():
            score += 0.3
        elif case.platform == "通用":
            score += 0.15  # Partial match to generic

    # Module match (weight: 0.2)
    max_score += 0.2
    if features.get("module"):
        module = features["module"].lower()
        if any(module in kw.lower() for kw in case.keywords):
            score += 0.2
        elif any(kw.lower() in module for kw in case.keywords):
            score += 0.15

    # Error code match (weight: 0.25)
    max_score += 0.25
    if features.get("error_code"):
        error = features["error_code"].lower()
        if any(error in kw.lower() for kw in case.keywords):
            score += 0.25
        elif any(kw.lower() in error for kw in case.keywords):
            score += 0.15

    # Keywords match (weight: 0.25)
    max_score += 0.25
    if features.get("keywords"):
        case_keywords_lower = [kw.lower() for kw in case.keywords]
        matched = 0
        for kw in features["keywords"]:
            if any(kw.lower() in ck for ck in case_keywords_lower):
                matched += 1
        if features["keywords"]:
            score += 0.25 * (matched / len(features["keywords"]))

    return score / max_score if max_score > 0 else 0.0


def match(
    error_code: Optional[str] = None,
    module: Optional[str] = None,
    platform: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    android_version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Match problem features against historical cases.

    Args:
        error_code: Error code (e.g., "-22", "ETIMEDOUT")
        module: Module name (AudioFlinger, AudioHAL, etc.)
        platform: Platform (qcom, mtk, sprd)
        keywords: List of keyword strings
        android_version: Android version

    Returns:
        Dictionary with matched cases and similarity scores
    """
    features = {
        "error_code": error_code,
        "module": module,
        "platform": platform,
        "keywords": keywords or [],
        "android_version": android_version
    }

    matches = []
    for case in BUILTIN_CASES:
        similarity = calculate_similarity(features, case)
        if similarity > 0.3:  # Threshold
            matches.append({
                "title": case.title,
                "similarity": round(similarity, 2),
                "root_cause": case.root_cause,
                "solution": case.solution,
                "platform": case.platform,
                "notes": case.notes,
                "source": "builtin"
            })

    # Search user knowledge bases
    user_results = search_user_knowledge(features)
    for result in user_results:
        result["source"] = "user_knowledge"
        matches.append(result)

    # Sort by similarity descending
    matches.sort(key=lambda x: x["similarity"], reverse=True)

    return {
        "matches": matches[:5],  # Top 5 matches
        "total_cases": len(BUILTIN_CASES),
        "user_knowledge_dirs": [str(d) for d in load_user_knowledge_dirs()],
        "features": features
    }


def load_user_knowledge_dirs() -> List[Path]:
    """
    Load user-configured knowledge base directories from user_config.md.

    Returns:
        List of Path objects for configured directories
    """
    config_file = SKILL_BASE_DIR / "user_config.md"
    if not config_file.exists():
        return []

    dirs = []
    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Skip section headers and format lines
            if line.startswith("---") or line.startswith("|") or line.startswith("**"):
                continue
            # Treat as a directory path
            path = Path(line)
            if path.is_absolute() or (len(line) > 1 and line[1] == ":"):
                # Absolute path (Windows D:\... or Unix /...)
                dirs.append(path)
            else:
                # Relative path - resolve from skill base dir
                dirs.append((SKILL_BASE_DIR / path).resolve())

    return dirs


def search_user_knowledge(
    features: Dict[str, Any],
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """
    Search user knowledge base directories for matching cases.

    Args:
        features: Problem features (error_code, module, platform, keywords)
        max_results: Maximum number of results to return

    Returns:
        List of matching entries from user knowledge bases
    """
    user_dirs = load_user_knowledge_dirs()
    if not user_dirs:
        return []

    results = []
    search_text = " ".join([
        features.get("error_code", "") or "",
        features.get("module", "") or "",
        features.get("platform", "") or "",
        " ".join(features.get("keywords", []))
    ]).lower()

    for user_dir in user_dirs:
        if not user_dir.exists():
            continue

        # Search all text files in the directory
        for ext in ["*.md", "*.txt", "*.log"]:
            for file_path in user_dir.rglob(ext):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                    # Simple keyword overlap scoring
                    keywords = features.get("keywords", [])
                    matches = sum(1 for kw in keywords if kw.lower() in content)
                    if matches >= 2:  # At least 2 keyword matches
                        results.append({
                            "title": f"[用户知识库] {file_path.name}",
                            "similarity": min(matches / len(keywords) if keywords else 0.5, 0.99),
                            "root_cause": f"详见文件: {file_path}",
                            "solution": "请查阅用户知识库文件获取详情",
                            "platform": features.get("platform", "未知"),
                            "notes": f"匹配度: {matches}/{len(keywords)} 关键词"
                        })
                except Exception:
                    continue

    # Sort by similarity and limit results
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:max_results]


def add_case(
    title: str,
    root_cause: str,
    solution: str,
    platform: str,
    keywords: List[str],
    notes: str = ""
) -> Dict[str, str]:
    """
    Add a new case to the library (in-memory for this session).

    Args:
        title: Case title
        root_cause: Root cause description
        solution: Solution description
        platform: Platform (qcom/mtk/sprd/通用)
        keywords: List of keywords
        notes: Additional notes

    Returns:
        Status message
    """
    global BUILTIN_CASES

    new_case = CaseMatch(
        title=title,
        similarity=0.0,
        root_cause=root_cause,
        solution=solution,
        platform=platform,
        keywords=keywords,
        notes=notes
    )

    BUILTIN_CASES.append(new_case)

    return {
        "status": "success",
        "message": f"Added case: {title}",
        "total_cases": len(BUILTIN_CASES)
    }
