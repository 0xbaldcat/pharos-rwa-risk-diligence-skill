from __future__ import annotations

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rwa_risk_diligence.cli import (
    CRITICAL_ADDRESS,
    LOW_ADDRESS,
    PROVIDER_CHOICES,
    build_provider,
    default_chain_id,
    demo_fixtures,
)
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
    parser = argparse.ArgumentParser(description="Run agent-style RWA diligence scenarios")
    parser.add_argument("--provider", choices=PROVIDER_CHOICES, default=os.getenv("RWA_PROVIDER", "fixture"))
    parser.add_argument("--rpc-url", default=os.getenv("PHAROS_RPC_URL", ""))
    parser.add_argument("--chain-id", default=os.getenv("RWA_CHAIN_ID"))
    parser.add_argument("--block", default=os.getenv("RWA_BLOCK"))
    args = parser.parse_args()

    provider_name = args.provider
    if provider_name == "fixture":
        provider = FixtureRiskSignalProvider(demo_fixtures())
    else:
        provider = build_provider(provider_name, args.rpc_url)
    skill = RiskDiligenceSkill(provider)
    chain_id = args.chain_id or default_chain_id(provider_name)
    block = args.block or ("123456" if provider_name == "fixture" else "latest")
    print_json([run_scenario(skill, scenario, chain_id, block) for scenario in SCENARIOS])


def run_scenario(skill: RiskDiligenceSkill, scenario: dict[str, str], chain_id: str, block: str) -> dict[str, Any]:
    memo = skill.generate_due_diligence_memo(chain_id, scenario["address"], block=block)
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
