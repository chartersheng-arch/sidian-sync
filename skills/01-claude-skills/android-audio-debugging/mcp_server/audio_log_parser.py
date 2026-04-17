"""Audio Log Parser - Parse Android audio logs and extract structured information.

Supports:
- logcat (standard Android logcat output)
- dmesg (kernel log)
- bugreport (extracted from tar.gz)
- multi-log synthesis
"""
import re
import gzip
import tarfile
import io
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class LogEntry:
    """Single log entry with parsed information."""
    timestamp: str
    line_no: int
    message: str
    layer: str
    raw: str


@dataclass
class ErrorEntry:
    """Aggregated error information."""
    count: int
    message: str
    first_line: int
    last_line: int
    layer: str
    context_before: List[str]
    context_after: List[str]


@dataclass
class StateChange:
    """State change event."""
    timestamp: str
    component: str
    from_state: str
    to_state: str
    line_no: int


# Layer patterns for classification
LAYER_PATTERNS = {
    "kernel_driver": [
        r"ASoC:", r"snd_soc_", r"DMA:", r"dmaengine",
        r"pcmCVDDrv", r"codec", r"tlv320aic", r"wm8994",
        r"/dev/snd/", r"ALSA", r"sound/soc"
    ],
    "audio_hal": [
        r"audio_hw", r"audio_hal", r"HAL:", r"audio_stream",
        r"out_write", r"in_read", r"out_set_parameters",
        r"in_set_parameters", r"audio_hw_device"
    ],
    "audio_flinger": [
        r"AudioFlinger", r"PlaybackThread", r"RecordThread",
        r"MixerThread", r"DirectOutputThread", r"AudioStreamOut",
        r"AudioTrack", r"AudioRecord"
    ],
    "audio_policy": [
        r"AudioPolicy", r"setOutputDevice", r"setInputDevice",
        r"getDeviceForStrategy", r"routing", r"AudioPolicyService"
    ],
    "audio_service": [
        r"AudioService", r"MediaFocusControl", r"AudioSystem",
        r"android\.media", r"AudioManager"
    ],
    "app": [
        r"ActivityManager", r"ProcessRecord", r"app/process",
        r"pid=\d+.*AudioTrack", r"pid=\d+.*AudioRecord"
    ],
    "bluetooth": [
        r"BluetoothAudio", r"A2DP", r"SCO", r"bt_a2dp",
        r"bt_sco", r"LDAC", r"aptX"
    ]
}

# Error patterns
ERROR_PATTERNS = {
    "-ENODEV": r"-ENODEV|No such device",
    "-EINVAL": r"-EINVAL|Invalid argument",
    "-ENOMEM": r"-ENOMEM|Cannot allocate memory",
    "-EAGAIN": r"-EAGAIN|Resource temporarily unavailable",
    "underrun": r"underrun|underruns",
    "overrun": r"overrun|overruns",
    "xrun": r"xrun|dropped",
    "standby": r"standby|STANDBY",
    "timeout": r"timeout|ETIMEDOUT",
    "busy": r"EBUSY|Device or resource busy",
    "clock": r"clock|CLK",
    "DMA": r"DMA.*error|transfer.*error",
    "suspend": r"SUSPEND|suspend",
    "resume": r"RESUME|resume"
}

# State change patterns
STATE_PATTERNS = [
    (r"(\w+Thread):\s*(\w+)\s*→\s*(\w+)", "thread_state"),
    (r"state:\s*(\w+)\s*(?:→|->)\s*(\w+)", "component_state"),
    (r"(\w+)\s+(?:entering|entered)\s+(\w+)", "enter_state"),
    (r"(\w+)\s+(?:exiting|left)\s+(\w+)", "exit_state"),
    (r"standby", r"standby"),
]


def classify_layer(message: str) -> str:
    """Classify log message to audio layer."""
    for layer, patterns in LAYER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return layer
    return "unknown"


def parse_timestamp(line: str) -> Optional[str]:
    """Extract timestamp from log line."""
    # Android logcat format: 01-15 10:23:45.678
    match = re.match(r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})", line)
    if match:
        return match.group(1)
    # Kernel dmesg format: [  123.456789]
    match = re.match(r"\[\s*(\d+\.\d+)\]", line)
    if match:
        return f"kernel:{match.group(1)}"
    return None


def parse_log_line(line: str, line_no: int) -> Optional[LogEntry]:
    """Parse single log line into structured entry."""
    timestamp = parse_timestamp(line)
    if not timestamp:
        return None

    layer = classify_layer(line)

    return LogEntry(
        timestamp=timestamp,
        line_no=line_no,
        message=line.strip(),
        layer=layer,
        raw=line
    )


