from rwa_risk_diligence import CentralizationPower, ContractSignalSet, RiskDiligenceSkill
from rwa_risk_diligence.cli import CHAIN_ID, CRITICAL_ADDRESS, LOW_ADDRESS, demo_fixtures
from rwa_risk_diligence.provider import FixtureRiskSignalProvider, PharosLiveMockSignalProvider


def build_skill():
    return RiskDiligenceSkill(FixtureRiskSignalProvider(demo_fixtures()))


def test_low_fixture_keeps_rwa_compliance_powers_in_context():
    memo = build_skill().generate_due_diligence_memo(CHAIN_ID, LOW_ADDRESS, block="123456")

    assert memo.risk_level == "LOW"
    assert memo.confidence == 1.0
    assert memo.red_flags == []
    assert build_skill().verdict(memo) == "allow"


def test_critical_fixture_matches_rf_01_and_rf_02():
    memo = build_skill().generate_due_diligence_memo(CHAIN_ID, CRITICAL_ADDRESS, block="123456")
    flag_ids = {flag.id for flag in memo.red_flags}

    assert memo.risk_level == "CRITICAL"
    assert "RF-01" in flag_ids
    assert "RF-02" in flag_ids
    assert "RF-03" in flag_ids
    assert "RF-04" in flag_ids
    assert "RF-10" in flag_ids
    assert memo.confidence == 0.7
    assert build_skill().verdict(memo) == "block"


def test_memo_schema_contains_required_sections():
    memo_json = build_skill().generate_due_diligence_memo(CHAIN_ID, CRITICAL_ADDRESS, block="123456").to_json()

    assert memo_json["address"] == CRITICAL_ADDRESS
    assert memo_json["chain_id"] == CHAIN_ID
    assert memo_json["block"] == "123456"
    assert memo_json["signals"]["S2_proxy_upgradeability"]["upgradeable"] is True
    assert len(memo_json["centralization_powers"]) == 3
    assert len(memo_json["dd_checklist"]) == 8
    assert "issuer identity and off-chain asset backing require external verification" in memo_json["unknowns"]
    assert "rpc:pharos-atlantic" in memo_json["data_sources"]


def test_source_unverified_reduces_confidence_without_autofailing():
    address = "0x4000000000000000000000000000000000000004"
    provider = FixtureRiskSignalProvider(
        {
            address: ContractSignalSet(
                address=address,
                chain_id=CHAIN_ID,
                block="123456",
                asset_type="ERC20",
                code_present=True,
                source_verified=False,
                owner="0xSafe000000000000000000000000000000000001",
                owner_type="multisig",
                centralization_powers=[
                    CentralizationPower(
                        power="pause",
                        holder="0xSafe000000000000000000000000000000000001",
                        holder_type="MULTISIG",
                        guarded_by_timelock=True,
                        guarded_by_multisig=True,
                    )
                ],
                privileged_functions=["pause", "blacklist"],
                mint_has_cap=True,
                data_sources=["fixture"],
            )
        }
    )

    memo = RiskDiligenceSkill(provider).generate_due_diligence_memo(CHAIN_ID, address, block="123456")

    assert memo.risk_level == "LOW"
    assert memo.confidence == 0.7
    assert [flag.id for flag in memo.red_flags] == ["RF-10"]


def test_unknown_holder_type_reduces_confidence():
    address = "0x5000000000000000000000000000000000000005"
    provider = FixtureRiskSignalProvider(
        {
            address: ContractSignalSet(
                address=address,
                chain_id=CHAIN_ID,
                block="123456",
                asset_type="ERC20",
                code_present=True,
                source_verified=True,
                centralization_powers=[
                    CentralizationPower(
                        power="upgrade",
                        holder="0xUnknown00000000000000000000000000000001",
                        holder_type="UNKNOWN",
                        guarded_by_timelock=False,
                        guarded_by_multisig=False,
                    )
                ],
                data_sources=["fixture"],
            )
        }
    )

    memo = RiskDiligenceSkill(provider).generate_due_diligence_memo(CHAIN_ID, address, block="123456")

    assert memo.confidence == 0.9


