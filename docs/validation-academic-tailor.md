# Academic tailor validation — 2026-09-26

## Change scope

One new skill, `research-academic-tailor`, with 11 topical references, a provenance guide and source manifest, three Markdown templates, and 14 manual behavioral scenarios. No new model driver, execution dependency, agent role, or source PDF is included. Existing README/AGENTS routing is extended; both existing skill-count assertions change from 10 to 11 without weakening their per-skill language/frontmatter checks.

The input archive contained 44 PDFs (24 handouts, 20 transcripts; 241 pages). The synthesis selects 16 handouts and 12 transcripts and explicitly records missing transcripts for sections 2.5, 2.6 and 3.3. Selection does not imply verbatim auditing of every page. Source identity, page locators, upstream snapshot and adaptation decisions are recorded inside the skill.

## Executed locally

```bash
python3 -m unittest discover -s tests -p test_academic_tailor.py -v
python3 -m compileall -q tests
```

Result: **12 packaging tests passed**; the new test_academic_tailor.py and changed test_v2.py compiled. Checks cover a single valid entry point, direct topic routing, local links, text-only packaging, provenance counts and hashes, explicit missing-source metadata, templates, license notice, repository integration, and the unexecuted status of behavioral scenarios.

Before editing, reconstructed copies of README.md, AGENTS.md and tests/test_v2.py were checked against their Git blob SHA at base commit `00f2f52529ae44d12f31d17f6ce3aa25ea213189`. The test_v2.py change is solely the expected skill count. The local staging directory contains only this change set, not a full checkout.

## Post-push regression check

GitHub Actions run [36242183921](https://github.com/xy3xy3/ResearchWorkspaceTemplate/actions/runs/36242183921) tested the full repository at `bfd4c134312ed663a3294a422894f7f7bfcc1aa4`. Its Python 3.11 log reports 80 tests: 78 passed, one failed, and one optional matplotlib rendering test was skipped because matplotlib was unavailable. All 12 new packaging checks passed.

The sole failure was a second historical skill-count assertion in `tests/test_workflow.py`, still expecting 10 rather than 11. The follow-up corrects that count and renames its test from `test_ten_skills_and_json_schemas` to `test_eleven_skills_and_json_schemas`; no regression checks are removed. The workflow automatically reruns on the follow-up push. Consult that commit's GitHub Actions result for the final matrix status rather than interpreting the first failure or the local packaging count as a final full-suite result.

## Not established by these checks

The existing complete regression suite was not run in the partial local staging directory; the post-push full-suite execution above is a GitHub-hosted CI run.

The 14 scenarios in `assets/evaluation-cases.json` are proposed manual/native-agent evaluations and remain `not_run`. Static assertions that safeguards are documented do not show that a model follows them. No independent model review, native Codex session, live literature lookup, research experiment, end-to-end manuscript generation, LaTeX build, submission or acceptance was tested here. No scientific correctness or publication outcome is certified.
