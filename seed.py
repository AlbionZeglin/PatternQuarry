from core import FIELDS

PROMPTS = [
'Tell me about one real incident. What happened, and what was at stake?',
'Where and how often does this situation recur? What makes these cases alike?',
'Who was involved, and who experienced the consequences?',
'Which needs or forces pulled in different directions?',
'What did you try first? What alternatives did you reject, and why?',
'What worked? What observable evidence supports that account?',
'What failed or created a new burden? Does anyone remember it differently?',
'When would this approach stop working? What is a counterexample?',
'What larger arrangement makes this possible? What smaller practice sustains it?',
'What remains uncertain, and who or which vetted standard could help resolve it?'
]

def seed(store):
    if store.all():
        return
    def save(kind, project, body, decision='Fictional demonstration; original wording'):
        return store.save(kind, project, body, 'Demo editor', decision)
    p = save('project', '', {'name': 'A steadier change window', 'objective': 'Learn how a fictional civic IT team makes urgent changes accountable.', 'scope': 'Release coordination for a fictional public benefits service. No real agency or citizen data.', 'tenant': 'Local workspace', 'visibility': 'private', 'consent_public': True})
    pid = p['id']
    s = save('session', pid, {'name': '01 · The Friday patch', 'expert': 'Morgan, fictional service lead', 'interviewer': 'Demo interviewer', 'objective': 'Reconstruct the incident before naming a pattern.', 'scope': 'One urgent patch and the practices around it.', 'visibility': 'private', 'consent_notes': True, 'consent_public': True, 'consent_record': 'Fictional participant; demo evidence may be shared under CC0-1.0.', 'notes': 'Fictional interview. Interviewer: Tell me about a specific incident. Morgan: A Friday patch was needed before the next benefit run. The service owner wanted speed, while the release lead needed a credible rollback decision. We agreed who could stop the release and wrote down the signals before starting.', 'questions': 'Would the same practice work with a vendor running the release? Ask an external controls specialist about documentation expectations.', 'disagreements': 'The release lead attributes success to the stop rule. The service owner thinks the rehearsal mattered more.', 'prompt_feedback': 'Try asking “what would you have seen if it failed?” before asking for benefits.', 'prompt_index': 0})
    private = save('excerpt', pid, {'session': s['id'], 'text': 'PRIVATE-DEMO-ONLY: Morgan names the internal bridge and a colleague’s direct contact. This detail is deliberately excluded from all public claims.', 'source': 'Fictional interview, restricted working notes', 'anchor': '00:03–00:04', 'visibility': 'private', 'license': 'No public reuse', 'consent_public': False})
    texts = [
('00:05–00:09', 'Fictional incident: an urgent benefits-service patch had to land before the next run. The service owner and release lead agreed on a named decision owner, a stop authority, and a shared evidence log. This kept urgency from erasing responsibility, but coordination took time. It recurs during urgent cross-team changes. A log alone cannot resolve disputed authority; that needs leadership. The team used it in a patch and a rehearsal. Candidate control evidence: decision log with timestamps; controls specialist review remains necessary.'),
('00:10–00:14', 'Fictional incident: before deploying, the team wrote down a queue-delay threshold, a rollback owner, and a decision time. Speed competed with reversibility. A rehearsal made the threshold usable. The patch completed; one earlier test failed because nobody watched the signal. Monitoring and rehearsal cost staff time. This practice recurs in bounded releases, but fails if rollback is impossible or monitoring is stale. A second rehearsal used the same form. Candidate evidence: approved stop criteria and rehearsal record; technical validation is required.'),
('00:15–00:18', 'Fictional incident: the handoff included a short receipt listing the change, signals to watch, the next owner, and an acknowledgement. A long email had previously gone unread. Completeness competed with attention. The receipt reduced ambiguity in two rehearsed handoffs, with the cost of maintaining a concise summary. It helps across shifts; it fails when the receiving team lacks authority or cannot acknowledge. Candidate evidence: acknowledged handoff record; do not treat acknowledgement as proof of effectiveness.')]
    excerpts = [save('excerpt', pid, {'session': s['id'], 'text': text, 'source': 'Original fictional interview, reviewed public summary', 'anchor': anchor, 'visibility': 'public', 'license': 'CC0-1.0', 'consent_public': True}) for anchor, text in texts]
    values = [
['A named decision lane', 'Urgent changes crossing service and release teams.', 'Urgency obscures who can decide or stop a change.', 'Fast delivery; accountable authority; limited coordination time.', 'Name a decision owner and stop authority before work begins; keep their decisions in a shared log.', 'Teams have a visible decision route for this change.', 'Decisions can be reconstructed and challenged.', 'Coordination time and log maintenance.', 'Fictional patch and rehearsal described in the evidence.', 'A log cannot resolve disputed authority.', 'Assumption: leadership accepts the authority assignment. Competing account: rehearsal may explain success better. Seek an external controls specialist.', 'Candidate organizational control: documented responsibility. Possible evidence: timestamped decision log. GAO Green Book, https://www.gao.gov/greenbook, is a relevant public input for a specialist to vet; no conformance claim.'],
['Rehearse the stop rule', 'A bounded release with observable service signals.', 'A team recognizes failure too late to reverse a change.', 'Release speed; reversibility; confidence in monitoring.', 'Before release, specify a measurable stop signal, its observer, a rollback owner, and a decision time; rehearse the response.', 'A release has an executable route back to a known state.', 'The team can act on a signal without renegotiating roles.', 'Rehearsal effort and monitoring overhead.', 'Fictional urgent patch and second rehearsal.', 'Irreversible migrations require a different recovery strategy.', 'Assumption: signals are timely and rollback is valid. External technical review is needed for thresholds. The interview does not establish causal effectiveness.', 'Candidate technical control: change recovery testing. Possible evidence: stop criteria and dated rehearsal record.'],
['An acknowledged handoff', 'Work passes between shifts or operating teams.', 'A sender mistakes a sent message for shared understanding.', 'Completeness; attention; continuity of ownership.', 'Send a short receipt naming the change, watch signals, and next owner; obtain an explicit acknowledgement.', 'The receiving team has accepted the next action.', 'Ambiguity is visible before the sender leaves.', 'A summary must be maintained and acknowledged.', 'Two fictional rehearsed shift handoffs.', 'An acknowledgement cannot confer missing authority.', 'Assumption: the receiver can act. Seek a counterexample from an unstaffed shift. Acknowledgement is not evidence of effectiveness.', 'Candidate operational control: continuity of responsibility. Possible evidence: dated handoff receipt.']]
    patterns = []
    for vals, e in zip(values, excerpts):
        b = dict(zip(['name'] + FIELDS, vals))
        b.update(status='approved', license='CC0-1.0', claims={f: [{'id': e['id'], 'rev': e['rev']}] for f in FIELDS}, relationships=[])
        patterns.append(save('pattern', pid, b))
    for i, pattern in enumerate(patterns):
        b = pattern['body']
        b['relationships'] = ([{'type': 'supporting', 'target': patterns[1]['id']}, {'type': 'supporting', 'target': patterns[2]['id']}] if i == 0 else [{'type': 'parent', 'target': patterns[0]['id']}])
        pattern = store.save('pattern', pid, b, 'Demo editor', 'Connect the example language; retain claim anchors', pattern['id'], pattern['rev'])
        store.promote(pattern['id'], pattern['rev'], 'Demo reviewer', {c: True for c in ['consent', 'redaction', 'licensing', 'disclosure']}, 'Reviewed original fictional summaries and original pattern wording; no real participant information. CC0-1.0 applies to the demo content.')
    save('pattern', pid, {'name': 'A quiet escalation channel', **{f: '' for f in FIELDS}, 'status': 'draft', 'license': '', 'claims': {'problem': [{'id': private['id'], 'rev': 1}]}, 'relationships': []}, 'Working hypothesis only; private evidence must not be published')
