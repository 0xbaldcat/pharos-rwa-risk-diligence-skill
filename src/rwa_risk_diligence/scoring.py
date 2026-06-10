from __future__ import annotations

from typing import List

from .types import ContractSignalSet, RedFlag


LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def risk_level_from_flags(flags: List[RedFlag]) -> str:
    severities = {flag.severity for flag in flags}
    if "CRITICAL" in severities:
        return "CRITICAL"
    if "HIGH" in severities:
        return "HIGH"
    if "MEDIUM" in severities:
        return "MEDIUM"
    return "LOW"


def confidence_for(signals: ContractSignalSet) -> float:
    confidence = 1.0
    if signals.source_verified is False:
        confidence -= 0.3
    if signals.upgradeable and not signals.implementation:
        confidence -= 0.2
    if any(power.holder_type == "UNKNOWN" for power in signals.centralization_powers):
        confidence -= 0.1
    return max(0.0, round(confidence, 2))


def verdict_for(risk_level: str, block_level: str = "CRITICAL", warn_level: str = "HIGH") -> str:
    level_index = LEVELS.index(risk_level)
    if level_index >= LEVELS.index(block_level):
        return "block"
    if level_index >= LEVELS.index(warn_level):
        return "warn"
    return "allow"
