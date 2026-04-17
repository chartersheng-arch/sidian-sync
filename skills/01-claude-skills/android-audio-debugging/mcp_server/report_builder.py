"""Report Builder - Generate structured Markdown diagnosis reports."""
from typing import Dict, List, Optional, Any
from datetime import datetime


def format_evidence(evidence: List[Dict[str, str]]) -> str:
    """Format evidence list as markdown table."""
    if not evidence:
        return "_无_"

    lines = ["| 证据 | 来源 |", "|------|------|"]
    for e in evidence:
        lines.append(f"| {e.get('content', '')} | {e.get('source', '')} |")

    return "\n".join(lines)


def format_hypothesis_table(hypotheses: List[Dict[str, Any]]) -> str:
    """Format hypothesis list as markdown table."""
    if not hypotheses:
        return "_无_"

    lines = [
        "| 假设 | 置信度 | 支持证据 | 缺失证据 |",
        "|------|--------|----------|----------|"
    ]

    for h in hypotheses:
        confidence = h.get("confidence", "中")
        evidence = h.get("supporting_evidence", [])
        missing = h.get("missing_evidence", [])

        evidence_str = ", ".join(evidence) if evidence else "_无_"
        missing_str = ", ".join(missing) if missing else "_无_"

        lines.append(f"| {h.get('description', '')} | {confidence} | {evidence_str} | {missing_str} |")

    return "\n".join(lines)


def format_fix_suggestions(fixes: List[Dict[str, Any]]) -> str:
    """Format fix suggestions as priority table."""
    if not fixes:
        return "_无_"

    lines = [
        "| 优先级 | 方案 | 改动范围 | 风险 |",
        "|--------|------|----------|------|"
    ]

    for f in fixes:
        priority = f.get("priority", "P1")
        solution = f.get("solution", "")
        scope = f.get("scope", "")
        risk = f.get("risk", "低")

        lines.append(f"| {priority} | {solution} | {scope} | {risk} |")

    return "\n".join(lines)


def format_verification_plan(plan: List[Dict[str, str]]) -> str:
    """Format verification plan as checklist."""
    if not plan:
        return "_无_"

    lines = []
    for i, item in enumerate(plan, 1):
        method = item.get("method", "")
        expected = item.get("expected", "")
        criteria = item.get("criteria", "")

        lines.append(f"{i}. **验证方法**: {method}")
        lines.append(f"   - 预期结果: {expected}")
        lines.append(f"   - 判断标准: {criteria}")
        lines.append("")

    return "\n".join(lines)


def build_report(
    title: str = "Android Audio 问题诊断报告",
    device_info: Optional[str] = None,
    phenomenon: str = "",
    problem_type: str = "",
    impact_scope: str = "",
    reproduction_rate: str = "",
    evidence_chain: Optional[List[Dict[str, str]]] = None,
    hypothesis_table: Optional[List[Dict[str, Any]]] = None,
    matched_cases: Optional[List[str]] = None,
    root_cause: str = "",
    root_cause_analysis: str = "",
    fix_suggestions: Optional[List[Dict[str, Any]]] = None,
    verification_plan: Optional[List[Dict[str, str]]] = None,
    attachments: Optional[List[str]] = None,
    notes: Optional[Dict[str, str]] = None
) -> str:
    """
    Build a structured Markdown diagnosis report.

    Args:
        title: Report title
        device_info: Device information string
        phenomenon: Problem phenomenon description
        problem_type: Problem type (无声/杂音/延迟/爆音/断续)
        impact_scope: Impact scope description
        reproduction_rate: Reproduction rate (必现/偶发/条件触发)
        evidence_chain: List of evidence dictionaries
        hypothesis_table: List of hypothesis dictionaries
        matched_cases: List of matched case titles
        root_cause: Root cause description
        root_cause_analysis: Root cause analysis
        fix_suggestions: List of fix suggestion dictionaries
        verification_plan: List of verification plan dictionaries
        attachments: List of attachment descriptions
        notes: Additional notes dictionary

    Returns:
        Markdown formatted report string
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# {title}",
        "",
        f"**生成时间**: {now}",
        "",
        "---",
        "",
        "## 基本信息",
        "",
    ]

    if device_info:
        lines.append(f"- **设备**: {device_info}")

    if problem_type:
        lines.append(f"- **问题类型**: {problem_type}")

    if impact_scope:
        lines.append(f"- **影响范围**: {impact_scope}")

    if reproduction_rate:
        lines.append(f"- **复现率**: {reproduction_rate}")

    lines.extend(["", "## 问题现象", "", phenomenon, ""])

    # Analysis section
    lines.extend(["", "---", "", "## 分析过程", ""])

    if evidence_chain:
        lines.extend(["", "### 证据链", ""])
        lines.append(format_evidence(evidence_chain))
        lines.append("")

    if hypothesis_table:
        lines.extend(["", "### 根因假设", ""])
        lines.append(format_hypothesis_table(hypothesis_table))
        lines.append("")

    if matched_cases:
        lines.extend(["", "### 匹配案例", ""])
        for case in matched_cases:
            lines.append(f"- {case}")
        lines.append("")

    # Conclusion section
    lines.extend(["", "---", "", "## 根因结论", ""])

    if root_cause:
        lines.extend(["", "### 直接原因", "", root_cause, ""])

    if root_cause_analysis:
        lines.extend(["", "### 根因分析", "", root_cause_analysis, ""])

    # Fix suggestions
    if fix_suggestions:
        lines.extend(["", "---", "", "## 修复建议", ""])
        lines.append(format_fix_suggestions(fix_suggestions))
        lines.append("")

    # Verification plan
    if verification_plan:
        lines.extend(["", "---", "", "## 验证计划", ""])
        lines.append(format_verification_plan(verification_plan))
        lines.append("")

    # Attachments
    if attachments:
        lines.extend(["", "---", "", "## 附件", ""])
        for att in attachments:
            lines.append(f"- {att}")
        lines.append("")

    # Notes
    if notes:
        lines.extend(["", "---", "", "## 备注", ""])
        for key, value in notes.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")

    lines.extend(["", "---", "", "_报告由 Android Audio Debugging Skill 自动生成_", ""])

    return "\n".join(lines)


def build_simple_report(
    title: str,
    phenomenon: str,
    root_cause: str,
    solution: str
) -> str:
    """
    Build a simple report with basic information.

    Args:
        title: Report title
        phenomenon: Problem description
        root_cause: Root cause
        solution: Solution

    Returns:
        Markdown formatted simple report
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""# {title}

**生成时间**: {now}

## 问题现象
{phenomenon}

## 根因
{root_cause}

## 解决方案
{solution}

---
_报告由 Android Audio Debugging Skill 自动生成_
"""
