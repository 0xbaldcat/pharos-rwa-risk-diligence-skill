# Test Checklist

- Memo output matches the required schema: address, chain_id, block, asset_type, risk_level, confidence, signals, centralization_powers, red_flags, dd_checklist, unknowns, data_sources.
- RWA compliance powers are handled with holder context: multisig plus timelock remains LOW, single EOA control can become HIGH or CRITICAL.
- RF-01, RF-02, RF-03, RF-04, and RF-10 are covered by the critical offline fixture.
- Source-unverified state reduces confidence without automatically failing the asset.
- Guardrail verdict maps CRITICAL to block, HIGH to warn, lower levels to allow by default.
- Demo CLI runs without network access.
- Future live provider tests must mock Pharos RPC responses by default.
