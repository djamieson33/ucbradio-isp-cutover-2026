from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from config import LintConfig

Severity = Literal["ERROR", "WARN", "INFO"]


@dataclass
class Finding:
    severity: Severity
    rule: str
    file: str
    message: str
    pointer: str | None = None


class Reporter:
    def __init__(self, cfg: LintConfig):
        self.cfg = cfg
        self.findings: list[Finding] = []

    def error(self, rule: str, path: Path, message: str, pointer: str | None = None) -> None:
        self.findings.append(Finding("ERROR", rule, str(path), message, pointer))

    def warn(self, rule: str, path: Path, message: str, pointer: str | None = None) -> None:
        self.findings.append(Finding("WARN", rule, str(path), message, pointer))

    def info(self, rule: str, path: Path, message: str, pointer: str | None = None) -> None:
        self.findings.append(Finding("INFO", rule, str(path), message, pointer))

    def _print_text(self) -> None:
        if not self.findings:
            print("[OK] No lint findings.")
            return

        for f in self.findings:
            loc = f.file
            if f.pointer:
                loc = f"{loc}:{f.pointer}"
            print(f"[{f.severity}] {f.rule} :: {loc} :: {f.message}")

        counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
        for f in self.findings:
            counts[f.severity] += 1
        print(f"\nSummary: {counts['ERROR']} errors, {counts['WARN']} warnings, {counts['INFO']} info")

    def _print_json(self) -> None:
        payload: list[dict[str, Any]] = [
            {
                "severity": f.severity,
                "rule": f.rule,
                "file": f.file,
                "pointer": f.pointer,
                "message": f.message,
            }
            for f in self.findings
        ]
        print(json.dumps({"findings": payload}, indent=2))

    def flush(self) -> None:
        if self.cfg.output_format == "json":
            self._print_json()
        else:
            self._print_text()

    def exit_code(self) -> int:
        # strict => any WARN counts as failure too
        has_error = any(f.severity == "ERROR" for f in self.findings)
        has_warn = any(f.severity == "WARN" for f in self.findings)

        self.flush()

        if has_error:
            return 2
        if self.cfg.strict and has_warn:
            return 2
        return 0
