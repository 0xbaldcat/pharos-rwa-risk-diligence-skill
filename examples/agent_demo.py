from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rwa_risk_diligence.cli import CHAIN_ID, CRITICAL_ADDRESS, LOW_ADDRESS, build_provider, demo_fixtures
from rwa_risk_diligence.engine import RiskDiligenceSkill
from rwa_risk_diligence.provider import FixtureRiskSignalProvider


SCENARIOS = [
    {
        "id": "rwa-allowlist-review",
        "request": "Review a Pharos RWA token before adding it to the allowlist.",
        "address": os.getenv("RWA_LOW_ADDRESS", LOW_ADDRESS),
    },
    {
        "id": "rwa-admin-risk-review",
        "request": "Check an upgradeable token with EOA admin before we trust it.",
        "address": os.getenv("RWA_CRITICAL_ADDRESS", CRITICAL_ADDRESS),
    },
]


def main() -> None:
    provider_name = os.getenv("RWA_PROVIDER", "fixture")
    rpc_url = os.getenv("PHAROS_RPC_URL", "")
    if provider_name == "fixture":
        provider = FixtureRiskSignalProvider(demo_fixtures())
    else:
        provider = build_provider(provider_name, rpc_url)
    skill = RiskDiligenceSkill(provider)
    block = os.getenv("RWA_BLOCK") or ("123456" if provider_name == "fixture" else "latest")
    print_json([run_scenario(skill, scenario, block) for scenario in SCENARIOS])


def run_scenario(skill: RiskDiligenceSkill, scenario: dict[str, str], block: str) -> dict[str, Any]:
    memo = skill.generate_due_diligence_memo(CHAIN_ID, scenario["address"], block=block)
    return {
        "scenario_id": scenario["id"],
        "request": scenario["request"],
        "triggered_skill": "rwa_risk_diligence",
        "primitive": "generate_due_diligence_memo",
        "decision": {
            "address": memo.address,
            "risk_level": memo.risk_level,
            "confidence": memo.confidence,
            "guardrail_verdict": skill.verdict(memo),
            "red_flags": [flag.id for flag in memo.red_flags],
            "failed_checks": [check.id for check in memo.dd_checklist if check.status == "FAIL"],
        },
    }


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
