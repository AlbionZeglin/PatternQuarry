import copy
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from core import Store, FIELDS
from seed import seed
from server import bundle

CHECKS = dict(consent=True, redaction=True, licensing=True, disclosure=True)

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / 'test.sqlite3')
        seed(self.store)
        self.project = next(i for i in self.store.all() if i['kind']=='project')['id']
        self.pattern = next(i for i in self.store.all() if i['kind']=='pattern' and i['body']['status']=='approved')

    def tearDown(self):
        self.temp.cleanup()

    def edit(self, item, body):
        return self.store.save(item['kind'], item['project'], body, 'Test editor', 'Review evidence', item['id'], item['rev'])

    def test_revisions_and_conflict(self):
        old = copy.deepcopy(self.pattern)
        new = self.edit(old, old['body'] | {'solution':'A revised form', 'status':'draft'})
        self.assertEqual(new['rev'], old['rev']+1)
        self.assertEqual(self.store.get(old['id'], old['rev']), old)
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.edit(old, old['body'])
        reopened = Store(self.store.path)
        self.assertEqual(reopened.get(new['id']), new)

    def test_trace_and_deterministic_export(self):
        releases = self.store.releases()
        first = bundle(releases)
        self.assertEqual(first, bundle(releases))
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            content = '\n'.join(archive.read(n).decode() for n in archive.namelist())
            self.assertNotIn('PRIVATE-DEMO-ONLY', content)
            self.assertNotIn('consent_record', content)
            for r in releases:
                for f in FIELDS:
                    for ref in r['pattern']['claims'][f]:
                        evidence = next(e for e in r['evidence'] if e['id']==ref['id'] and e['rev']==ref['rev'])
                        source = self.store.get(ref['id'], ref['rev'])
                        self.assertEqual(evidence['text'], source['body']['text'])
                for link in r['pattern']['relationships']:
                    self.assertIn(link['target']+'.md', archive.namelist())

    def test_full_capture_draft_approve_publish(self):
        session = next(i for i in self.store.all() if i['kind']=='session')
        evidence = self.store.save('excerpt', self.project, {'session':session['id'],'text':'A reviewed fictional incident: a team rehearsed its handoff.', 'visibility':'public','consent_public':True,'license':'CC0-1.0','source':'Original fictional interview','anchor':'paragraph 1'},'Interviewer','Capture a reviewed summary')
        body = {'name':'A test form', 'status':'draft', 'license':'CC0-1.0', 'relationships':[], **{f:'A claim drawn from the fictional test incident.' for f in FIELDS}, 'claims':{f:[{'id':evidence['id'],'rev':1}] for f in FIELDS}}
        draft = self.store.save('pattern', self.project, body, 'Editor', 'Extract candidate')
        approved = self.edit(draft, body | {'status':'approved'})
        release = self.store.promote(approved['id'], approved['rev'], 'Reviewer', CHECKS, 'Reviewed for public reuse')
        self.assertEqual(release['pattern']['rev'], 2)
        # Editing the source leaves the approved claim and frozen publication unchanged.
        self.edit(evidence, evidence['body'] | {'text':'Changed later'})
        self.assertEqual(release['evidence'][0]['text'], evidence['body']['text'])
        self.assertEqual(self.store.get(approved['id'])['body']['claims']['solution'][0]['rev'], 1)

    def test_private_evidence_and_consent_boundaries(self):
        private = next(i for i in self.store.all() if i['kind']=='excerpt' and i['body']['visibility']=='private')
        body = copy.deepcopy(self.pattern['body'])
        body['claims']['solution']=[{'id':private['id'],'rev':private['rev']}]
        p = self.edit(self.pattern, body)
        with self.assertRaisesRegex(ValueError,'Private evidence'):
            self.store.promote(p['id'],p['rev'],'Reviewer',CHECKS,'Review')
        session = next(i for i in self.store.all() if i['kind']=='session')
        self.edit(session, session['body'] | {'consent_public':False})
        with self.assertRaisesRegex(ValueError,'consent'):
            self.store.promote(self.pattern['id'],self.pattern['rev'],'Reviewer',CHECKS,'Review')

    def test_required_claims_and_checklist(self):
        body=copy.deepcopy(self.pattern['body'])
        body['claims']['forces']=[]
        with self.assertRaisesRegex(ValueError,'anchors'):
            self.edit(self.pattern,body)
        with self.assertRaisesRegex(ValueError,'four publication checks'):
            self.store.promote(self.pattern['id'],self.pattern['rev'],'Reviewer',{},'Review')

    def test_project_scope(self):
        p=self.store.save('project','',{'name':'Another project'},'Editor','New project')
        body=copy.deepcopy(self.pattern['body'])
        with self.assertRaisesRegex(ValueError,'this project'):
            self.store.save('pattern',p['id'],body,'Editor','Try cross-project evidence')

if __name__=='__main__':
    unittest.main()
