#!/usr/bin/env python3
"""Convert a Bandit text report into a clean, organised Markdown summary."""

import re
import sys
from pathlib import Path

SEVERITY_ICON = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🔵"}


def parse_issues(text: str):
    """Extract individual issue blocks from a Bandit text report."""
    issues = []
    blocks = re.split(r"-{10,}", text)
    for block in blocks:
        if ">> Issue:" not in block:
            continue

        issue = {}
        issue["title"] = _search(r">> Issue: \[(.*?)\] (.*?)\n", block, group=2)
        issue["test_id"] = _search(r">> Issue: \[(.*?):", block)
        issue["severity"] = _search(r"Severity: (\w+)", block).upper()
        issue["confidence"] = _search(r"Confidence: (\w+)", block)
        issue["cwe"] = _search(r"CWE: (CWE-\d+)", block)
        issue["location"] = _search(r"Location: (.*?)\n", block)

        # Capture the code snippet lines (numbered lines after the metadata).
        code_lines = re.findall(r"^\s*\d+\s+.*$", block, re.MULTILINE)
        issue["code"] = "\n".join(line.strip() for line in code_lines)
        issues.append(issue)
    return issues


def parse_metrics(text: str):
    """Extract the run metrics summary."""
    metrics = {}
    metrics["loc"] = _search(r"Total lines of code: (\d+)", text)
    metrics["high"] = _search(r"High: (\d+)", text)
    metrics["medium"] = _search(r"Medium: (\d+)", text)
    metrics["low"] = _search(r"Low: (\d+)", text)
    return metrics


def _search(pattern: str, text: str, group: int = 1) -> str:
    match = re.search(pattern, text)
    return match.group(group).strip() if match else "N/A"


def build_markdown(issues, metrics) -> str:
    out = []
    out.append("# 🛡️ Bandit SAST Report\n")

    # Summary box
    out.append("## 📊 Summary\n")
    out.append("| Metric | Value |")
    out.append("| :--- | :--- |")
    out.append(f"| 📝 Lines of Code Scanned | **{metrics['loc']}** |")
    out.append(f"| 🔴 High Severity | **{metrics['high']}** |")
    out.append(f"| 🟠 Medium Severity | **{metrics['medium']}** |")
    out.append(f"| 🔵 Low Severity | **{metrics['low']}** |")
    out.append(f"| 🧮 Total Issues | **{len(issues)}** |\n")

    # Issues table overview
    out.append("## 🔍 Issues Overview\n")
    out.append("| # | Severity | Test ID | Issue | Location |")
    out.append("| :-: | :--- | :--- | :--- | :--- |")
    for i, issue in enumerate(issues, 1):
        icon = SEVERITY_ICON.get(issue["severity"], "")
        out.append(
            f"| {i} | {icon} {issue['severity']} | `{issue['test_id']}` | "
            f"{issue['title']} | `{issue['location']}` |"
        )
    out.append("")

    # Detailed breakdown
    out.append("## 📋 Detailed Findings\n")
    for i, issue in enumerate(issues, 1):
        icon = SEVERITY_ICON.get(issue["severity"], "")
        out.append(f"### {icon} Issue #{i}: {issue['title']}\n")
        out.append(f"- **Severity:** {issue['severity']}")
        out.append(f"- **Confidence:** {issue['confidence']}")
        out.append(f"- **Test ID:** `{issue['test_id']}`")
        out.append(
            f"- **CWE:** [{issue['cwe']}]"
            f"(https://cwe.mitre.org/data/definitions/"
            f"{issue['cwe'].replace('CWE-', '')}.html)"
        )
        out.append(f"- **Location:** `{issue['location']}`\n")
        if issue["code"]:
            out.append("```python")
            out.append(issue["code"])
            out.append("```\n")

    return "\n".join(out)


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "bandit_report.txt")
    if not src.exists():
        print(f"❌ File not found: {src}")
        sys.exit(1)

    text = src.read_text(encoding="utf-8")
    issues = parse_issues(text)
    metrics = parse_metrics(text)
    markdown = build_markdown(issues, metrics)

    out_file = src.with_suffix(".md")
    out_file.write_text(markdown, encoding="utf-8")
    print(f"✅ Clean report written to: {out_file}")


if __name__ == "__main__":
    main()
