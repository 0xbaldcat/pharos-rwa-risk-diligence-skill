from __future__ import annotations

from typing import List

from .types import CentralizationPower, ContractSignalSet, RedFlag


def match_red_flags(signals: ContractSignalSet) -> List[RedFlag]:
    flags: List[RedFlag] = []
    eoa_upgrade_admin = _has_power(signals, power="upgrade", holder_type="EOA")
    eoa_compliance_admin = any(
        power.holder_type == "EOA"
        and power.power in {"blacklist", "forceTransfer", "pause"}
        for power in signals.centralization_powers
    )

    if signals.upgradeable and eoa_upgrade_admin and not _upgrade_guarded(signals):
        flags.append(
            RedFlag(
                id="RF-01",
                severity="CRITICAL",
                evidence="Upgradeable proxy is controlled by a single EOA without multisig or timelock protection.",
                explanation="The issuer can replace contract logic quickly, which can change token controls after review.",
            )
        )
    if "mint" in signals.privileged_functions and signals.mint_has_cap is False:
        flags.append(
            RedFlag(
                id="RF-02",
                severity="CRITICAL",
                evidence="Mint function is present and no supply cap was detected.",
                explanation="Unbounded minting can dilute holders or undermine asset-backing assumptions.",
            )
        )
    if {"blacklist", "forceTransfer"}.issubset(set(signals.privileged_functions)) and eoa_compliance_admin:
        flags.append(
            RedFlag(
                id="RF-03",
                severity="HIGH",
                evidence="Blacklist and forceTransfer controls are held by an EOA.",
                explanation="Compliance powers can be legitimate for RWA tokens, but EOA control creates seizure risk.",
            )
        )
    if signals.upgradeable and not _upgrade_guarded(signals):
        flags.append(
            RedFlag(
                id="RF-04",
                severity="HIGH",
                evidence="Upgradeable path has no detected timelock.",
                explanation="Instant upgrades leave holders exposed to sudden logic changes.",
            )
        )
    if "setFee" in signals.privileged_functions and signals.fee_has_upper_bound is False:
        flags.append(
            RedFlag(
                id="RF-05",
                severity="HIGH",
                evidence="Fee control exists and no hard upper bound was detected.",
                explanation="Fees can potentially be raised to punitive levels.",
            )
        )
    if signals.transfer_allowlist_required is True:
        flags.append(
            RedFlag(
                id="RF-06",
                severity="HIGH",
                evidence="Transfers require allowlisted senders and no public allowlist process is known.",
                explanation="Users may be unable to transfer unless a central operator permits it.",
            )
        )
    if signals.owner is None and signals.admin_roles:
        flags.append(
            RedFlag(
                id="RF-07",
                severity="MEDIUM",
                evidence="Admin roles exist but standard owner discovery is unavailable.",
                explanation="Non-standard ownership reduces review confidence.",
            )
        )
    if signals.proxy_admin and signals.deployer and signals.proxy_admin.lower() == signals.deployer.lower():
        flags.append(
            RedFlag(
                id="RF-08",
                severity="MEDIUM",
                evidence="Proxy admin matches deployer address.",
                explanation="The same deployer key appears to control upgrades.",
            )
        )
    if "sweep" in signals.privileged_functions or "withdraw" in signals.privileged_functions:
        if _has_any_eoa_holder(signals):
            flags.append(
                RedFlag(
                    id="RF-09",
                    severity="MEDIUM",
                    evidence="Withdraw or sweep capability can move assets to an EOA-controlled operator.",
                    explanation="Treasury or accidental token balances can be extracted by a privileged holder.",
                )
            )
    if signals.source_verified is False:
        flags.append(
            RedFlag(
                id="RF-10",
                severity="INFO",
                evidence="Source verification is unavailable or disabled.",
                explanation="Assessment confidence is reduced because source-level review is unavailable.",
            )
        )

    return flags


def _has_power(signals: ContractSignalSet, power: str, holder_type: str) -> bool:
    return any(item.power == power and item.holder_type == holder_type for item in signals.centralization_powers)


def _has_any_eoa_holder(signals: ContractSignalSet) -> bool:
    return any(item.holder_type == "EOA" for item in signals.centralization_powers)


def _upgrade_guarded(signals: ContractSignalSet) -> bool:
    upgrade_powers: List[CentralizationPower] = [
        power for power in signals.centralization_powers if power.power == "upgrade"
    ]
    if not upgrade_powers:
        return bool(signals.timelock_min_delay_seconds)
    return any(power.guarded_by_multisig and power.guarded_by_timelock for power in upgrade_powers)
