"""Offline v2 tests. Real local files/processes; remote services and parsers are mocked."""
from __future__ import annotations
import contextlib
import importlib.util
import io
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
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / '.agents/skills'

def load(name, relative):
    path = SKILLS / relative
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

svc = load('service_client', 'research-literature/scripts/service_client.py')
alpha = load('v2_alpha', 'research-literature/scripts/alphaxiv.py')
sci = load('v2_sci', 'research-literature/scripts/sciverse.py')
pio = load('paper_io', 'research-paper-prep/scripts/paper_io.py')
prep = load('v2_prep', 'research-paper-prep/scripts/prepare.py')
clone = load('v2_clone', 'research-paper-prep/scripts/clone_ref.py')
cp = load('v2_checkpoint', 'research-autopilot/scripts/checkpoint.py')
pr = load('paper_repo', 'research-latex/scripts/paper_repo.py')
latex = load('v2_latex', 'research-latex/scripts/latex.py')
plot = load('v2_plot', 'research-figures/scripts/plot.py')


def gitinit(path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'init', '-q', str(path)], check=True)


class TemporaryCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
    def tearDown(self):
        self.tmp.cleanup()


class ServiceTests(TemporaryCase):
    def test_layer_order_precedes_alias(self):
        skill=self.root/'skill';skill.mkdir()
        (self.root/'.env').write_text('ALPHAXIV_API_TOKEN=project\n')
        (skill/'.env').write_text('ALPHAXIV_API_TOKEN=skill\n')
        with mock.patch.dict(os.environ, {'ALPHAXIV_API_KEY':'process'}, clear=True):
            self.assertEqual(svc.token(self.root,skill,'ALPHAXIV_API_TOKEN','ALPHAXIV_API_KEY'),'process')
        with mock.patch.dict(os.environ,{},clear=True):
            self.assertEqual(svc.token(self.root,skill,'ALPHAXIV_API_TOKEN'),'skill')
            (skill/'.env').unlink()
            self.assertEqual(svc.token(self.root,skill,'ALPHAXIV_API_TOKEN'),'project')

    def test_empty_disables_fallback_and_unused_dotenv_not_parsed(self):
        (self.root/'.env').write_text('invalid dotenv\n')
        with mock.patch.dict(os.environ,{'TOKEN':'ok'},clear=True):
            self.assertEqual(svc.token(self.root,self.root,'TOKEN'),'ok')
            os.environ['TOKEN']=''
            with self.assertRaises(svc.ServiceError): svc.token(self.root,self.root,'TOKEN')

    def test_dotenv_is_literal_and_validated(self):
        p=self.root/'.env';p.write_text('A=$(touch SHOULD_NOT_EXIST)\nB="${UNCHANGED}" # comment\n')
        self.assertEqual(svc.dotenv(p)['B'],'${UNCHANGED}')
        self.assertFalse((self.root/'SHOULD_NOT_EXIST').exists())
        p.write_text('broken')
        with self.assertRaises(svc.ServiceError): svc.dotenv(p)

    def test_official_origins_only_and_redirect_refused(self):
        self.assertEqual(svc.endpoint('https://api.sciverse.space','sciverse.space',subdomains=True),'https://api.sciverse.space')
        for u in ['http://api.sciverse.space','https://sciverse.space.evil.test','https://key@api.sciverse.space','https://api.sciverse.space:444','https://api.sciverse.space/path']:
            with self.assertRaises(svc.ServiceError): svc.endpoint(u,'sciverse.space',subdomains=True)
        with self.assertRaises(svc.ServiceError): svc.NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test')

    def test_http_error_does_not_echo_body_or_secret(self):
        error=HTTPError('https://api.sciverse.space',401,'secret-token',{},io.BytesIO(b'secret-token'))
        with mock.patch.object(svc,'build_opener') as opener:
            opener.return_value.open.side_effect=error
            with self.assertRaises(svc.ServiceError) as caught:
                svc.request_bytes('https://api.sciverse.space')
        self.assertNotIn('secret-token',str(caught.exception))
        self.assertIn('401',str(caught.exception))

    def test_response_limit(self):
        with mock.patch.object(svc,'MAX_RESPONSE',2),mock.patch.object(svc,'build_opener') as opener:
            response=opener.return_value.open.return_value.__enter__.return_value
            response.read.return_value=b'long'
            with self.assertRaises(svc.ServiceError): svc.request_bytes('https://api.sciverse.space')

    def test_output_redacts_escaped_token(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out): svc.emit({'key':'secret"quote'},('secret"quote',))
        self.assertEqual(json.loads(out.getvalue())['key'],'[REDACTED]')

    def test_sse_multiline_and_notifications(self):
        body=b': ping\n\nevent: message\ndata: {"id":1,\ndata: "result":{"ok":true}}\n\ndata: [DONE]\n\n'
        self.assertEqual(alpha.messages(body,'text/event-stream')[0]['result'],{'ok':True})
        self.assertEqual(alpha.messages(b'','application/json'),[])

    def test_mcp_negotiation_session_schema_and_call(self):
        calls=[]
        def transport(url,**kw):
            payload=kw['payload'];calls.append(kw)
            if payload['method']=='notifications/initialized': return b'',{}
            method=payload['method']
            value=({'protocolVersion':'2025-03-26'} if method=='initialize' else
                   {'tools':[{'name':'get_paper_content','inputSchema':{'required':['url']}}]} if method=='tools/list' else
                   {'content':[{'type':'text','text':'source passage'}]})
            return json.dumps({'id':payload['id'],'result':value}).encode(),{'mcp-session-id':'real-session'}
        with mock.patch.object(alpha,'request_bytes',side_effect=transport):
            c=alpha.McpClient('secret');result=c.call('get_paper_content',{'url':'https://arxiv.org/abs/2601.01234'})
        self.assertIn('content',result)
        self.assertEqual(calls[1]['headers']['Mcp-Session-Id'],'real-session')
        self.assertEqual(calls[-1]['headers']['MCP-Protocol-Version'],'2025-03-26')
        self.assertEqual(calls[-1]['payload']['method'],'tools/call')

    def test_mcp_read_allowlist_errors_and_schema(self):
        c=alpha.McpClient('secret')
        with self.assertRaises(svc.ServiceError): c.call('delete_folder',{})
        with mock.patch.object(c,'tools',return_value={'tools':[{'name':'get_paper_content','inputSchema':{'required':['url']}}]}):
            with self.assertRaises(svc.ServiceError): c.call('get_paper_content',{})
        with mock.patch.object(c,'post',return_value=[{'id':1,'result':{'isError':True}}]):
            with self.assertRaises(svc.ServiceError): c.rpc('tools/call')
        with mock.patch.object(c,'post',return_value=[{'id':999,'result':{}}]):
            with self.assertRaises(svc.ServiceError): c.rpc('tools/call')

    def test_mcp_pagination(self):
        c=alpha.McpClient('secret');c.ready=True
        with mock.patch.object(c,'rpc',side_effect=[{'tools':[{'name':'a'}],'nextCursor':'next'},{'tools':[{'name':'b'}]}]):
            self.assertEqual(len(c.tools()['tools']),2)
        with mock.patch.object(c,'rpc',return_value={'tools':[],'nextCursor':'same'}):
            with self.assertRaises(svc.ServiceError): c.tools()

    def test_sciverse_routes_and_filters(self):
        method,path,_,body=sci.route('search',{'query':'q','year_from':2025,'authors':['A']})
        self.assertEqual((method,path),('POST','/meta-search'))
        self.assertEqual(body['filters'][0]['operator'],'FILTER_OP_GTE')
        self.assertEqual(sci.route('semantic',{'query':'q','mode':'quality'})[3]['sub_queries'],3)
        self.assertIn('a%2Fb',sci.route('evidence-get',{'schema_id':'a/b','evidence_id':'c'})[1])
        for command,args in [('content',{}),('semantic',{}),('evidence-get',{})]:
            with self.assertRaises(svc.ServiceError): sci.route(command,args)

    def test_sciverse_transport_and_non_object_failure(self):
        with mock.patch.object(sci,'request_bytes',return_value=(b'{"records":[]}',{})) as request:
            self.assertEqual(sci.retrieve('content',{'doc_id':'actual'},'secret'),{'records':[]})
            self.assertIn('doc_id=actual',request.call_args.args[0])
            self.assertEqual(request.call_args.kwargs['headers']['Authorization'],'Bearer secret')
        with mock.patch.object(sci,'request_bytes',return_value=(b'[]',{})):
            with self.assertRaises(svc.ServiceError): sci.retrieve('catalog',{},'secret')


