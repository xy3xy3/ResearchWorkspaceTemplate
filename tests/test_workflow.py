"""Offline contract and local-process tests. No live Codex, APIs, or GPUs."""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'
sys.path.insert(0, str(SKILLS / 'research-workspace/scripts'))
import runtime

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, SKILLS / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

ws = load('workspace_cli', 'research-workspace/scripts/workspace.py')
runner = load('experiment_runner', 'research-experiment/scripts/run.py')
analysis = load('experiment_analysis', 'research-experiment/scripts/analyze.py')
review = load('research_audit', 'research-review/scripts/audit.py')
literature = load('literature_search', 'research-literature/scripts/search.py')
loop = load('autopilot_loop', 'research-autopilot/scripts/loop.py')

class TemplateTests(unittest.TestCase):
    def test_runtime_vendors_identical(self):
        copies = list(SKILLS.glob('*/scripts/runtime.py'))
        self.assertEqual(len(copies), 5)
        self.assertEqual(len({p.read_bytes() for p in copies}), 1)

    def test_native_configuration(self):
        cfg = tomllib.loads((ROOT / '.codex/config.toml').read_text())
        self.assertEqual(cfg['agents']['max_concurrent_threads_per_session'], 3)
        agents = list((ROOT / '.codex/agents').glob('*.toml'))
        self.assertEqual(len(agents), 4)
        for p in agents:
            item = tomllib.loads(p.read_text())
            for key in ['name', 'description', 'developer_instructions']:
                self.assertTrue(item[key])

    def test_seven_skills_and_json_schemas(self):
        files = list(SKILLS.glob('*/SKILL.md'))
        self.assertEqual(len(files), 7)
        for p in files:
            text = p.read_text()
            self.assertTrue(text.startswith('---\n'))
            self.assertIn('name: ' + p.parent.name, text)
            self.assertIn('description:', text)
        for p in (SKILLS / 'research-autopilot/references').glob('*.json'):
            schema = json.loads(p.read_text())
            self.assertEqual(schema['type'], 'object')
            self.assertFalse(schema['additionalProperties'])

    def test_gitignore_boundaries(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            subprocess.run(['git', 'init', '-q', str(d)], check=True)
            shutil.copy(ROOT / '.gitignore', d / '.gitignore')
            for path in ['repos/code/a.py', 'paper/main.tex', 'refrepo/a/file', '.runtime/log', '.agents/skills/x/.env', 'workspace.local.json']:
                self.assertEqual(subprocess.run(['git', '-C', str(d), 'check-ignore', '-q', path]).returncode, 0, path)
            for path in ['task/active/T-1/meta.json', 'research/findings/f.md', 'spec/rules.md', '.env.example', '.agents/skills/x/.env.example', 'repos/.gitkeep']:
                self.assertEqual(subprocess.run(['git', '-C', str(d), 'check-ignore', '-q', path]).returncode, 1, path)

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        ws.initialize(self.root, argparse.Namespace(code_repo=None, paper_repo=None, direction='A synthetic local research test, not a scientific result.'))
        self.cfg = runtime.read_json(self.root / 'workspace.local.json')
        self.repo = self.root / 'repos/demo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        shutil.copy(SKILLS / 'research-experiment/assets/toy_experiment.py', self.repo / 'toy.py')
        (self.repo / '.gitignore').write_text('__pycache__/\n')
        self.commit()
        self.cfg['code_repo'] = 'repos/demo'
        runtime.write_json(self.root / 'workspace.local.json', self.cfg)

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self):
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.email=tests@example.invalid', '-c', 'user.name=Offline Tests', 'commit', '-qm', 'test fixture'], check=True)
        self.head = runtime.git(self.repo, 'rev-parse', 'HEAD')

    def plan(self, purpose='pilot', method='linear', seeds=None):
        return {'question_id': 'Q-test', 'hypothesis': 'Test execution only', 'baseline': 'mean',
                'comparison_group': 'synthetic-v1', 'code_commit': self.head, 'purpose': purpose,
                'seeds': [0, 1, 2] if seeds is None else seeds,
                'argv': [sys.executable, 'toy.py', '--method', method, '--seed', '{seed}'],
                'timeout_seconds': 5, 'metric': {'name': 'mse', 'direction': 'lower', 'unit': 'squared-error'},
                'dataset': {'name': 'synthetic', 'version': 'v1', 'split': '60/40'}, 'env_keys': []}

    def cli(self, *args, success=True):
        result = subprocess.run([sys.executable, str(SKILLS / 'research-workspace/scripts/workspace.py'), '--root', str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        return json.loads(result.stdout) if success else result

    def test_env_precedence_literals_empty_and_secret_filter(self):
        skill = self.root / 'skill'
        skill.mkdir()
        (self.root / '.env').write_text('TEST_API_KEY=project-key\nLITERAL="${UNCHANGED}"\n')
        (skill / '.env').write_text("TEST_API_KEY='skill-key' # literal\n")
        with mock.patch.dict(os.environ, {'TEST_API_KEY': 'process-key', 'OTHER_SECRET': 'do-not-pass'}, clear=True):
            env, secrets = runtime.environment(self.root, skill, ['TEST_API_KEY', 'LITERAL'])
            self.assertEqual(env['TEST_API_KEY'], 'process-key')
            self.assertEqual(env['LITERAL'], '${UNCHANGED}')
            self.assertNotIn('OTHER_SECRET', env)
            self.assertIn('process-key', secrets)
            os.environ['TEST_API_KEY'] = ''
            self.assertEqual(runtime.environment(self.root, skill, ['TEST_API_KEY'])[0]['TEST_API_KEY'], '')
            del os.environ['TEST_API_KEY']
            self.assertEqual(runtime.environment(self.root, skill, ['TEST_API_KEY'])[0]['TEST_API_KEY'], 'skill-key')
            (skill / '.env').unlink()
            self.assertEqual(runtime.environment(self.root, skill, ['TEST_API_KEY'])[0]['TEST_API_KEY'], 'project-key')
        with self.assertRaises(ValueError):
            runtime.environment(self.root, skill, ['PATH'])

    def test_dotenv_does_not_execute_shell(self):
        file = self.root / '.env'
        file.write_text('X=$(touch SHOULD_NOT_EXIST)\n')
        self.assertEqual(runtime.dotenv(file)['X'], '$(touch SHOULD_NOT_EXIST)')
        self.assertFalse((self.root / 'SHOULD_NOT_EXIST').exists())
        file.write_text('invalid line\n')
        with self.assertRaises(ValueError): runtime.dotenv(file)

    def test_path_and_evidence_boundaries(self):
        for path in ['../outside', '/etc/passwd', '.env']:
            with self.assertRaises(ValueError): runtime.evidence(self.root, path)
        (self.root / 'research/escape').symlink_to(self.root.parent)
        with self.assertRaises(ValueError): runtime.inside(self.root, 'research/escape/out')
        (self.root / 'research/empty.md').touch()
        with self.assertRaises(ValueError): runtime.evidence(self.root, 'research/empty.md')

    def test_independent_repository_required(self):
        self.assertEqual(runtime.code_repo(self.root, self.cfg), self.repo)
        with self.assertRaises(ValueError): runtime.code_repo(self.root, {'code_repo': '.'})
        with self.assertRaises(ValueError): runtime.code_repo(self.root, {'code_repo': 'research'})
        with self.assertRaises(ValueError): runtime.code_repo(self.root, {'code_repo': 'repos/demo/nested'})

    def test_task_create_event_archive_and_immutable(self):
        task = self.cli('task-new', '--title', '执行测试', '--question', 'Q-1')
        ident = task['id']
        self.cli('task-event', ident, '--kind', 'decision', '--text', 'Use synthetic fixture', '--state', 'running')
        self.cli('task-close', ident, '--outcome', 'completed', '--summary', 'missing proof', success=False)
        proof = self.root / 'research/findings/proof.md'
        proof.write_text('Actual test evidence, not a research finding.')
        done = self.cli('task-close', ident, '--outcome', 'completed', '--summary', 'checked', '--evidence', 'research/findings/proof.md')
        self.assertEqual(done['status'], 'completed')
        self.assertTrue((self.root / 'task/archive' / ident / 'meta.json').exists())
        self.assertFalse((self.root / 'task/active' / ident).exists())
        self.cli('task-event', ident, '--kind', 'progress', '--text', 'overwrite history', success=False)

    def test_finding_requires_evidence_and_brief_not_overwritten(self):
        self.cli('note', '--kind', 'finding', '--title', 'unsupported', '--body', 'guess', success=False)
        idea = self.cli('note', '--kind', 'idea', '--title', 'hypothesis', '--body', 'untested')
        self.assertTrue((self.root / idea['path']).exists())
        before = (self.root / 'research/brief.md').read_text()
        self.cli('init', '--direction', 'overwrite', success=False)
        self.assertEqual((self.root / 'research/brief.md').read_text(), before)

    def test_real_local_seed_runs_and_paired_analysis(self):
        base, _ = runner.execute(self.root, self.cfg, self.plan(method='mean'))
        cand, _ = runner.execute(self.root, self.cfg, self.plan())
        self.assertEqual(base['status'], 'succeeded')
        self.assertEqual(cand['status'], 'succeeded')
        self.assertEqual(len(cand['trials']), 3)
        self.assertEqual(cand['source']['commit'], self.head)
        self.assertEqual(cand['source']['fingerprint'], cand['source_after']['fingerprint'])
        result = analysis.compare(base, cand)
        self.assertLess(result['candidate_minus_baseline'], 0)
        self.assertEqual(result['n'], 3)
        self.assertIsNotNone(result['paired_bootstrap_95_percent_interval'])
        self.assertEqual(review.audit(self.root)['status'], 'PASS')
        self.assertEqual(runtime.git(self.repo, 'status', '--porcelain'), '')

    def test_dirty_default_rejected_confirmatory_always_rejected(self):
        (self.repo / 'extra.txt').write_text('uncommitted')
        with self.assertRaises(ValueError): runner.execute(self.root, self.cfg, self.plan())
        with self.assertRaises(ValueError): runner.execute(self.root, self.cfg, self.plan(purpose='confirmatory'), allow_dirty=True)
        result, _ = runner.execute(self.root, self.cfg, self.plan(purpose='smoke', seeds=[0]), allow_dirty=True)
        self.assertEqual(result['status'], 'succeeded')
        self.assertTrue(result['source']['dirty'])

    def test_wrong_commit_and_over_budget_rejected(self):
        plan = self.plan()
        plan['code_commit'] = 'not-the-commit'
        with self.assertRaises(ValueError): runner.execute(self.root, self.cfg, plan)
        plan = self.plan()
        plan['timeout_seconds'] = 601
        with self.assertRaises(ValueError): runner.execute(self.root, self.cfg, plan)

    def test_nonzero_exit_and_invalid_metric_receipts(self):
        for snippet, status in [('raise SystemExit(4)', 'failed'), ('pass', 'invalid_metrics'),
            ("import os,json;from pathlib import Path;Path(os.environ['RW_RUN_DIR'],'metrics.json').write_text(json.dumps({'mse':float('nan')}))", 'invalid_metrics')]:
            plan = self.plan(seeds=[0])
            plan['argv'] = [sys.executable, '-c', snippet]
            record, path = runner.execute(self.root, self.cfg, plan)
            self.assertEqual(record['status'], 'failed')
            self.assertEqual(record['trials'][0]['status'], status)
            self.assertTrue(path.exists())

    def test_stop_and_timeout_reap_process(self):
        env, _ = runtime.environment(self.root, self.root)
        result = runtime.run_logged([sys.executable, '-c', 'import time;time.sleep(30)'], self.root, env, .15, self.root / '.runtime/timeout.log')
        self.assertEqual(result['status'], 'timeout')
        self.assertLess(result['seconds'], 5)
        (self.root / '.runtime/STOP').touch()
        result = runtime.run_logged([sys.executable, '-c', 'raise Exception()'], self.root, env, 1, self.root / '.runtime/stopped.log', stop=self.root / '.runtime/STOP')
        self.assertEqual(result['status'], 'stopped')

    def test_source_drift_taints_results(self):
        plan = self.plan(seeds=[0])
        plan['argv'] = [sys.executable, '-c', "import os,json;from pathlib import Path;Path('modified.txt').write_text('x');Path(os.environ['RW_RUN_DIR'],'metrics.json').write_text(json.dumps({'mse':1}))"]
        result, _ = runner.execute(self.root, self.cfg, plan)
        self.assertEqual(result['status'], 'tainted_source_changed')

    def test_comparison_rejects_smoke_missing_seeds_failed_and_nonfinite(self):
        base, _ = runner.execute(self.root, self.cfg, self.plan(seeds=[0, 1]))
        self.assertIsNone(analysis.compare(base, base)['paired_bootstrap_95_percent_interval'])
        for change in ['smoke', 'missing', 'failed', 'nan', 'protocol']:
            bad = copy.deepcopy(base)
            if change == 'smoke': bad['plan']['purpose'] = 'smoke'
            if change == 'missing': bad['trials'].pop()
            if change == 'failed': bad['trials'][0]['returncode'] = 2
            if change == 'nan': bad['trials'][0]['metrics']['mse'] = float('nan')
            if change == 'protocol': bad['plan']['dataset']['version'] = 'changed'
            with self.assertRaises(ValueError): analysis.compare(base, bad)

    def test_audit_detects_tampering_and_missing_raw(self):
        self.assertEqual(review.audit(self.root)['status'], 'NOT_APPLICABLE')
        result, _ = runner.execute(self.root, self.cfg, self.plan(seeds=[0]))
        raw = self.root / '.runtime/experiments' / result['id'] / 'seed-0/metrics.json'
        raw.write_text('{"mse":999}')
        self.assertEqual(review.audit(self.root)['status'], 'FAIL')
        raw.unlink()
        self.assertEqual(review.audit(self.root)['status'], 'WARN')

    def test_claims_need_support_and_reject_smoke(self):
        run, path = runner.execute(self.root, self.cfg, self.plan(purpose='smoke', seeds=[0]))
        ref = runtime.evidence(self.root, path.relative_to(self.root))
        ref['locator'] = 'trials[0].metrics.mse'
        runtime.write_json(self.root / 'research/claims.json', [{'status': 'supported', 'evidence': [ref]}])
        self.assertEqual(review.audit(self.root)['status'], 'FAIL')

    def fake_codex(self, mode='complete'):
        binary = self.root / 'fake-codex'
        binary.write_text('#!' + sys.executable + '\n' + r'''
import json, sys
from pathlib import Path
args = sys.argv[1:]
root = Path(args[args.index('-C')+1])
final = Path(args[args.index('-o')+1])
phase = 'review' if args[args.index('--sandbox')+1] == 'read-only' else 'execute'
mode = (root / '.runtime/mock-mode').read_text()
if mode == 'error':
    raise SystemExit(3)
if phase == 'review':
    value = {'status': 'revise' if mode == 'revise' else 'proceed', 'summary': 'Offline mock review only.', 'next_action': 'Inspect the synthetic fixture.'}
else:
    artifact = root / 'research/findings/mock.md'
    artifact.write_text('A synthetic fixture. This is not genuine scientific evidence.')
    value = {'status': 'complete' if mode == 'complete' else 'continue', 'summary': 'Offline mock execution only.', 'next_action': 'Review original fixture.', 'progress': True, 'artifacts': [] if mode == 'empty' else ['research/findings/mock.md']}
final.write_text(json.dumps(value))
print(json.dumps({'mock': True, 'phase': phase}))
''')
        binary.chmod(0o700)
        (self.root / '.runtime/mock-mode').write_text(mode)
        return str(binary)

    def loop_args(self, mode='complete', **kwargs):
        args = dict(execute=True, resume=None, max_rounds=None, codex_bin=self.fake_codex(mode), model=None)
        args.update(kwargs)
        return argparse.Namespace(**args)

    def test_autopilot_mock_complete_and_resume_no_new_round(self):
        args = self.loop_args()
        state = loop.drive(self.root, self.cfg, args)
        self.assertEqual(state['status'], 'completed')
        self.assertEqual(len(state['attempts']), 1)
        self.assertEqual(state['attempts'][0]['review']['status'], 'proceed')
        args.resume = state['id']
        self.assertEqual(len(loop.drive(self.root, self.cfg, args)['attempts']), 1)

    def test_autopilot_empty_evidence_and_process_error_not_success(self):
        for mode in ['empty', 'error']:
            state = loop.drive(self.root, self.cfg, self.loop_args(mode))
            self.assertEqual(state['status'], 'error')
            self.assertEqual(state['attempts'][0]['status'], 'error')

    def test_autopilot_budget_stall_stop_and_contract_resume(self):
        args = self.loop_args('continue', max_rounds=1)
        state = loop.drive(self.root, self.cfg, args)
        self.assertEqual(state['status'], 'budget-exhausted')
        args.resume = state['id']
        self.assertEqual(loop.drive(self.root, self.cfg, args)['spent_seconds'], state['spent_seconds'])
        (self.root / 'spec/changed.md').write_text('new restriction')
        with self.assertRaises(ValueError): loop.drive(self.root, self.cfg, args)
        state = loop.drive(self.root, self.cfg, self.loop_args('revise'))
        self.assertEqual(state['status'], 'stalled')
        (self.root / '.runtime/STOP').touch()
        state = loop.drive(self.root, self.cfg, self.loop_args())
        self.assertEqual(state['status'], 'stopped')
        self.assertEqual(state['attempts'], [])

    def test_autopilot_dry_run_no_execution_and_no_budget_escalation(self):
        args = self.loop_args(execute=False)
        self.assertEqual(loop.drive(self.root, self.cfg, args)['status'], 'dry-run')
        self.assertFalse(list((self.root / 'research/cycles').glob('*/state.json')))
        args.max_rounds = 100
        with self.assertRaises(ValueError): loop.drive(self.root, self.cfg, args)

    def test_runtime_log_redaction_and_cap(self):
        result = runtime.run_logged([sys.executable, '-c', "print('super-secret-key')"], self.root, dict(os.environ), 2, self.root / '.runtime/redacted.log', ['super-secret-key'])
        self.assertEqual(result['status'], 'succeeded')
        self.assertNotIn('super-secret-key', (self.root / '.runtime/redacted.log').read_text())
        result = runtime.run_logged([sys.executable, '-c', "print('x'*10000)"], self.root, dict(os.environ), 2, self.root / '.runtime/cap.log', max_bytes=100)
        self.assertEqual(result['status'], 'log_limit')
        self.assertLess((self.root / '.runtime/cap.log').stat().st_size, 200)


class LiteratureTests(unittest.TestCase):
    def test_identifier_dedup_without_title_only_false_merge(self):
        data = literature.deduplicate([
            {'title': 'A', 'doi': 'https://doi.org/10.1234/ABC', 'sources': ['crossref']},
            {'title': 'A revised title', 'doi': '10.1234/abc', 'arxiv_id': '2601.01234v2', 'sources': ['s2']},
            {'title': 'A revised title', 'arxiv_id': '2601.01234v1', 'sources': ['arxiv']},
            {'title': 'A', 'doi': '10.1234/another', 'sources': ['crossref']}])
        self.assertEqual(len(data), 2)
        joined = next(x for x in data if x['id'] == 'doi:10.1234/abc')
        self.assertEqual(joined['sources'], ['arxiv', 'crossref', 's2'])
        self.assertIn('arxiv:2601.01234', joined['identifiers'])

    def test_provider_parsers_mocked_not_live(self):
        atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/2601.01234v2</id><title>Test paper</title><published>2026-01-01</published><author><name>A</name></author></entry></feed>'
        crossref = json.dumps({'message': {'items': [{'title': ['Test'], 'DOI': '10.1/test', 'issued': {'date-parts': [[2026]]}, 'author': [{'given': 'A', 'family': 'B'}]}]}}).encode()
        semantic = json.dumps({'data': [{'title': 'Test', 'paperId': 'xyz', 'externalIds': {'DOI': '10.1/test'}, 'authors': [{'name': 'A B'}]}]}).encode()
        for provider, body in [('arxiv', atom), ('crossref', crossref), ('semanticscholar', semantic)]:
            with mock.patch.object(literature, 'get', return_value=body):
                result = literature.retrieve(provider, 'test', 1, {})
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['verification'], 'metadata-only')

    def test_partial_and_failed_searches_are_recorded(self):
        import io
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ws.initialize(root, argparse.Namespace(code_repo=None, paper_repo=None, direction='offline literature tests'))
            argv = ['search.py', '--root', d, '--query', 'test']
            for partial in [True, False]:
                def retrieve(provider, *unused):
                    if partial and provider == 'arxiv':
                        return [{'title': 'Offline test', 'arxiv_id': '0000.00000', 'sources': ['arxiv'], 'verification': 'metadata-only'}]
                    raise RuntimeError('simulated provider failure')
                output = io.StringIO()
                with mock.patch.object(sys, 'argv', argv), mock.patch.object(literature, 'retrieve', side_effect=retrieve), mock.patch.object(sys, 'stdout', output):
                    code = literature.main()
                self.assertEqual(code, 0 if partial else 2)
                message = json.loads(output.getvalue())
                self.assertEqual(message['status'], 'partial' if partial else 'failed')
                report = runtime.read_json(root / 'research/literature' / (message['id'] + '.json'))
                self.assertTrue(report['errors'])

    def test_import_remains_unverified(self):
        import io
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ws.initialize(root, argparse.Namespace(code_repo=None, paper_repo=None, direction='offline import tests'))
            source = root / 'metadata.json'
            source.write_text(json.dumps([{'title': 'Test import', 'doi': '10.1/import'}]))
            with mock.patch.object(sys, 'argv', ['search.py', '--root', d, '--import-file', str(source)]), mock.patch.object(sys, 'stdout', io.StringIO()):
                self.assertEqual(literature.main(), 0)
            self.assertEqual(runtime.read_json(root / 'ref/catalog.json')[0]['verification'], 'unverified-import')

if __name__ == '__main__':
    unittest.main()
