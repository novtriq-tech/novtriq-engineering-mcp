# NOVTRIQ Engineering Intelligence MCP

An MCP (Model Context Protocol) server exposing 27 engineering intelligence tools for
data centres and critical facilities, building energy and carbon, UK building
regulations, Eurocode structural and cost, cyber and certification, and UAE compliance.

This repository is the open, self-hostable catalogue face of the NOVTRIQ MCP. It
advertises the full tool set so any MCP client or aggregator can discover it, and it
forwards tool execution to the authoritative hosted endpoint. The engineering
calculators themselves run on the hosted service.

- Hosted endpoint: `https://api.novtriq.tech/mcp` (streamable-http, keyless free tier)
- Transport: JSON-RPC 2.0 over HTTP
- Tools: 27
- Provider: NOVTRIQ, UK engineering intelligence

## Use the hosted server directly

Most clients should point straight at the hosted endpoint. Example MCP client config:

```json
{
  "mcpServers": {
    "novtriq-engineering": {
      "url": "https://api.novtriq.tech/mcp"
    }
  }
}
```

The free tier is keyless (5 requests/minute, 500/month per address). Higher tiers and
API keys are available at https://novtriq.tech/eaas.

## Run this catalogue server locally

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8080
```

Or with Docker:

```bash
docker build -t novtriq-engineering-mcp .
docker run -p 8080:8080 novtriq-engineering-mcp
```

Then:

```bash
curl -s -X POST http://localhost:8080/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

`initialize`, `tools/list`, `resources/list` and `prompts/list` are answered locally.
`tools/call` is forwarded to the hosted endpoint (override with the
`NOVTRIQ_MCP_UPSTREAM` environment variable).

## Tool catalogue

### Data centres and critical facilities
`calculate_pue` (IEC 30134-2 / ASHRAE TC 9.9), `estimate_cooling_load` (CIBSE Guide B2 /
ASHRAE 90.1), `thermal_load`, `eed_datacentre_pack` (EU 2023/1791 Art.12, Reg 2024/1364)

### Building energy, carbon and EPC
`assess_epbd_score` (EU 2024/1275), `calculate_carbon` (CIBSE TM65 / RICS WLCA),
`building_carbon_footprint` (CRREM), `sap_sbem_precheck` (UK SAP 10.3 / SBEM),
`mees_checker`, `heatpump_heatloss` (BS EN 12831 / MCS), `digital_renovation_passport`,
`building_readiness`

### UK building regulations
`part_o_overheating` (Approved Document O), `part_s_ev` (Approved Document S),
`uk_planning_checker` (GPDO 2015)

### Structural and cost
`eurocode_beam_designer` (EC3 / EC2), `eurocode_column_checker` (EC3),
`eu_cost_benchmarking`, `get_technical_dd_quote` (RICS / CIBSE), `roi_calculator`

### Cyber and certification
`check_nis2_readiness` (EU 2022/2555), `dgnb_bim_readiness` (ISO 19650),
`contractor_vetting`

### UAE
`check_uae_bim_compliance` (Dubai Circular 196, ISO 19650), `check_uae_cybersecurity`
(NESA / Dubai ISR / CBUAE / TDRA), `check_grid_feasibility_uae` (DEWA / ADDC / SEWA /
FEWA), `uae_climate_ghg` (Federal Decree-Law No. 11 of 2024)

The full JSON Schema for every tool is in [`tools.json`](tools.json).

## Notes

Tool outputs are indicative engineering estimates and should be validated by a
qualified engineer against current standards and site specific data.

## License

MIT. See [LICENSE](LICENSE).