def test_live_mock_provider_reads_view_signals_for_low_risk_contract():
    address = "0x6000000000000000000000000000000000000006"
    owner = "0x7000000000000000000000000000000000000007"
    provider = PharosLiveMockSignalProvider(
        "https://rpc.test",
        rpc_call=build_mock_rpc(
            address,
            owner=owner,
            admin_type="multisig_timelock",
            timelock_delay=86400,
            mint_cap=1_000_000,
            source_verified=True,
            privileged_powers=["pause", "blacklist", "forceTransfer"],
            is_upgradeable=False,
        ),
    )

    memo = RiskDiligenceSkill(provider).generate_due_diligence_memo(CHAIN_ID, address)

    assert memo.risk_level == "LOW"
    assert RiskDiligenceSkill(provider).verdict(memo) == "allow"
    assert memo.signals["S3_ownership_admin"]["owner"] == owner.lower()
    assert memo.signals["S6_timelock"]["timelock_min_delay_seconds"] == 86400
    assert memo.data_sources == ["rpc:pharos-atlantic", "mock-view-methods"]


def test_live_mock_provider_reads_view_signals_for_critical_contract():
    address = "0x8000000000000000000000000000000000000008"
    owner = "0x9000000000000000000000000000000000000009"
    provider = PharosLiveMockSignalProvider(
        "https://rpc.test",
        rpc_call=build_mock_rpc(
            address,
            owner=owner,
            admin_type="single_eoa",
            timelock_delay=0,
            mint_cap=PharosLiveMockSignalProvider.UINT256_MAX,
            source_verified=False,
            privileged_powers=["mint", "pause", "blacklist", "forceTransfer", "upgrade"],
            is_upgradeable=True,
        ),
    )

    memo = RiskDiligenceSkill(provider).generate_due_diligence_memo(CHAIN_ID, address)
    flag_ids = {flag.id for flag in memo.red_flags}

    assert memo.risk_level == "CRITICAL"
    assert RiskDiligenceSkill(provider).verdict(memo) == "block"
    assert {"RF-01", "RF-02", "RF-03", "RF-04", "RF-10"}.issubset(flag_ids)
    assert memo.signals["S2_proxy_upgradeability"]["upgradeable"] is True


def build_mock_rpc(address, *, owner, admin_type, timelock_delay, mint_cap, source_verified, privileged_powers, is_upgradeable):
    selectors = PharosLiveMockSignalProvider.SELECTORS
    normalized_address = address.lower()
    responses = {
        selectors["owner"]: encode_address(owner),
        selectors["admin_type"]: encode_string(admin_type),
        selectors["timelock_delay"]: encode_uint(timelock_delay),
        selectors["mint_cap"]: encode_uint(mint_cap),
        selectors["source_verified"]: encode_bool(source_verified),
        selectors["privileged_powers"]: encode_string_array(privileged_powers),
        selectors["is_upgradeable"]: encode_bool(is_upgradeable),
    }

    def rpc(method, params):
        if method == "eth_getCode":
            assert params[0] == normalized_address
            return "0x60006000"
        if method == "eth_call":
            call = params[0]
            assert call["to"] == normalized_address
            return responses[call["data"]]
        raise AssertionError(f"unexpected rpc method {method}")

    return rpc


def encode_uint(value):
    return "0x" + int(value).to_bytes(32, "big").hex()


def encode_bool(value):
    return encode_uint(1 if value else 0)


def encode_address(value):
    raw = bytes.fromhex(value[2:])
    return "0x" + (b"\x00" * 12 + raw).hex()


def encode_string(value):
    data = value.encode()
    padded = data + b"\x00" * ((32 - len(data) % 32) % 32)
    return "0x" + (32).to_bytes(32, "big").hex() + len(data).to_bytes(32, "big").hex() + padded.hex()


def encode_string_array(values):
    encoded_items = []
    for value in values:
        data = value.encode()
        padded = data + b"\x00" * ((32 - len(data) % 32) % 32)
        encoded_items.append(len(data).to_bytes(32, "big") + padded)

    head_size = len(values) * 32
    offsets = []
    cursor = head_size
    for item in encoded_items:
        offsets.append(cursor.to_bytes(32, "big"))
        cursor += len(item)

    array_payload = len(values).to_bytes(32, "big") + b"".join(offsets) + b"".join(encoded_items)
    return "0x" + (32).to_bytes(32, "big").hex() + array_payload.hex()
