"""Device Collector - Execute ADB commands to collect device diagnostic information."""
import subprocess
import json
from typing import Dict, List, Optional, Any


# Common diagnostic command bundles
DIAGNOSTIC_BUNDLES = {
    "audio_full": [
        "dumpsys media.audio_policy",
        "dumpsys audioflinger",
        "dumpsys audio",
        "cat /proc/asound/cards",
        "ls -la /dev/snd/",
        "getprop ro.build.version.sdk",
        "getprop ro.product.model",
        "getprop ro.hardware",
    ],
    "audio_playback": [
        "dumpsys audioflinger | grep -A10 PlaybackThreads",
        "cat /proc/asound/card0/pcm0p/sub0/status",
        "cat /proc/asound/card0/pcm0p/sub0/hw_params",
    ],
    "audio_capture": [
        "dumpsys audioflinger | grep -A10 RecordThread",
        "cat /proc/asound/card0/pcm0c/sub0/status",
        "cat /proc/asound/card0/pcm0c/sub0/hw_params",
    ],
    "kernel_audio": [
        "dmesg | grep -i audio",
        "dmesg | grep -i asoc",
        "dmesg | grep -i dma",
    ],
    "audio_properties": [
        "getprop | grep -i audio",
        "getprop | grep -i persist.audio",
    ]
}


def execute_adb_command(
    command: str,
    device_serial: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Execute single ADB command on device.

    Args:
        command: Shell command to execute
        device_serial: Optional device serial number
        timeout: Command timeout in seconds

    Returns:
        Dictionary with command output and status
    """
    try:
        cmd = ["adb"]
        if device_serial:
            cmd.extend(["-s", device_serial])
        cmd.extend(["shell", command])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "command": command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "stdout": "",
            "stderr": "Command timed out",
            "returncode": -1,
            "success": False
        }
    except FileNotFoundError:
        return {
            "command": command,
            "stdout": "",
            "stderr": "adb not found. Is Android SDK platform-tools installed?",
            "returncode": -2,
            "success": False
        }
    except Exception as e:
        return {
            "command": command,
            "stdout": "",
            "stderr": str(e),
            "returncode": -3,
            "success": False
        }


def execute_bundle(
    bundle_name: str,
    device_serial: Optional[str] = None,
    timeout_per_command: int = 30
) -> Dict[str, Any]:
    """
    Execute predefined diagnostic bundle.

    Args:
        bundle_name: Name of diagnostic bundle (audio_full, audio_playback, etc.)
        device_serial: Optional device serial number
        timeout_per_command: Timeout for each command

    Returns:
        Dictionary with all command results
    """
    if bundle_name not in DIAGNOSTIC_BUNDLES:
        return {
            "error": f"Unknown bundle: {bundle_name}",
            "available_bundles": list(DIAGNOSTIC_BUNDLES.keys())
        }

    commands = DIAGNOSTIC_BUNDLES[bundle_name]
    results = {}

    for cmd in commands:
        result = execute_adb_command(cmd, device_serial, timeout_per_command)
        results[cmd] = {
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "success": result["success"]
        }

    return results


def collect_device_info(device_serial: Optional[str] = None) -> Dict[str, Any]:
    """
    Collect basic device information.

    Args:
        device_serial: Optional device serial number

    Returns:
        Dictionary with device information
    """
    info = {}

    # Device properties
    props = [
        "ro.product.model",
        "ro.product.manufacturer",
        "ro.build.version.sdk",
        "ro.build.version.release",
        "ro.hardware",
        "ro.board.platform",
    ]

    for prop in props:
        result = execute_adb_command(f"getprop {prop}", device_serial)
        if result["success"]:
            info[prop] = result["stdout"]

    # Audio-related properties
    audio_props = execute_adb_command("getprop | grep -i audio", device_serial)
    if audio_props["success"]:
        info["audio_properties"] = audio_props["stdout"]

    return info


def get_audio_state(device_serial: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive audio state from device.

    Args:
        device_serial: Optional device serial number

    Returns:
        Dictionary with audio state information
    """
    state = {}

    # AudioFlinger state
    af_state = execute_adb_command("dumpsys audioflinger", device_serial)
    state["audioflinger"] = af_state["stdout"] if af_state["success"] else af_state["stderr"]

    # AudioPolicy state
    ap_state = execute_adb_command("dumpsys media.audio_policy", device_serial)
    state["audio_policy"] = ap_state["stdout"] if ap_state["success"] else ap_state["stderr"]

    # ALSA status
    alsa_cards = execute_adb_command("cat /proc/asound/cards", device_serial)
    state["alsa_cards"] = alsa_cards["stdout"] if alsa_cards["success"] else alsa_cards["stderr"]

    # Sound devices
    snd_devices = execute_adb_command("ls -la /dev/snd/", device_serial)
    state["sound_devices"] = snd_devices["stdout"] if snd_devices["success"] else snd_devices["stderr"]

    return state


def collect(
    commands: List[str],
    device_serial: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Execute custom commands on device.

    Args:
        commands: List of shell commands to execute
        device_serial: Optional device serial number
        timeout: Command timeout in seconds

    Returns:
        Dictionary with command results
    """
    results = {}
    errors = []

    for cmd in commands:
        result = execute_adb_command(cmd, device_serial, timeout)
        results[cmd] = result["stdout"] if result["success"] else result["stderr"]
        if not result["success"]:
            errors.append({
                "command": cmd,
                "error": result["stderr"]
            })

    return {
        "results": results,
        "errors": errors,
        "success_count": len(commands) - len(errors),
        "error_count": len(errors)
    }
