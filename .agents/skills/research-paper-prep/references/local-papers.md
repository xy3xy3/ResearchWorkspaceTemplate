# Local paper lifecycle

1. Obtain a lawful paper copy or existing parsed Markdown. Downloading access-restricted papers or uploading private PDFs is not authorized by this skill.
2. Import existing MinerU/PaddleOCR Markdown when available. This avoids redundant OCR. Preserve the original file untouched.
3. For PDF-only input, provision the chosen parser and weights in the user's local environment, then explicitly run the wrapper. A local CLI may download model weights on first launch; offline/network restrictions require actual host configuration. The wrapper does not install models, call a cloud parser API, or claim to enforce a network sandbox.
4. Inspect parsed formulas/tables and source ordering. Multiple Markdown fragments need `--join-pages`; the helper uses natural filename sorting and marks fragment boundaries. This is not a PDF page-order proof.
5. Publish only paper.md, source.json and optional repo.txt. Visual links/embedded image material are replaced with omission markers. Text captions/equations remain when available. Missing visuals must be reported whenever a claim depends on them. Do not treat omitted images as having been read.
6. Keep annotations in notes.md. Reference clones are rebuilt from repo.txt into ignored refrepo/<id>. Inspect license/README/code before executing anything. Record the actual checkout commit for code-based claims.

Supported local command adapters:

```text
mineru -p <temporary-input.pdf> -o <temporary-output> -b pipeline
paddleocr pp_structurev3 -i <temporary-input.pdf> --save_path <temporary-output>
```

`--parser-exe` selects an installed executable path, not an arbitrary shell command string. The wrapper uses argv arrays, positive timeouts, temporary work directories, input-size/type checks, and refuses existing ref IDs. A 200 MiB input limit is this wrapper's bound, not a statement about all parser products. CPU/GPU behavior depends on the chosen local parser build; this template does not promise GPU detection.

The input/source hashes and parser declaration are preserved. Parser version is currently marked not-probed; retain an environment lock/version record separately for strict reproducibility. For imported Markdown, the recorded parser is user-declared, not locally verified. PDF/image staging created by the helper is cleaned on failure as well as success; the original PDF is never deleted.

Clone safety: ignored independent destination, no overwrite/pull/reset, finite timeout, skipped LFS/submodules, no execution of downloaded code. It does not replace an OS sandbox or neutralize arbitrary user Git filters. Private SSH access relies on the local account's normal Git/SSH configuration, not a key copied from ChatGPT.

Primary parser documentation consulted:
- https://opendatalab.github.io/MinerU/usage/quick_usage/
- https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PP-StructureV3.html

These adapters require a matching installed CLI. A mocked argv test does not establish that a particular local parser version works end to end.
