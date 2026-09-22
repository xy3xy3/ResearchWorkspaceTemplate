# Sciverse（科研检索与证据服务）

Migrated contract: the user's `ResearchTemplate/scripts/paper_retrieval/sciverse.py`. Official service: `https://sciverse.space/`; API origin defaults to `https://api.sciverse.space`. Set `SCIVERSE_API_TOKEN` in the process, skill `.env`, or project `.env`, in that order. Optional `SCIVERSE_BASE_URL` is restricted to official HTTPS sciverse.space hosts without paths, embedded credentials, queries, or nonstandard ports.

| Local command | HTTP route | Use |
|---|---|---|
| catalog | GET /meta-catalog | Discover fields/collections |
| search | POST /meta-search | Structured bibliographic filters |
| semantic | POST /agentic-search | Natural-language discovery |
| relations | POST /meta-paper-relations | Relations of supplied papers |
| content | GET /content | Content for a returned doc_id |
| schema-capabilities | GET /paper-schema | Discover schema capabilities |
| schema-search | POST /paper-schema/search | Search structured paper records |
| evidence-search | POST /paper-schema/evidence/search | Find structured evidence |
| evidence-get | GET /paper-schema/schemas/{schema_id}/evidence/{evidence_id} | Fetch identified evidence |
| provenance | POST /paper-schema/resolve-provenance | Resolve source provenance |

```bash
python3 .agents/skills/research-literature/scripts/sciverse.py catalog --args '{}'
python3 .agents/skills/research-literature/scripts/sciverse.py search \
  --args '{"query":"scene generation","year_from":2025,"page_size":10}'
python3 .agents/skills/research-literature/scripts/sciverse.py semantic \
  --args '{"query":"task-driven scene synthesis with functional evaluation","mode":"balanced"}'
python3 .agents/skills/research-literature/scripts/sciverse.py content --args '{"doc_id":"ACTUAL_RETURNED_ID"}'
python3 .agents/skills/research-literature/scripts/sciverse.py evidence-get \
  --args '{"schema_id":"ACTUAL_SCHEMA_ID","evidence_id":"ACTUAL_EVIDENCE_ID"}'
```

Do not guess service IDs. Inspect catalog/capabilities and actual responses before supplying advanced filters. Semantic mode presets follow the old script: fast=es, balanced=hybrid, quality=hybrid with three subqueries. This is a request preset, not a measured speed/quality guarantee. Dates, licensing, access level, and coverage must be recorded from actual results.

This bundled client intentionally covers the listed read-only routes, not every account/schema operation from the old utility. It returns raw JSON; the literature owner records provenance, performs normalization only from returned fields, and distinguishes provider metadata from original evidence. Endpoint/schema changes, authorization failures, rate limits and missing content remain explicit failures. No automatic paid fallback or infinite retry. Private queries still leave the local machine; obtain appropriate permission before transmitting them.
