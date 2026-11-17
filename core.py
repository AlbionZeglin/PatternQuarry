"""Append-only revisions and explicit, immutable public releases."""
import copy
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone

FIELDS = ['context', 'problem', 'forces', 'solution', 'resulting_context', 'benefits', 'costs', 'instances', 'exceptions', 'boundaries', 'controls']
CHECKS = ['consent', 'redaction', 'licensing', 'disclosure']

def now():
    return datetime.now(timezone.utc).isoformat()

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS revisions (
              id TEXT NOT NULL, rev INTEGER NOT NULL, kind TEXT NOT NULL,
              project TEXT NOT NULL, body TEXT NOT NULL, author TEXT NOT NULL,
              date TEXT NOT NULL, decision TEXT NOT NULL, PRIMARY KEY(id,rev));
            CREATE TABLE IF NOT EXISTS releases (
              id TEXT PRIMARY KEY, project TEXT NOT NULL, body TEXT NOT NULL);
            ''')

    def db(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def get(self, entity, rev=None, db=None):
        if db is None:
            with self.db() as connection:
                return self.get(entity, rev, connection)
        query = 'SELECT * FROM revisions WHERE id=?'
        args = [entity]
        if rev is not None:
            query += ' AND rev=?'
            args.append(rev)
        row = db.execute(query + ' ORDER BY rev DESC LIMIT 1', args).fetchone()
        if not row:
            raise ValueError('Revision not found')
        return dict(row) | {'body': json.loads(row['body'])}

    def all(self, project=None):
        with self.db() as db:
            rows = db.execute('SELECT r.* FROM revisions r JOIN (SELECT id, MAX(rev) rev FROM revisions GROUP BY id) h ON r.id=h.id AND r.rev=h.rev ORDER BY r.date').fetchall()
        return [dict(r) | {'body': json.loads(r['body'])} for r in rows if project is None or r['project'] == project or r['kind'] == 'project']

    def history(self, entity):
        with self.db() as db:
            return [dict(r) | {'body': json.loads(r['body'])} for r in db.execute('SELECT * FROM revisions WHERE id=? ORDER BY rev DESC', [entity])]

    def validate_pattern(self, body, project, db):
        if not body.get('name', '').strip():
            raise ValueError('A pattern needs a name')
        for link in body.get('relationships', []):
            target = self.get(link['target'], db=db)
            if link['type'] not in ['parent', 'supporting', 'conflicting'] or target['kind'] != 'pattern' or target['project'] != project:
                raise ValueError('Relationships must link to patterns in this project')
        for field, refs in body.get('claims', {}).items():
            if field not in FIELDS:
                raise ValueError('Unknown claim field')
            for ref in refs:
                evidence = self.get(ref['id'], ref['rev'], db)
                if evidence['kind'] != 'excerpt' or evidence['project'] != project:
                    raise ValueError('Evidence must belong to this project')
        if body.get('status') == 'approved':
            for field in FIELDS:
                if not body.get(field, '').strip() or not body.get('claims', {}).get(field):
                    raise ValueError('Approval requires text and evidence anchors for every claim field: ' + field)
            if not body.get('license', '').strip():
                raise ValueError('Record reuse terms before approval')

    def save(self, kind, project, body, author, decision, entity=None, base=None):
        if kind not in ['project', 'session', 'excerpt', 'pattern']:
            raise ValueError('Unknown entity type')
        if not author.strip() or not decision.strip():
            raise ValueError('Author and editorial decision are required')
        body = copy.deepcopy(body)
        if not isinstance(body, dict):
            raise ValueError('Record body must be an object')
        if kind in ['project', 'session'] and not body.get('name', '').strip():
            raise ValueError('A name is required')
        if kind == 'session' and not body.get('consent_notes'):
            raise ValueError('Record consent to retain interview notes before saving')
        if kind == 'pattern' and body.get('status') not in ['draft', 'approved']:
            raise ValueError('Choose draft or approved status')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if entity:
                old = self.get(entity, db=db)
                if old['kind'] != kind or old['project'] != project:
                    raise ValueError('Entity scope cannot change')
                if old['rev'] != base:
                    raise ValueError('This item changed. Reload before saving to avoid overwriting another revision.')
                rev = old['rev'] + 1
            else:
                entity = kind[:3].upper() + '-' + uuid.uuid4().hex[:10]
                rev = 1
            if kind != 'project':
                p = self.get(project, db=db)
                if p['kind'] != 'project':
                    raise ValueError('Invalid project')
            if kind == 'pattern':
                self.validate_pattern(body, project, db)
            if kind == 'excerpt':
                session = self.get(body['session'], db=db)
                if session['kind'] != 'session' or session['project'] != project:
                    raise ValueError('Excerpt must belong to a session in this project')
                if body.get('visibility') not in ['private', 'public'] or not body.get('text', '').strip():
                    raise ValueError('Excerpt text and visibility are required')
            if kind == 'session' and body.get('visibility') not in ['private', 'public']:
                raise ValueError('Choose session visibility')
            db.execute('INSERT INTO revisions VALUES (?,?,?,?,?,?,?,?)', [entity, rev, kind, project if kind != 'project' else entity, canonical(body), author.strip(), now(), decision.strip()])
        return self.get(entity)

    def promote(self, entity, rev, reviewer, checks, note):
        if not reviewer.strip() or not note.strip() or not all(checks.get(c) is True for c in CHECKS):
            raise ValueError('A named reviewer, review note, and all four publication checks are required')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            pattern = self.get(entity, rev, db)
            if pattern['kind'] != 'pattern' or pattern['body'].get('status') != 'approved':
                raise ValueError('Select an approved pattern revision')
            self.validate_pattern(pattern['body'], pattern['project'], db)
            evidence = {}
            for refs in pattern['body']['claims'].values():
                for ref in refs:
                    e = self.get(ref['id'], ref['rev'], db)
                    current = self.get(e['id'], db=db)
                    session = self.get(e['body']['session'], db=db)
                    project = self.get(e['project'], db=db)
                    if e['body'].get('visibility') != 'public' or current['body'].get('visibility') != 'public':
                        raise ValueError('Private evidence cannot enter a publication. Create a separately reviewed, redacted public excerpt and cite it.')
                    if not session['body'].get('consent_public') or not project['body'].get('consent_public'):
                        raise ValueError('Project and session must both record consent to publish')
                    if not e['body'].get('license', '').strip() or not e['body'].get('consent_public') or not current['body'].get('consent_public'):
                        raise ValueError('Every cited excerpt needs public reuse consent and terms')
                    # Explicit allowlist: no session notes, interview identity, prompts, or private revision history.
                    evidence[e['id'] + '@' + str(e['rev'])] = {
                        'id': e['id'], 'rev': e['rev'], 'text': e['body']['text'],
                        'source': e['body'].get('source', ''), 'anchor': e['body'].get('anchor', ''),
                        'license': e['body']['license'], 'author': e['author'], 'date': e['date'],
                        'sha256': hashlib.sha256(canonical(e['body']).encode()).hexdigest()}
            b = pattern['body']
            public_pattern = {k: b.get(k, '') for k in ['name', 'license'] + FIELDS}
            public_pattern['claims'] = b['claims']
            public_pattern['relationships'] = b.get('relationships', [])
            release = {'schema_version': '1.0', 'exporter_version': '1.0.0',
                       'pattern': {'id': entity, 'rev': rev, 'author': pattern['author'], 'date': pattern['date'], **public_pattern},
                       'evidence': sorted(evidence.values(), key=lambda e: (e['id'], e['rev'])),
                       'review': {'reviewer': reviewer, 'date': now(), 'checks': checks, 'note': note},
                       'disclosure': 'Original pattern text; fictional examples where stated. No AI generation in this prototype. Control references are candidate links, not a compliance assessment.'}
            release['input_sha256'] = hashlib.sha256(canonical({'pattern': release['pattern'], 'evidence': release['evidence']}).encode()).hexdigest()
            release_id = 'REL-' + uuid.uuid4().hex[:10]
            release['id'] = release_id
            db.execute('INSERT INTO releases VALUES (?,?,?)', [release_id, pattern['project'], canonical(release)])
        return release

    def releases(self, project=None):
        with self.db() as db:
            rows = db.execute('SELECT * FROM releases ORDER BY rowid DESC').fetchall()
        return [json.loads(r['body']) for r in rows if project is None or r['project'] == project]


def markdown(release):
    p = release['pattern']
    lines = [f"# {p['name']}", f"\n{p['id']} · revision {p['rev']} · {p['license']}"]
    for field in FIELDS:
        refs = ', '.join(f"[{r['id']} r{r['rev']}](#evidence-{r['id'].lower()}-{r['rev']})" for r in p['claims'].get(field, []))
        lines += [f"\n## {field.replace('_', ' ').title()}", '\n' + p[field], '\nEvidence: ' + refs]
    lines += ['\n## Relationships']
    for link in p['relationships']:
        lines += [f"- {link['type']}: [{link['target']}]({link['target']}.md)"]
    lines += ['\n## Evidence']
    for e in release['evidence']:
        lines += [f"\n<a id=\"evidence-{e['id'].lower()}-{e['rev']}\"></a>", f"\n### {e['id']} r{e['rev']}", '\n' + e['text'], f"\nSource: {e['source']} · {e['anchor']} · {e['license']}", f"\nRecorded by {e['author']} on {e['date']} · SHA-256 {e['sha256']}"]
    lines += ['\n## Publication record', '\n' + canonical({k: v for k, v in release.items() if k not in ['pattern', 'evidence']})]
    return '\n'.join(lines) + '\n'
