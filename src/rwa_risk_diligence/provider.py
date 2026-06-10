from __future__ import annotations

from typing import Dict, Protocol

from .types import ContractSignalSet


class RiskSignalProvider(Protocol):
    def collect_signals(self, chain_id: str, address: str, block: str = "latest") -> ContractSignalSet:
        ...


class FixtureRiskSignalProvider:
    def __init__(self, fixtures: Dict[str, ContractSignalSet]):
        self._fixtures = {normalize_address(address): signals for address, signals in fixtures.items()}

    def collect_signals(self, chain_id: str, address: str, block: str = "latest") -> ContractSignalSet:
        signals = self._fixtures.get(normalize_address(address))
        if signals is None:
            raise ValueError("fixture provider does not contain requested address")
        if signals.chain_id != chain_id:
            raise ValueError("fixture provider does not contain requested chain")
        return signals


def normalize_address(address: str) -> str:
    return address.strip().lower()