def aggregate_errors(logs: List[LogEntry]) -> List[ErrorEntry]:
    """Aggregate similar errors and extract context."""
    error_groups: Dict[str, Dict] = {}

    for log in logs:
        for error_name, pattern in ERROR_PATTERNS.items():
            if re.search(pattern, log.message, re.IGNORECASE):
                key = f"{error_name}:{log.layer}"
                if key not in error_groups:
                    error_groups[key] = {
                        "message": f"{error_name} in {log.layer}",
                        "count": 0,
                        "first_line": log.line_no,
                        "last_line": log.line_no,
                        "layer": log.layer,
                        "context_before": [],
                        "context_after": []
                    }
                error_groups[key]["count"] += 1
                error_groups[key]["last_line"] = log.line_no
                break

    return [ErrorEntry(**data) for data in error_groups.values()]


def extract_state_changes(logs: List[LogEntry]) -> List[StateChange]:
    """Extract state change events."""
    changes = []

    for i, log in enumerate(logs):
        for pattern, state_type in STATE_PATTERNS:
            match = re.search(pattern, log.message)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    component = groups[0] if groups[0] else "unknown"
                    from_state = groups[1] if len(groups) > 1 else "unknown"
                    to_state = groups[2] if len(groups) > 2 else from_state

                    changes.append(StateChange(
                        timestamp=log.timestamp,
                        component=component,
                        from_state=from_state,
                        to_state=to_state,
                        line_no=log.line_no
                    ))
                break

    return changes


def build_timeline(logs: List[LogEntry]) -> List[str]:
    """Build chronological timeline of events."""
    timeline = []
    for log in logs:
        timeline.append(f"{log.timestamp} [{log.layer}] {log.message[:100]}")
    return timeline


