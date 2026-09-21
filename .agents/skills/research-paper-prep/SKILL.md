---
name: research-paper-prep
description: "本地论文 Markdown 归档与参考仓库克隆；支持现有 MinerU/PaddleOCR 文本和本地解析命令，不长期保留 PDF 或图片。"
---

# Local paper preparation

Read `references/local-papers.md`. This skill owns source preparation, not literature conclusions. All scripts/dependencies are local to this skill; Python 3.11+ and Git suffice for Markdown import and clone planning. Actual PDF parsing requires a separately provisioned local MinerU or PaddleOCR installation.

## Persistent source contract

`ref/<id>/` contains `paper.md`, `source.json`, optional `repo.txt`, and later `notes.md`. The source manifest records input/output hashes, declared parser, acquisition mode, omitted visuals, and source URL. Parsed text is not scientifically verified text. Keep figures' captions and textual equations where available, but do not pretend missing plots were inspected.

PDFs, images, parser bundles, and full cloned repositories are not versioned. The wrapper creates temporary artifacts under `.runtime/paper-prep/`, publishes only text/metadata, and removes its own staging files on success or failure. It does not delete the user's original input. Do not recursively clean the user's Downloads or old `ref/` trees. Existing tracked binaries require a separately reviewed migration, not just a new ignore rule.

```bash
# Already parsed locally or supplied by the user; no model/API call.
python3 .agents/skills/research-paper-prep/scripts/prepare.py \
  --id paper-slug --source /local/parsed/paper.md --parser mineru \
  --source-url https://arxiv.org/abs/2601.01234 --repo-url https://github.com/owner/repository

# Explicitly run an installed local parser; original PDF is not deleted.
python3 .agents/skills/research-paper-prep/scripts/prepare.py \
  --id another-paper --source /local/paper.pdf --parser paddleocr \
  --source-url https://arxiv.org/abs/2601.01235 --execute

# Default plan only, then explicitly clone into ignored refrepo/paper-slug/.
python3 .agents/skills/research-paper-prep/scripts/clone_ref.py paper-slug
python3 .agents/skills/research-paper-prep/scripts/clone_ref.py paper-slug --execute
```

Use the actual source URL, not these illustrative identifiers. Multiple parser Markdown fragments require explicit `--join-pages` after checking natural-sort order; fragments are not claimed to be verified PDF page numbers. Parser-specific formula/table quality requires inspection. If a formula exists only as an image, record the gap rather than reconstructing it by guesswork.

Provision model weights before an offline run. Some parser installations download weights on first use; a local command alone does not enforce offline operation. No dependency installation or cloud PDF upload is performed by this wrapper. Importing an existing `.md` records the declared parser, not proof that the parser ran here.

Cloning is opt-in, timeout-bounded, shallow, and refuses existing destinations. It verifies the outer Git ignore rule, skips LFS downloads/submodules, and stores the resolved commit locally. It does not pull/reset/clean or execute repository code. Private repository access uses the user's local Git/SSH credentials; ChatGPT connector credentials are not transferred to this script.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
