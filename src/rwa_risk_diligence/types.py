from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CentralizationPower:
    power: str
    holder: str
    holder_type: str
    guarded_by_timelock: bool
    guarded_by_multisig: bool

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RedFlag:
    id: str
    severity: str
    evidence: str
    explanation: str

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiligenceCheck:
    id: str
    status: str
    note: str

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskMemo:
    address: str
    chain_id: str
    block: str
    asset_type: str
    risk_level: str
    confidence: float
    signals: Dict[str, Any]
    centralization_powers: List[CentralizationPower]
    red_flags: List[RedFlag]
    dd_checklist: List[DiligenceCheck]
    unknowns: List[str]
    data_sources: List[str]

    def to_json(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "chain_id": self.chain_id,
            "block": self.block,
            "asset_type": self.asset_type,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "signals": self.signals,
            "centralization_powers": [power.to_json() for power in self.centralization_powers],
            "red_flags": [flag.to_json() for flag in self.red_flags],
            "dd_checklist": [check.to_json() for check in self.dd_checklist],
            "unknowns": self.unknowns,
            "data_sources": self.data_sources,
        }


@dataclass(frozen=True)
class ContractSignalSet:
    address: str
    chain_id: str
    block: str
    asset_type: str
    code_present: bool
    proxy_type: Optional[str] = None
    implementation: Optional[str] = None
    proxy_admin: Optional[str] = None
    source_verified: Optional[bool] = None
    owner: Optional[str] = None
    owner_type: Optional[str] = None
    admin_roles: List[str] = field(default_factory=list)
    centralization_powers: List[CentralizationPower] = field(default_factory=list)
    privileged_functions: List[str] = field(default_factory=list)
    mint_has_cap: Optional[bool] = None
    fee_has_upper_bound: Optional[bool] = None
    transfer_allowlist_required: Optional[bool] = None
    timelock_min_delay_seconds: Optional[int] = None
    holder_concentration_top10_percent: Optional[float] = None
    deployer: Optional[str] = None
    data_sources: List[str] = field(default_factory=list)

    @property
    def upgradeable(self) -> bool:
        return self.proxy_type is not None or self.implementation is not None

    def to_signals_json(self) -> Dict[str, Any]:
        return {
            "S1_existence_type": {
                "code_present": self.code_present,
                "asset_type": self.asset_type,
            },
            "S2_proxy_upgradeability": {
                "proxy_type": self.proxy_type,
                "implementation": self.implementation,
                "proxy_admin": self.proxy_admin,
                "upgradeable": self.upgradeable,
            },
            "S3_ownership_admin": {
                "owner": self.owner,
                "owner_type": self.owner_type,
                "admin_roles": self.admin_roles,
            },
            "S4_privileged_functions": self.privileged_functions,
            "S5_token_economics": {
                "mint_has_cap": self.mint_has_cap,
                "fee_has_upper_bound": self.fee_has_upper_bound,
                "holder_concentration_top10_percent": self.holder_concentration_top10_percent,
            },
            "S6_timelock": {
                "timelock_min_delay_seconds": self.timelock_min_delay_seconds,
            },
            "S7_source_verification": {
                "source_verified": self.source_verified,
            },
        }
