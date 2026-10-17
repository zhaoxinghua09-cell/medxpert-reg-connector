# MedXpert Global Regulatory Connector (reg-connector)

## License Notice

- **Code**: The source code of this repository is released under **Apache-2.0** (see [LICENSE](LICENSE)), copyright by 赵兴华 / Steven Zhao·China (ORCID 0009-0001-0512-1237).
- **Knowledge base / methodology**: The bundled knowledge base, `references/`, synthesized regulatory knowledge, retrieval methodology, classification system and editorial structure are **All Rights Reserved** (see [CONTENT-LICENSE](CONTENT-LICENSE)); they may be quoted with attribution for academic or public discussion, but may not be copied, adapted, redistributed, resold, or used to train models without prior written permission.
- **Brand status**: MedXpert, SynomosAI, LGD and similar names are project identifiers only; none is a registered legal entity or registered trademark. Their use is for source identification and does not assert any legal-entity or trademark rights.
- **Disclaimer**: This repository does not constitute regulatory, legal, or registration-agent advice. For critical decisions, always refer to the latest official publications of the competent authority.
- **Contact**: zhaoxinghua09@gmail.com ｜ ORCID 0009-0001-0512-1237

---

The public interface of the MedXpert medical-device line. It packages a global medical-device regulatory knowledge base (27 hub documents covering **NMPA / FDA / EU MDR / PMDA and global orthopedic registration pathways**) into a **local, read-only MCP server** that any MCP client (WorkBuddy / Claude Code / Cursor, etc.) can invoke for retrieval.

- 🔒 **Local-only, read-only: zero network egress, zero credentials**
- 📚 27 regulatory hubs with a custom Chinese-friendly BM25 approximate retrieval engine
- 🧰 4 tools: `list_hubs` / `search_regulation` / `get_hub` / `ask_classification`

> Complementary to the `medxpert-reg-hub` knowledge skill: reg-hub lets an agent **read** knowledge; reg-connector lets an agent **call** retrieval.

## Quick Start

```bash
pip install fastmcp
```

Clone this repository and add it to your host's `mcp.json`:

```json
{
  "mcpServers": {
    "@nomos/medxpert/reg-connector": {
      "command": "<your python interpreter path>",
      "args": ["<repository dir>/reg_connector_server.py"],
      "disabled": false,
      "description": "MedXpert Global Regulatory Connector: local read-only retrieval across global medical-device regulation hubs (NMPA/FDA/MDR/PMDA, 27 hubs)"
    }
  }
}
```

Reload the MCP connection. `references/` must sit next to `reg_connector_server.py` (clone-and-run); alternatively set the `REG_HUB_REFS` environment variable to point at a custom knowledge-base directory.

> **Install via PyPI (`pip install medxpert-reg-connector`)**: the package ships the server itself but **not the 27 knowledge hubs** (size and licensing considerations — the knowledge base is distributed with this repository). After installing, clone this repository's `references/` and point `REG_HUB_REFS=<repo dir>/references` at it, or use the "clone-and-run" flow above.

## Tools

| Tool | Input | Returns | Purpose |
|------|-------|---------|---------|
| `list_hubs()` | none | all hubs (hub_key / title / sections / official_links / phase) | Overview of the knowledge base |
| `search_regulation(query, top_k=5, hub_filter=None)` | keywords (CN/EN/regulation number, e.g. `UDI`/`510k`/`MDR PMS`/`委托生产`) | matched hub_key/title/section/snippet/score/links | Regulation entry retrieval |
| `get_hub(hub_key)` | hub key (from `list_hubs`) | full text + official links | Retrieve a full hub document |
| `ask_classification(product)` | product description (e.g. `骨科金属接骨板`) | matches + recommended_hubs + hint | Quick classification & registration-path lookup |

## Usage Examples

```python
# List all 27 hubs
list_hubs()

# Search UDI multi-country comparison
search_regulation("UDI", top_k=3)
# → hits the "UDI global identifier hub": CN/US/EU/JP in parallel (GS1/MA/AliHealth, GUDID, EUDAMED, KikiDB)

# Bone-plate classification and pathway
ask_classification("骨科金属接骨板")
# → recommended hubs: orthopedic-instrument_global-registration-path, registration-engineer, registration-cycle-cost-validity-comparison ...
```

## Typical Scenarios

- Registration-path lookup (China Class II cycle/cost, real registration-certificate examples)
- UDI comparison across the CN/US/EU/JP systems
- Indexing for clinical evaluation and risk management (ISO 14971) materials
- Global orthopedic registration-path compilation

## Notes & Boundaries

1. **Returns knowledge-base leads, not official conclusions.** Classification and registration paths must be confirmed against the target market's official classification sources (NMPA / FDA / MDR).
2. Local-only and read-only, with zero egress — suitable for intranet / compliance environments.
3. Reload the server after the knowledge base is updated.
4. Optional `REG_HUB_REFS` to point at a custom knowledge-base directory.

## License & Attribution

Source code: **Apache-2.0** (see [LICENSE](LICENSE)), copyright by 赵兴华 / Steven Zhao·China (ORCID 0009-0001-0512-1237). The bundled knowledge base / `references/` / synthesized regulatory knowledge / retrieval methodology / classification system are **All Rights Reserved** (see [CONTENT-LICENSE](CONTENT-LICENSE)); they may be quoted with attribution, but not copied, resold, or used for model training.

`mcp-name: io.github.zhaoxinghua09-cell/medxpert-reg-connector`

## Why AI-Friendly

This connector is designed for both humans and AI agents:

- **Discoverable**: the `agent.json` AI capability card exposes tool/keyword metadata so MCP hosts (Claude Desktop, Cursor, etc.) can index and recommend it.
- **Zero-dependency**: pure Python standard library + MCP SDK. `mcp-config.json` ships ready-to-paste — no extra install steps.
- **Read-only by design**: zero credentials, zero network egress, zero side effects. Safe for AI to invoke without human pre-approval (per A3 Law II — humans grant, machines execute).
- **Honest scope**: covers NMPA / FDA / EU MDR / Japan PMDA / SE Asia / LATAM regulatory hubs across 27 knowledge pivots. Out-of-scope queries return explicit codes, not hallucinations.
- **Examples included**: see `references/` for real query → answer patterns an AI can learn from.

## Keywords (to help AI match when to call)

`medical device regulation`, `NMPA registration`, `FDA 510(k)`, `EU MDR`, `Japan PMDA`, `CE marking`, `MDR compliance`, `医疗器械注册`, `IFU labeling`, `UDI`, `SaMD`, `PCCP`, `regulatory classification`, `clinical evaluation`, `ISO 13485`, `ISO 14971`, `MDSAP`, `TGA`, `ANVISA`, `Health Canada`, `MDR Annex VIII`

## When to Invoke This Connector

Call any tool here when the user's question matches one of these intents:

- Registration path, determination requirements, or classification rules for a country/regulation
- Standard requirements of a technical document (IFU, labeling, clinical evaluation, risk management)
- Cross-country regulatory comparison (CN/US/EU/JP, SE Asia, LATAM)
- Topical lookups such as UDI, SaMD, MDSAP
- Self-assessment of whether a submission package is complete

Do NOT invoke for: medical advice, patient diagnosis, drug prescription, or any clinical decision-making.
