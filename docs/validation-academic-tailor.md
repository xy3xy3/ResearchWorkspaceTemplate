# Academic tailor validation — 2026-09-26

## Change scope

One new skill, `research-academic-tailor`, with 11 topical references, a provenance guide and source manifest, three Markdown templates, and 14 manual behavioral scenarios. No new model driver, execution dependency, agent role, or source PDF is included. Existing README/AGENTS routing is extended; the existing skill-count assertion changes from 10 to 11 without weakening its per-skill language checks.

The input archive contained 44 PDFs (24 handouts, 20 transcripts; 241 pages). The synthesis selects 16 handouts and 12 transcripts and explicitly records missing transcripts for sections 2.5, 2.6 and 3.3. Selection does not imply verbatim auditing of every page. Source identity, page locators, upstream snapshot and adaptation decisions are recorded inside the skill.

## Executed locally

```bash
python3 -m unittest discover -s tests -p test_academic_tailor.py -v
python3 -m compileall -q tests
```

Result: **12 packaging tests passed**; both changed/new Python test files compiled. Checks cover a single valid entry point, direct topic routing, local links, text-only packaging, provenance counts and hashes, explicit missing-source metadata, templates, license notice, repository integration, and the unexecuted status of behavioral scenarios.

Before editing, reconstructed copies of README.md, AGENTS.md and tests/test_v2.py were checked against their Git blob SHA at base commit `00f2f52529ae44d12f31d17f6ce3aa25ea213189`. The test_v2.py change is solely the expected skill count. The local staging directory contains only this change set, not a full checkout.

## Not established by these checks

The existing complete regression suite was not run in this partial local staging directory; the repository's normal CI runs the complete suite after publication. Consult that commit's GitHub Actions result rather than treating the local test count as a full regression run.

The 14 scenarios in `assets/evaluation-cases.json` are proposed manual/native-agent evaluations and remain `not_run`. Static assertions that safeguards are documented do not show that a model follows them. No independent model review, native Codex session, live literature lookup, research experiment, end-to-end manuscript generation, LaTeX build, submission or acceptance was tested here. No scientific correctness or publication outcome is certified.
