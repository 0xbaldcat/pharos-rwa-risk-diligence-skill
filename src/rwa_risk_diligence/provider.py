from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Protocol
from urllib.request import Request, urlopen

from .types import CentralizationPower, ContractSignalSet


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


class PharosLiveMockSignalProvider:
    """Read demo RWA risk signals from Pharos Atlantic mock contracts.

    This is a narrow read-only adapter for Phase 1 video demos. It only calls
    fixed view methods exposed by our mock contracts; it is not a generic source
    parser or arbitrary contract analyzer.
    """

    SELECTORS = {
        "owner": "0x8da5cb5b",
        "admin_type": "0x9f3342b6",
        "timelock_delay": "0xeef09bad",
        "mint_cap": "0x76c71ca1",
        "source_verified": "0xe7c1f248",
        "privileged_powers": "0x5c9e7d82",
        "is_upgradeable": "0xdaa3a163",
    }
    UINT256_MAX = (1 << 256) - 1

    def __init__(self, rpc_url: str, rpc_call: Optional[Callable[[str, Any], Any]] = None):
        if not rpc_url and rpc_call is None:
            raise ValueError("rpc_url is required for live mock provider")
        self._rpc_url = rpc_url
        self._rpc_call = rpc_call or self._default_rpc_call

    def collect_signals(self, chain_id: str, address: str, block: str = "latest") -> ContractSignalSet:
        block_tag = _block_tag(block)
        normalized = normalize_address(address)
        code = self._rpc_call("eth_getCode", [normalized, block_tag])
        if not code or code == "0x":
            raise ValueError("pharos live mock provider did not find contract code")

        owner = _decode_address(self._eth_call(normalized, self.SELECTORS["owner"], block_tag))
        admin_type = _decode_string(self._eth_call(normalized, self.SELECTORS["admin_type"], block_tag))
        timelock_delay = _decode_uint256(self._eth_call(normalized, self.SELECTORS["timelock_delay"], block_tag))
        mint_cap = _decode_uint256(self._eth_call(normalized, self.SELECTORS["mint_cap"], block_tag))
        source_verified = _decode_bool(self._eth_call(normalized, self.SELECTORS["source_verified"], block_tag))
        privileged_powers = _decode_string_array(
            self._eth_call(normalized, self.SELECTORS["privileged_powers"], block_tag)
        )
        is_upgradeable = _decode_bool(self._eth_call(normalized, self.SELECTORS["is_upgradeable"], block_tag))

        holder_type = _holder_type(admin_type)
        guarded_by_timelock = timelock_delay > 0
        guarded_by_multisig = admin_type == "multisig_timelock"
        centralization_powers = [
            CentralizationPower(
                power=power,
                holder=owner,
                holder_type=holder_type,
                guarded_by_timelock=guarded_by_timelock,
                guarded_by_multisig=guarded_by_multisig,
            )
            for power in privileged_powers
        ]

        return ContractSignalSet(
            address=address,
            chain_id=chain_id,
            block=block,
            asset_type="ERC20",
            code_present=True,
            proxy_type="mock-upgradeable" if is_upgradeable else None,
            source_verified=source_verified,
            owner=owner,
            owner_type="multisig" if guarded_by_multisig else ("EOA" if holder_type == "EOA" else "unknown"),
            admin_roles=["DEFAULT_ADMIN_ROLE"],
            centralization_powers=centralization_powers,
            privileged_functions=privileged_powers,
            mint_has_cap=mint_cap != self.UINT256_MAX,
            fee_has_upper_bound=True,
            timelock_min_delay_seconds=timelock_delay if timelock_delay > 0 else None,
            data_sources=["rpc:pharos-atlantic", "mock-view-methods"],
        )

    def _eth_call(self, address: str, selector: str, block_tag: str) -> str:
        return self._rpc_call("eth_call", [{"to": address, "data": selector}, block_tag])

    def _default_rpc_call(self, method: str, params: Any) -> Any:
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        request = Request(self._rpc_url, data=payload, headers={"content-type": "application/json"})
        with urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode())
        if "error" in body:
            raise ValueError(f"rpc error from {method}: {body['error']}")
        return body["result"]


def _block_tag(block: str) -> str:
    if block == "latest" or block.startswith("0x"):
        return block
    if block.isdigit():
        return hex(int(block))
    return block


def _hex_bytes(data: str) -> bytes:
    value = data[2:] if data.startswith("0x") else data
    return bytes.fromhex(value)


def _word(data: bytes, offset: int = 0) -> bytes:
    return data[offset : offset + 32]


def _word_int(data: bytes, offset: int = 0) -> int:
    return int.from_bytes(_word(data, offset), "big")


def _decode_address(data: str) -> str:
    raw = _word(_hex_bytes(data))
    return "0x" + raw[-20:].hex()


def _decode_uint256(data: str) -> int:
    return _word_int(_hex_bytes(data))


def _decode_bool(data: str) -> bool:
    return bool(_decode_uint256(data))


def _decode_string(data: str) -> str:
    raw = _hex_bytes(data)
    start = _word_int(raw)
    length = _word_int(raw, start)
    value_start = start + 32
    return raw[value_start : value_start + length].decode()


def _decode_string_array(data: str) -> List[str]:
    raw = _hex_bytes(data)
    array_start = _word_int(raw)
    count = _word_int(raw, array_start)
    values: List[str] = []
    for index in range(count):
        item_offset = _word_int(raw, array_start + 32 + index * 32)
        item_start = array_start + 32 + item_offset
        item_length = _word_int(raw, item_start)
        value_start = item_start + 32
        values.append(raw[value_start : value_start + item_length].decode())
    return values


def _holder_type(admin_type: str) -> str:
    if admin_type == "single_eoa":
        return "EOA"
    if admin_type == "multisig_timelock":
        return "MULTISIG"
    return "UNKNOWN"
