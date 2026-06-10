from rwa_risk_diligence import CentralizationPower, ContractSignalSet, RiskDiligenceSkill
from rwa_risk_diligence.cli import CHAIN_ID, CRITICAL_ADDRESS, LOW_ADDRESS, demo_fixtures
from rwa_risk_diligence.provider import FixtureRiskSignalProvider


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
    assert "rpc:pharos-testnet" in memo_json["data_sources"]


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
