"""Offline packaging checks only; these do not execute or grade an LLM."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/research-academic-tailor'
TOPICS = {
    'reading-and-decomposition', 'baseline-and-modules',
    'experiments-and-evidence', 'argument-and-contributions',
    'paper-writing', 'thesis-writing', 'figures-and-style',
    'language-and-citations', 'submission', 'revision', 'cross-disciplinary',
}


def text(relative: str) -> str:
    return (SKILL / relative).read_text(encoding='utf-8')


def local_links(markdown: str) -> list[str]:
    """Only inspect inline Markdown links used by this documentation package."""
    links = re.findall(r'\[[^\]\n]*\]\(([^)\s]+)\)', markdown)
    return [unquote(urlsplit(link).path) for link in links
            if not urlsplit(link).scheme and urlsplit(link).path]


class AcademicTailorTests(unittest.TestCase):
    def test_single_entry_and_frontmatter(self):
        self.assertEqual(list(SKILL.rglob('SKILL.md')), [SKILL / 'SKILL.md'])
        body = text('SKILL.md')
        header = body.split('---', 2)[1]
        name = re.search(r'^name: (.+)$', header, re.M).group(1)
        self.assertEqual(name, SKILL.name)
        self.assertRegex(name, r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
        self.assertLessEqual(len(name), 64)
        desc = re.search(r'^description: "(.+)"$', header, re.M).group(1)
        self.assertTrue(desc)
        self.assertLessEqual(len(desc), 1024)
        self.assertLess(len(body.splitlines()), 500)

    def test_all_local_markdown_links_resolve_inside_package(self):
        for path in SKILL.rglob('*.md'):
            for link in local_links(path.read_text(encoding='utf-8')):
                target = (path.parent / link).resolve()
                self.assertTrue(target.is_relative_to(SKILL.resolve()), (path, link))
                self.assertTrue(target.is_file(), (path, link))

    def test_link_parser_handles_external_and_fragment_links(self):
        self.assertEqual(local_links('[a](refs/a.md#part) [b](https://example.org/x) [c](#part)'), ['refs/a.md'])

    def test_topics_are_directly_routed(self):
        body = text('SKILL.md')
        for topic in TOPICS:
            relative = f'references/{topic}.md'
            self.assertIn(f'({relative})', body)
            self.assertGreater(len(text(relative)), 400)
        self.assertEqual(len(TOPICS), 11)

    def test_manifest_counts_and_paths(self):
        data = json.loads(text('references/source-manifest.json'))
        files = data['files']
        self.assertEqual(len(files), data['total_files'])
        self.assertEqual(len(files), 44)
        self.assertEqual(sum(f['pages'] for f in files), 241)
        self.assertEqual(data['total_pages'], 241)
        self.assertEqual(sum(f['path'].startswith('课件/') for f in files), 24)
        self.assertEqual(sum(f['path'].startswith('音频转文本/') for f in files), 20)
        self.assertEqual(len({f['path'] for f in files}), 44)
        for item in files:
            self.assertRegex(item['sha256'], r'^[0-9a-f]{64}$')
            self.assertGreater(item['pages'], 0)
            self.assertFalse(Path(item['path']).is_absolute())
            self.assertNotIn('..', Path(item['path']).parts)
        self.assertRegex(data['archive_sha256'], r'^[0-9a-f]{64}$')

    def test_selection_and_missing_transcripts_are_explicit(self):
        data = json.loads(text('references/source-manifest.json'))
        selected = [f for f in data['files'] if f['in_scope']]
        self.assertEqual(len(selected), 28)
        self.assertEqual(sum(f['path'].startswith('课件/') for f in selected), 16)
        self.assertEqual(data['missing_transcript_sections'], ['2.5', '2.6', '3.3'])
        self.assertEqual(data['upstream_commit'], 'd2417333a6f4d577b2cb8c68206d0443252fc936')
        self.assertIn('not a claim of verbatim reading', data['note'])

    def test_package_contains_text_only_and_no_runtime(self):
        for path in SKILL.rglob('*'):
            if path.is_file():
                self.assertIn(path.suffix, {'.md', '.json'}, path)
                path.read_text(encoding='utf-8')
        self.assertFalse((SKILL / 'scripts').exists())

    def test_templates_keep_missing_evidence_visible(self):
        workbench = text('assets/paper-workbench.md')
        for term in ['claim_id', 'evidence_id', 'DATA_NEEDED', 'supported', 'contradicted', 'missing']:
            self.assertIn(term, workbench)
        self.assertIn('CITATION_NEEDED', text('assets/manuscript-outline.md'))
        self.assertIn('pending', text('assets/revision-response.md'))
        self.assertIn('paper_repo', workbench)

    def test_scope_and_communication_contract_are_documented(self):
        body = text('SKILL.md')
        for term in ['## Communication', 'Chinese gloss', 'uncertainty',
                     '不加入选导师', '不伪造结果', '不投稿', '独立 `paper_repo`',
                     '没有原生子智能体就顺序完成', '不重造工具链']:
            self.assertIn(term, body)

    def test_third_party_notice_is_present(self):
        notice = text('THIRD_PARTY_NOTICES.md')
        for term in ['MIT License', 'Copyright (c) 2026',
                     'Permission is hereby granted', 'THE SOFTWARE IS PROVIDED "AS IS"']:
            self.assertIn(term, notice)
        self.assertIn('LZX0719-Hub/shuidao-skill', notice)

    def test_behavioral_cases_are_unexecuted_manual_scenarios(self):
        data = json.loads(text('assets/evaluation-cases.json'))
        self.assertEqual(data['execution_status'], 'not_run')
        self.assertEqual(len(data['cases']), 14)
        self.assertEqual(len({case['id'] for case in data['cases']}), 14)
        for case in data['cases']:
            for key in ['input', 'expected', 'forbidden']:
                self.assertTrue(case[key], (case['id'], key))

    def test_repository_integration(self):
        for name in ['README.md', 'AGENTS.md']:
            self.assertIn(SKILL.name, (ROOT / name).read_text(encoding='utf-8'))
        self.assertIn('11 个技能', (ROOT / 'README.md').read_text(encoding='utf-8'))
        previous_tests = (ROOT / 'tests/test_v2.py').read_text(encoding='utf-8')
        ast.parse(previous_tests)
        self.assertIn('self.assertEqual(len(files),11)', previous_tests)


if __name__ == '__main__':
    unittest.main()