def parse_log(
    log_text: str,
    platform: str = "auto",
    time_range_start: Optional[str] = None,
    time_range_end: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse Android audio logs and extract structured information.

    Args:
        log_text: Raw log text to parse
        platform: Platform type (qcom/mtk/sprd/auto)
        time_range_start: Optional start time filter
        time_range_end: Optional end time filter

    Returns:
        Dictionary with layers, errors, state_changes, and timeline
    """
    lines = log_text.strip().split('\n')

    # Parse all log entries
    logs: List[LogEntry] = []
    for i, line in enumerate(lines):
        entry = parse_log_line(line, i + 1)
        if entry:
            logs.append(entry)

    # Group by layer
    layers: Dict[str, List[Dict]] = {
        "kernel_driver": [],
        "audio_hal": [],
        "audio_flinger": [],
        "audio_policy": [],
        "audio_service": [],
        "app": [],
        "bluetooth": [],
        "unknown": []
    }

    for log in logs:
        layers[log.layer].append({
            "timestamp": log.timestamp,
            "message": log.message,
            "line_no": log.line_no
        })

    # Aggregate errors
    errors = aggregate_errors(logs)

    # Extract state changes
    state_changes = extract_state_changes(logs)

    # Build timeline
    timeline = build_timeline(logs)

    return {
        "layers": layers,
        "errors": [asdict(e) for e in errors],
        "state_changes": [asdict(s) for s in state_changes],
        "timeline": timeline,
        "summary": {
            "total_lines": len(lines),
            "parsed_entries": len(logs),
            "error_count": len(errors),
            "state_change_count": len(state_changes)
        }
    }


# ============================================================================
# Bugreport & Multi-log Support
# ============================================================================

def parse_bugreport(
    bugreport_path: str,
    audio_keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Extract audio-related logs from Android bugreport.

    Args:
        bugreport_path: Path to bugreport tar.gz file
        audio_keywords: Keywords to filter audio-related content

    Returns:
        Dictionary with extracted audio logs
    """
    if audio_keywords is None:
        audio_keywords = [
            "audio", "AudioTrack", "AudioRecord",
            "AudioFlinger", "audio_hal", "ASoC",
            "snd_soc", "dsp", "afe", "codec"
        ]

    extracted = {
        "logcat": [],
        "dmesg": [],
        "system_properties": [],
        "audio_dumps": [],
        "libraries": []
    }

    try:
        with tarfile.open(bugreport_path, 'r:gz') as tar:
            for member in tar.getmembers():
                name = member.name.lower()

                # Extract logcat
                if 'logcat' in name and name.endswith('.txt'):
                    try:
                        f = tar.extractfile(member)
                        if f:
                            content = f.read().decode('utf-8', errors='ignore')
                            extracted["logcat"].append({
                                "file": member.name,
                                "lines": len(content.split('\n'))
                            })
                    except Exception:
                        continue

                # Extract dmesg
                elif 'dmesg' in name and name.endswith('.txt'):
                    try:
                        f = tar.extractfile(member)
                        if f:
                            content = f.read().decode('utf-8', errors='ignore')
                            extracted["dmesg"].append({
                                "file": member.name,
                                "lines": len(content.split('\n'))
                            })
                    except Exception:
                        continue

                # Extract system properties
                elif 'system_build' in name or 'prop' in name:
                    try:
                        f = tar.extractfile(member)
                        if f:
                            content = f.read().decode('utf-8', errors='ignore')
                            extracted["system_properties"].append({
                                "file": member.name,
                                "content_preview": content[:500]
                            })
                    except Exception:
                        continue

    except Exception as e:
        return {
            "error": str(e),
            "tip": "Provide bugreport as tar.gz file from adb bugreport"
        }

    return {
        "bugreport": extracted,
        "summary": {
            "logcat_files": len(extracted["logcat"]),
            "dmesg_files": len(extracted["dmesg"]),
            "prop_files": len(extracted["system_properties"])
        }
    }


def parse_dmesg(dmesg_text: str) -> Dict[str, Any]:
    """
    Parse kernel dmesg log for audio events.

    Args:
        dmesg_text: Raw dmesg text

    Returns:
        Dictionary with parsed kernel audio events
    """
    lines = dmesg_text.strip().split('\n')

    audio_events = []
    asoc_events = []
    dma_events = []
    clock_events = []

    # Audio-related kernel patterns
    AUDIO_KERNEL_PATTERNS = {
        "asoc": r"asoc-|snd_soc|Audio|PCM|CODEC|DAPM",
        "dma": r"DMA|dmaengine|xrun|underrun|overflow",
        "clock": r"clk_|clock|PLL|mclk|fsync",
        "machine": r"machine_driver|sound-card|Audiojack|HP|speaker"
    }

    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            continue

        # Parse dmesg timestamp [  123.456789]
        timestamp_match = re.match(r'\[\s*(\d+\.\d+)\]', line)
        if timestamp_match:
            timestamp = float(timestamp_match.group(1))
        else:
            timestamp = i  # Fallback to line number

        # Check for audio-related content
        line_lower = line.lower()
        for category, pattern in AUDIO_KERNEL_PATTERNS.items():
            if re.search(pattern, line_lower, re.IGNORECASE):
                entry = {
                    "timestamp": timestamp,
                    "line": i + 1,
                    "message": line.strip(),
                    "category": category
                }

                if category == "asoc":
                    asoc_events.append(entry)
                elif category == "dma":
                    dma_events.append(entry)
                elif category == "clock":
                    clock_events.append(entry)
                else:
                    audio_events.append(entry)
                break

    # Aggregate by category
    categorized = {
        "asoc": asoc_events,
        "dma": dma_events,
        "clock": clock_events,
        "other": audio_events
    }

    # Find error patterns
    error_patterns = [
        (r"xrun|underrun|overrun", "Buffer underrun/overrun"),
        (r"failed|error|-E\d+", "Error condition"),
        (r"timeout|ETIMEDOUT", "Timeout"),
        (r"dai.*not.*running|afe.*port.*start", "Port/DAI not running"),
        (r"pop|click|noise|clamp", "Audio artifact")
    ]

    errors_found = []
    for category, events in categorized.items():
        for event in events:
            for pattern, desc in error_patterns:
                if re.search(pattern, event["message"], re.IGNORECASE):
                    errors_found.append({
                        **event,
                        "error_type": desc
                    })
                    break

    return {
        "kernel_audio": categorized,
        "errors": errors_found,
        "summary": {
            "total_lines": len(lines),
            "asoc_events": len(asoc_events),
            "dma_events": len(dma_events),
            "clock_events": len(clock_events),
            "errors_found": len(errors_found)
        }
    }


def synthesize_logs(
    log_sources: Dict[str, str]
) -> Dict[str, Any]:
    """
    Synthesize multiple log sources into unified timeline.

    Args:
        log_sources: Dict of source_name -> log_text

    Returns:
        Unified timeline with cross-references
    """
    all_events = []
    source_metadata = {}

    for source_name, log_text in log_sources.items():
        source_metadata[source_name] = {
            "lines": len(log_text.split('\n')),
            "chars": len(log_text)
        }

        # Parse based on source type
        if source_name == "dmesg":
            parsed = parse_dmesg(log_text)
            for category, events in parsed.get("kernel_audio", {}).items():
                for event in events:
                    all_events.append({
                        **event,
                        "source": source_name,
                        "layer": "kernel"
                    })
        else:
            # Standard logcat parsing
            parsed = parse_log(log_text)
            for layer, entries in parsed.get("layers", {}).items():
                for entry in entries:
                    all_events.append({
                        **entry,
                        "source": source_name,
                        "layer": layer
                    })

    # Sort by timestamp (if available) or line number
    def sort_key(event):
        ts = event.get("timestamp", 0)
        if isinstance(ts, str):
            return 0
        return float(ts) if ts else event.get("line", 0)

    all_events.sort(key=sort_key)

    # Build unified timeline
    timeline = []
    for event in all_events[:500]:  # Limit to 500 events
        ts = event.get("timestamp", "")
        layer = event.get("layer", "")
        source = event.get("source", "")
        msg = event.get("message", "")[:100]

        timeline.append({
            "timestamp": ts,
            "layer": layer,
            "source": source,
            "message": msg
        })

    # Find cross-source correlations
    correlations = []
    error_events = [e for e in all_events if "error" in e.get("message", "").lower() or "-E" in e.get("message", "")]

    return {
        "timeline": timeline,
        "total_events": len(all_events),
        "sources": source_metadata,
        "cross_correlations": correlations[:10],  # Top 10 correlated errors
        "errors": error_events[:50]  # Top 50 errors
    }
