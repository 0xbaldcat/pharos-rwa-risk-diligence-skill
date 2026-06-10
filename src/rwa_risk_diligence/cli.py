from __future__ import annotations

import argparse
import json
from typing import Any

from .engine import RiskDiligenceSkill
from .provider import FixtureRiskSignalProvider
from .types import CentralizationPower, ContractSignalSet


CHAIN_ID = "688688"
LOW_ADDRESS = "0x1000000000000000000000000000000000000001"
CRITICAL_ADDRESS = "0x2000000000000000000000000000000000000002"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an offline RWA risk diligence demo")
    parser.add_argument("--chain-id", default=CHAIN_ID)
    parser.add_argument("--address", default=CRITICAL_ADDRESS)
    args = parser.parse_args()

    skill = RiskDiligenceSkill(FixtureRiskSignalProvider(demo_fixtures()))
    memo = skill.generate_due_diligence_memo(args.chain_id, args.address, block="123456")
    payload = memo.to_json()
    payload["guardrail_verdict"] = skill.verdict(memo)
    print_json(payload)


def demo_fixtures() -> dict:
    return {
        LOW_ADDRESS: ContractSignalSet(
            address=LOW_ADDRESS,
            chain_id=CHAIN_ID,
            block="123456",
            asset_type="ERC20",
            code_present=True,
            source_verified=True,
            owner="0xSafe000000000000000000000000000000000001",
            owner_type="multisig",
            admin_roles=["DEFAULT_ADMIN_ROLE"],
            centralization_powers=[
                CentralizationPower(
                    power="pause",
                    holder="0xSafe000000000000000000000000000000000001",
                    holder_type="MULTISIG",
                    guarded_by_timelock=True,
                    guarded_by_multisig=True,
                )
            ],
            privileged_functions=["pause", "blacklist", "forceTransfer"],
            mint_has_cap=True,
            fee_has_upper_bound=True,
            timelock_min_delay_seconds=86400,
            data_sources=["fixture", "rpc:pharos-testnet"],
        ),
        CRITICAL_ADDRESS: ContractSignalSet(
            address=CRITICAL_ADDRESS,
            chain_id=CHAIN_ID,
            block="123456",
            asset_type="ERC20",
            code_present=True,
            proxy_type="transparent",
            implementation="0x3000000000000000000000000000000000000003",
            proxy_admin="0xAdmin000000000000000000000000000000000001",
            source_verified=False,
            owner="0xAdmin000000000000000000000000000000000001",
            owner_type="EOA",
            admin_roles=["DEFAULT_ADMIN_ROLE"],
            centralization_powers=[
                CentralizationPower(
                    power="upgrade",
                    holder="0xAdmin000000000000000000000000000000000001",
                    holder_type="EOA",
                    guarded_by_timelock=False,
                    guarded_by_multisig=False,
                ),
                CentralizationPower(
                    power="blacklist",
                    holder="0xAdmin000000000000000000000000000000000001",
                    holder_type="EOA",
                    guarded_by_timelock=False,
                    guarded_by_multisig=False,
                ),
                CentralizationPower(
                    power="forceTransfer",
                    holder="0xAdmin000000000000000000000000000000000001",
                    holder_type="EOA",
                    guarded_by_timelock=False,
                    guarded_by_multisig=False,
                ),
            ],
            privileged_functions=["mint", "pause", "blacklist", "forceTransfer", "upgradeTo"],
            mint_has_cap=False,
            fee_has_upper_bound=True,
            timelock_min_delay_seconds=None,
            holder_concentration_top10_percent=76.5,
            deployer="0xAdmin000000000000000000000000000000000001",
            data_sources=["fixture", "rpc:pharos-testnet"],
        ),
    }


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