class PreparationTests(TemporaryCase):
    def source(self,text='# Paper\nA result.\n'):
        p=self.root/'provided.md';p.write_text(text);return p
    def prepare(self,source,ident='paper',**kw):
        return prep.prepare(self.root,ident,source,parser='mineru',source_url='https://arxiv.org/abs/2601.01234',**kw)

    def test_text_only_keeps_caption_and_math(self):
        text,count=prep.text_only('# Paper\n![plot](images/a(b).png)\nCaption: x increases. $x^2$\n<img src="x.png">\n![b][fig]\n[fig]: x.png\n')
        self.assertEqual(count,3)
        self.assertIn('Caption: x increases. $x^2$',text)
        self.assertNotIn('images/a',text)
        self.assertNotIn('<img',text)

    def test_import_only_publishes_text_metadata_and_keeps_source(self):
        source=self.source('# Paper\n![x](x.png)\nMethod description.\n');before=source.read_bytes()
        result=self.prepare(source,repository='https://github.com/owner/repository')
        self.assertFalse(result['parser_execution_verified'])
        self.assertEqual(source.read_bytes(),before)
        self.assertEqual({p.name for p in (self.root/'ref/paper').iterdir()},{'paper.md','source.json','repo.txt'})
        self.assertEqual(result['markdown_sha256'],pio.digest(self.root/'ref/paper/paper.md'))
        self.assertEqual(list((self.root/'.runtime/paper-prep').iterdir()),[])

    def test_existing_record_never_overwritten(self):
        source=self.source();self.prepare(source)
        original=(self.root/'ref/paper/paper.md').read_bytes()
        source.write_text('Different text')
        with self.assertRaises(ValueError): self.prepare(source)
        self.assertEqual(original,(self.root/'ref/paper/paper.md').read_bytes())

    def test_invalid_id_symlink_and_signed_source_rejected(self):
        source=self.source()
        with self.assertRaises(ValueError): self.prepare(source,ident='../outside')
        (self.root/'ref').symlink_to(self.root.parent)
        with self.assertRaises(ValueError): self.prepare(source)
        with self.assertRaises(ValueError): prep.prepare(self.root,'x',source,parser='mineru',source_url='https://example.test/p?token=secret')

    def test_pdf_requires_execution_and_correct_magic(self):
        pdf=self.root/'paper.pdf';pdf.write_bytes(b'%PDF-1.7\nfixture')
        with self.assertRaises(ValueError): self.prepare(pdf)
        self.assertTrue(pdf.exists())
        pdf.write_bytes(b'not pdf')
        with self.assertRaises(ValueError): self.prepare(pdf,execute=True)

    def test_parser_command_contract(self):
        self.assertEqual(prep.parser_command('mineru',None,Path('in.pdf'),Path('out')),['mineru','-p','in.pdf','-o','out','-b','pipeline'])
        self.assertEqual(prep.parser_command('paddleocr',None,Path('in.pdf'),Path('out'))[1],'pp_structurev3')

    def test_mock_local_parser_cleans_pdf_and_images(self):
        pdf=self.root/'original.pdf';pdf.write_bytes(b'%PDF-1.7\nfixture')
        def fake(argv,*args):
            out=Path(argv[argv.index('-o')+1]);(out/'full.md').write_text('Text\n![figure](image.png)\nCaption\n');(out/'image.png').write_bytes(b'fake')
        with mock.patch.object(prep,'run',side_effect=fake): result=self.prepare(pdf,execute=True)
        self.assertTrue(result['parser_execution_verified'])
        self.assertTrue(pdf.exists())
        self.assertEqual(list((self.root/'.runtime/paper-prep').iterdir()),[])
        self.assertFalse(list((self.root/'ref').rglob('*.pdf')))
        self.assertFalse(list((self.root/'ref').rglob('*.png')))

    def test_multiple_pages_need_explicit_join(self):
        pdf=self.root/'original.pdf';pdf.write_bytes(b'%PDF-1.7\nfixture')
        def fake(argv,*args):
            out=Path(argv[argv.index('-o')+1]);(out/'page10.md').write_text('Tenth');(out/'page2.md').write_text('Second')
        with mock.patch.object(prep,'run',side_effect=fake):
            with self.assertRaises(ValueError): self.prepare(pdf,execute=True)
            result=self.prepare(pdf,execute=True,join_pages=True)
        self.assertEqual(result['fragments'],['page2.md','page10.md'])

    def test_failure_and_empty_output_not_published(self):
        pdf=self.root/'original.pdf';pdf.write_bytes(b'%PDF-1.7\nfixture')
        with mock.patch.object(prep,'run',side_effect=RuntimeError('parser failed')):
            with self.assertRaises(RuntimeError): self.prepare(pdf,execute=True)
        self.assertFalse((self.root/'ref/paper').exists())
        self.assertTrue(pdf.exists())
        self.assertEqual(list((self.root/'.runtime/paper-prep').iterdir()),[])
        with self.assertRaises(ValueError): self.prepare(self.source('  '))

    def test_real_local_process_timeout(self):
        start=time.monotonic()
        with self.assertRaises(RuntimeError): pio.run([sys.executable,'-c','import time;time.sleep(20)'],self.root,self.root/'log',.1)
        self.assertLess(time.monotonic()-start,5)

    def test_clone_plan_ignore_and_existing(self):
        gitinit(self.root);(self.root/'ref/p').mkdir(parents=True)
        (self.root/'ref/p/repo.txt').write_text('https://github.com/owner/repository\n')
        with self.assertRaises(ValueError): clone.clone(self.root,'p')
        (self.root/'.gitignore').write_text('/refrepo/\n')
        self.assertEqual(clone.clone(self.root,'p')['status'],'planned')
        (self.root/'refrepo/p').mkdir(parents=True)
        with self.assertRaises(ValueError): clone.clone(self.root,'p',execute=True)

    def test_mock_clone_records_commit_without_running_repo_code(self):
        gitinit(self.root);(self.root/'.gitignore').write_text('/refrepo/\n')
        (self.root/'ref/p').mkdir(parents=True);(self.root/'ref/p/repo.txt').write_text('git@github.com:owner/repository.git\n')
        def fake(argv,cwd,log,timeout,env):
            self.assertIn('--depth',argv);self.assertEqual(env['GIT_LFS_SKIP_SMUDGE'],'1')
            repo=Path(argv[-1]);gitinit(repo);(repo/'file').write_text('fixture')
            subprocess.run(['git','-C',str(repo),'add','file'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
        with mock.patch.object(clone,'run',side_effect=fake): result=clone.clone(self.root,'p',execute=True)
        self.assertEqual(len(result['commit']),40)
        self.assertTrue((self.root/'refrepo/p/.git/research-checkout.json').exists())

    def test_repository_urls_reject_credentials_and_local_protocols(self):
        for url in ['file:///tmp/repo','https://token@github.com/a/b','https://github.com/a/b?token=x','ext::sh -c whatever','https://github.com/a/../b']:
            with self.assertRaises(ValueError): pio.repo_url(url)


class NativeTests(TemporaryCase):
    def setUp(self):
        super().setUp();(self.root/'research').mkdir();(self.root/'spec').mkdir()
        (self.root/'research/brief.md').write_text('A bounded research question')
        cp.save(self.root/'spec/autonomy.json',dict(max_rounds=6,total_seconds=7200,round_seconds=1200,max_no_progress=2,max_revisions=2))
        (self.root/'research/evidence.md').write_text('Actual local fixture, not scientific data')
        (self.root/'research/review.md').write_text('Fixture review, not an actual model review')
    def event(self,ident,**kw):
        args=dict(status='continue',summary='Fixture',next_action='Inspect next source',artifacts=['research/evidence.md']);args.update(kw)
        return cp.record(self.root,ident,**args)

    def test_native_start_record_and_actual_evidence_hash(self):
        state=cp.start(self.root);self.assertEqual(cp.gate(self.root,state),'active')
        state=self.event(state['id'])
        self.assertEqual(state['events'][0]['artifacts'][0]['sha256'],cp.digest(self.root/'research/evidence.md'))
        self.assertEqual(state['mode'],'native-subagents')

    def test_progress_and_completion_require_evidence_review(self):
        state=cp.start(self.root)
        with self.assertRaises(ValueError): self.event(state['id'],artifacts=[])
        with self.assertRaises(ValueError): self.event(state['id'],status='complete')
        done=self.event(state['id'],status='complete',review='research/review.md')
        self.assertEqual(done['status'],'completed')
        with self.assertRaises(ValueError): self.event(state['id'])

    def test_contract_changes_and_stop(self):
        state=cp.start(self.root);(self.root/'spec/new.md').write_text('New constraint')
        self.assertEqual(cp.gate(self.root,state),'contract-changed')
        (self.root/'spec/new.md').unlink();(self.root/'.runtime').mkdir();(self.root/'.runtime/STOP').touch()
        self.assertEqual(cp.gate(self.root,state),'stopped')

    def test_no_progress_and_revision_limits(self):
        for status in ['no-progress','revise']:
            state=cp.start(self.root);self.event(state['id'],status=status,artifacts=[])
            state=self.event(state['id'],status=status,artifacts=[])
            self.assertEqual(state['status'],'stalled')

    def test_resume_does_not_reset_time_or_round_budget(self):
        state=cp.start(self.root);original=state['created_at']
        with mock.patch.object(cp.time,'time',return_value=original+7201):
            self.assertEqual(cp.gate(self.root,cp.load(cp.state_path(self.root,state['id']))),'budget-exhausted')
            late=self.event(state['id'])
        self.assertEqual(late['created_at'],original)
        self.assertEqual(late['status'],'budget-exhausted')
        self.assertEqual(len(late['events']),1)

    def test_bad_paths_and_legacy_state_rejected(self):
        with self.assertRaises(ValueError): cp.state_path(self.root,'C-old')
        for path in ['../outside','.env','research/missing.md']:
            with self.assertRaises(ValueError): cp.evidence(self.root,path)
        state=cp.start(self.root)
        with self.assertRaises(ValueError): self.event(state['id'],agents=[{'role':'reviewer'}])

    def test_retired_driver_cannot_start_models(self):
        result=subprocess.run([sys.executable,str(SKILLS/'research-autopilot/scripts/loop.py'),'--execute'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('retired',result.stderr)
        import ast
        for file in [SKILLS/'research-autopilot/scripts/loop.py',SKILLS/'research-autopilot/scripts/checkpoint.py']:
            tree=ast.parse(file.read_text())
            names={alias.name for node in ast.walk(tree) if isinstance(node,(ast.Import,ast.ImportFrom)) for alias in node.names}
            self.assertNotIn('subprocess',names)


class ManuscriptTests(TemporaryCase):
    def setUp(self):
        super().setUp();gitinit(self.root);(self.root/'.gitignore').write_text('/paper/\n')
        self.repo=self.root/'paper';gitinit(self.repo)

    def test_independent_registered_repository_boundary(self):
        self.assertEqual(pr.paper_repo(self.root,'paper'),self.repo)
        (self.root/'workspace.local.json').write_text(json.dumps({'paper_repo':'paper'}))
        self.assertEqual(pr.paper_repo(self.root),self.repo)
        for value in ['.','paper/nested']:
            with self.assertRaises(ValueError): pr.paper_repo(self.root,value)
        (self.root/'.gitignore').write_text('')
        with self.assertRaises(ValueError): pr.paper_repo(self.root,'paper')

    def test_latex_scaffold_preserves_existing(self):
        self.assertEqual(latex.initialize(self.repo)['status'],'created')
        self.assertEqual(latex.check(self.repo)['status'],'WARN')
        before=(self.repo/'main.tex').read_bytes()
        with self.assertRaises(ValueError): latex.initialize(self.repo)
        self.assertEqual((self.repo/'main.tex').read_bytes(),before)

    def test_latex_literal_refs_citations_and_duplicates(self):
        (self.repo/'main.tex').write_text(r'\label{x}\label{x}\ref{missing}\cite{absent}')
        result=latex.check(self.repo)
        self.assertEqual(result['status'],'FAIL');self.assertEqual(len(result['errors']),3)
        (self.repo/'main.tex').write_text(r'\label{x}\ref{x}\cite{real}')
        (self.repo/'refs.bib').write_text('@article{real, title={Verified externally}}')
        self.assertEqual(latex.check(self.repo)['status'],'PASS')

    def test_latex_include_cannot_escape(self):
        (self.repo/'main.tex').write_text(r'\input{../secret}')
        with self.assertRaises(ValueError): latex.check(self.repo)

    def test_build_plan_no_rc_and_no_shell_escape(self):
        latex.initialize(self.repo);result=latex.build(self.repo)
        self.assertEqual(result['status'],'planned');self.assertIn('-norc',result['argv'])
        self.assertIn('-pdflatex=pdflatex -no-shell-escape %O %S',result['argv'])
        self.assertFalse((self.repo/'.build').exists())
        with mock.patch.object(latex.shutil,'which',return_value=None):
            with self.assertRaises(ValueError): latex.build(self.repo,execute=True)

    def test_numeric_csv_validation(self):
        csv=self.root/'data.csv';csv.write_text('x,y\na,1\na,2\n')
        with self.assertRaises(ValueError): plot.read_rows(csv,'x','y','bar')
        csv.write_text('x,y,e\n1,nan,0\n')
        with self.assertRaises(ValueError): plot.read_rows(csv,'x','y','line','e')
        csv.write_text('x,y,e\n1,2,-1\n')
        with self.assertRaises(ValueError): plot.read_rows(csv,'x','y','line','e')

    def test_real_plot_and_standalone_rerender(self):
        try: import matplotlib
        except ImportError: self.skipTest('Optional matplotlib unavailable')
        csv=self.root/'data.csv';csv.write_text('method,score\nBaseline,10\nCandidate,12\n')
        out=self.repo/'figures/comparison'
        result=plot.render(csv,out,x='method',y='score',xlabel='Method',ylabel='Score (fixture units)',kind='bar')
        self.assertEqual(result['status'],'rendered')
        receipt=json.loads((out/'provenance.json').read_text());self.assertFalse(receipt['scientific_verification'])
        self.assertEqual((out/'data.csv').read_bytes(),csv.read_bytes())
        self.assertTrue((out/'figure.pdf').read_bytes().startswith(b'%PDF'))
        subprocess.run([sys.executable,str(out/'figure.py')],check=True,timeout=30)
        with self.assertRaises(ValueError): plot.render(csv,out,x='method',y='score',xlabel='Method',ylabel='Score',kind='bar')

    def test_error_bar_meaning_required(self):
        csv=self.root/'data.csv';csv.write_text('x,y,e\n1,2,.1\n')
        with self.assertRaises(ValueError): plot.render(csv,self.repo/'figures/x',x='x',y='y',xlabel='x',ylabel='y',error='e')


class ConfigurationTests(unittest.TestCase):
    def test_all_skills_carry_clear_language_policy(self):
        files=list(SKILLS.glob('*/SKILL.md'));self.assertEqual(len(files),11)
        for file in files:
            text=file.read_text();self.assertIn('## Communication',text)
            self.assertIn('Chinese gloss',text);self.assertIn('uncertainty',text)

    def test_eight_native_roles_have_model_effort_and_no_grandchildren(self):
        files=list((ROOT/'.codex/agents').glob('*.toml'));self.assertEqual(len(files),8)
        for file in files:
            role=tomllib.loads(file.read_text());self.assertIn(role['model'],{'gpt-5.6-luna','gpt-5.6-terra','gpt-6-astra'})
            self.assertIn(role['model_reasoning_effort'],{'low','medium','high'})
            self.assertIn('subagents',role['developer_instructions'])
        cfg=tomllib.loads((ROOT/'.codex/config.toml').read_text())
        self.assertEqual(cfg['agents']['max_concurrent_threads_per_session'],3)
        self.assertNotIn('model',cfg)

    def test_ignore_binaries_but_keep_research_text(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);gitinit(root);shutil.copy(ROOT/'.gitignore',root/'.gitignore')
            for path in ['ref/paper/paper.PDF','ref/paper/images/plot.png','ref/paper/plot.SVG','ref/paper/plot.jpg','refrepo/x/a.py']:
                self.assertEqual(subprocess.run(['git','-C',d,'check-ignore','-q',path]).returncode,0,path)
            for path in ['ref/paper/paper.md','ref/paper/source.json','ref/paper/repo.txt','research/findings/a.md','task/active/a/meta.json']:
                self.assertEqual(subprocess.run(['git','-C',d,'check-ignore','-q',path]).returncode,1,path)

if __name__=='__main__':
    unittest.main()
