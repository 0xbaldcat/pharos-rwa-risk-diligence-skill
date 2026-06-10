from __future__ import annotations

from typing import List

from .provider import RiskSignalProvider
from .red_flags import match_red_flags
from .scoring import confidence_for, risk_level_from_flags, verdict_for
from .types import ContractSignalSet, DiligenceCheck, RedFlag, RiskMemo


class RiskDiligenceSkill:
    def __init__(self, provider: RiskSignalProvider):
        self._provider = provider

    def collect_contract_signals(self, chain_id: str, address: str, block: str = "latest") -> ContractSignalSet:
        return self._provider.collect_signals(chain_id, address, block)

    def match_red_flags(self, signals: ContractSignalSet) -> List[RedFlag]:
        return match_red_flags(signals)

    def summarize_risk_level(self, flags: List[RedFlag]) -> str:
        return risk_level_from_flags(flags)

    def generate_due_diligence_memo(self, chain_id: str, address: str, block: str = "latest") -> RiskMemo:
        signals = self.collect_contract_signals(chain_id, address, block)
        flags = self.match_red_flags(signals)
        risk_level = self.summarize_risk_level(flags)
        unknowns = unknowns_for(signals)
        return RiskMemo(
            address=signals.address,
            chain_id=signals.chain_id,
            block=signals.block,
            asset_type=signals.asset_type,
            risk_level=risk_level,
            confidence=confidence_for(signals),
            signals=signals.to_signals_json(),
            centralization_powers=signals.centralization_powers,
            red_flags=flags,
            dd_checklist=build_dd_checklist(signals, flags),
            unknowns=unknowns,
            data_sources=signals.data_sources,
        )

    def verdict(self, memo: RiskMemo, block_level: str = "CRITICAL", warn_level: str = "HIGH") -> str:
        return verdict_for(memo.risk_level, block_level=block_level, warn_level=warn_level)


def build_dd_checklist(signals: ContractSignalSet, flags: List[RedFlag]) -> List[DiligenceCheck]:
    flag_ids = {flag.id for flag in flags}
    return [
        DiligenceCheck(
            id="DD-1",
            status="UNKNOWN",
            note="Issuer identity is off-chain and must be verified from legal and disclosure documents.",
        ),
        DiligenceCheck(
            id="DD-2",
            status="FAIL" if "RF-01" in flag_ids or "RF-04" in flag_ids else "PASS",
            note="Upgrade governance is acceptable only when controlled by multisig and timelock.",
        ),
        DiligenceCheck(
            id="DD-3",
            status="FAIL" if "RF-02" in flag_ids else "PASS",
            note="Minting requires a cap and clear governance for tokenized assets.",
        ),
        DiligenceCheck(
            id="DD-4",
            status="WARN" if "RF-03" in flag_ids else "PASS",
            note="Pause, blacklist, and force-transfer powers are normal for compliant RWA tokens, but holder type matters.",
        ),
        DiligenceCheck(
            id="DD-5",
            status="FAIL" if "RF-05" in flag_ids else "PASS",
            note="Adjustable fees should have an enforceable upper bound.",
        ),
        DiligenceCheck(
            id="DD-6",
            status="UNKNOWN" if signals.source_verified is None else ("PASS" if signals.source_verified else "WARN"),
            note="Source verification depends on an optional explorer adapter.",
        ),
        DiligenceCheck(
            id="DD-7",
            status="UNKNOWN",
            note="Oracle or valuation dependencies are not proven by this base fixture.",
        ),
        DiligenceCheck(
            id="DD-8",
            status="UNKNOWN",
            note="Off-chain backing, custody, and redemption cannot be proven on-chain by this skill.",
        ),
    ]


def unknowns_for(signals: ContractSignalSet) -> List[str]:
    unknowns: List[str] = []
    if signals.source_verified is None:
        unknowns.append("source verification adapter not provided")
    elif signals.source_verified is False:
        unknowns.append("source is unverified, source-level review unavailable")
    if signals.upgradeable and not signals.implementation:
        unknowns.append("proxy implementation could not be resolved")
    if not signals.centralization_powers:
        unknowns.append("privileged holder classification unavailable")
    unknowns.append("issuer identity and off-chain asset backing require external verification")
    return unknowns
