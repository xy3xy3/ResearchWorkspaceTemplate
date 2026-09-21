---
name: research-literature
description: "检索、去重、阅读与代码证据核对；内置 alphaXiv、Sciverse、arXiv、Crossref、Semantic Scholar 文档和脚本。"
---

# Literature and source evidence

Input: a research question, time window, known papers, and disclosure constraints. Output: one canonical search/synthesis record in `research/literature/`, identifiers in `ref/catalog.json`, parsed source text in `ref/<id>/paper.md`, and human/agent notes in `notes.md`. Do not overwrite parsed paper text with a summary.

## Route by information need

- Known papers and local evidence: inspect existing `ref/` and previous search dates first.
- Bibliographic discovery: existing `scripts/search.py` supports arXiv, Crossref, and Semantic Scholar, identifier deduplication, and explicitly unverified imports.
- Natural-language paper discovery, source passages, or linked code: use already available alphaXiv native tools, or this skill's `scripts/alphaxiv.py`. Read `references/alphaxiv.md` before using the script.
- Structured filters, semantic discovery, relation/evidence retrieval: use `scripts/sciverse.py`; read `references/sciverse.md` for the supported route subset.
- Locally parsed full text and ignored reference clones: hand off to `research-paper-prep`. Do not install external workspace hooks or execute reference-repository setup scripts.

```bash
python3 .agents/skills/research-literature/scripts/search.py --query 'task-driven scene generation' --limit 10
python3 .agents/skills/research-literature/scripts/alphaxiv.py tools
python3 .agents/skills/research-literature/scripts/alphaxiv.py discover \
  --keywords 'scene generation' 'embodied interaction' --question 'Which methods test functional scene usability?'
python3 .agents/skills/research-literature/scripts/sciverse.py semantic \
  --args '{"query":"functional scene generation","mode":"balanced","page_size":10}'
```

## Evidence workflow

Define inclusion/exclusion criteria and several meaningfully different queries. Record provider, query, date, coverage, returned identifiers, failure/partial status, and the raw-result location. Follow citations and closest competing methods rather than collecting an arbitrary paper count. Incremental monitoring is another dated search, not an implicit background service.

Distinguish provider-generated summaries, metadata, extracted source text, and verified findings. An API response is not a scientific verification. Read the relevant original passage before attaching a claim; record section/page/equation or Markdown line locator. Preserve version differences and contradictory reports. For code, record repository URL, actual commit, file/symbol, and whether it was inspected or executed.

Deduplicate strong identifiers first. Similar titles alone do not establish identity. AlphaXiv/Sciverse scripts intentionally return raw provider JSON, not invented normalized records. Retain that raw provenance; normalize only fields actually returned before using `search.py --import-file` with a JSON array of objects containing `title` and known `doi`/`arxiv_id`/`url`. Imports remain unverified. Never feed arbitrary provider JSON directly into the catalog.

“No match found” does not prove novelty. State the closest work, observed differences, and remaining uncertainty. Network failure is not an empty successful search: record the failure, then use a genuinely available alternative or existing material.

Secrets: process environment > current skill `.env` > project `.env`. Dedicated clients use `ALPHAXIV_API_TOKEN` (or `ALPHAXIV_API_KEY`) and `SCIVERSE_API_TOKEN`; no real keys in commands, chat, or Git. Authenticated redirects and arbitrary service origins are refused. Only send public/approved query content; external search services receive the submitted text.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
