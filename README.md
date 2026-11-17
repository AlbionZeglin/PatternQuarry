# Pattern Quarry

A private, local interview workbench for eliciting and connecting original patterns. Start with a concrete incident, explore conflicting forces, draft alongside the evidence, approve an exact revision, then review a public release. The fictional government IT example contains three linked, published patterns and a deliberately private working excerpt.

## Run on a Mac M1

Install **Python 3.10 or newer** using the universal2 macOS installer from https://www.python.org/downloads/macos/ (or `brew install python` if you already use Homebrew). No Node, Docker, compiler, database service, or Python packages are required. Apple Silicon uses the same source files as other platforms.

Clone the existing GitHub repository, open Terminal, and run:

```sh
git clone https://github.com/AlbionZeglin/PatternQuarry.git
cd PatternQuarry
python3 server.py
```

Alternatively, download the repository ZIP, extract it, and open Terminal in the extracted folder before running `python3 server.py`.

Open **http://localhost:8765** in Safari or Chrome. Keep Terminal open; press Control-C to stop. Restart the same command to resume. You may also run `bash start.command` in the project folder. If macOS blocks double-clicking the launcher, use Terminal; changing Gatekeeper settings is unnecessary.

If the port is occupied, run `python3 server.py --port 8766` and open http://localhost:8766. The application always binds to 127.0.0.1.

The first start seeds fictional demo content. Data is saved in `data/studio.sqlite3`, outside the public catalog. This filename is retained for compatibility with earlier prototypes; the application is now named Pattern Quarry. Stop the server before backing up that file. Restoring it to the same location restores all saved revisions and releases. The database is sensitive and is not encrypted by this app. Use a protected Mac login, FileVault, and suitable backup protection. You can use `--data` to select a different database; a new database starts with the fictional example. Local databases and generated screenshots are excluded from Git.

## Use your iPhone over Tailscale

See [IPHONE.md](IPHONE.md). With Tailscale connected on your Mac, run `python3 iphone.py` in this folder. It prints a private HTTPS URL to open in Safari on an iPhone using the same Tailscale login. The launcher adds an explicit owner-identity check while leaving the backend bound to loopback. Keep the Mac awake and the Terminal open; Control-C stops this session. This does not establish a connection from the build workspace to your devices.

## Five-minute demonstration

1. In **Interview**, read “The Friday patch.” The private note is intentionally marked `PRIVATE-DEMO-ONLY`. Open questions, competing accounts, and prompt feedback stay visible in the working interview. Ten editable-source interview prompts are defined in `seed.py`; the current question position is saved.
2. Select a **public** excerpt and choose **Draft from selection**. Give the candidate an original working name. Its stable ID is assigned once; every claim starts anchored to the selected excerpt's exact revision.
3. In the workbench, write the context, recurring problem, forces, defining form, resulting context, benefits, costs, instances, exceptions, boundaries, and candidate controls. Each field needs its own evidence anchors. Add or remove anchors as appropriate; selecting evidence is not proof that it supports a claim. Use the boundaries field to identify assumptions, disagreements, and review needed from a qualified expert.
4. Add parent, supporting, or conflicting relationships to other project patterns. Record reuse terms, your name, and the editorial decision. **Save as new draft** preserves prior revisions. **Approve new revision** requires every claim field and evidence anchor. Approval is an editorial action, not a compliance certification.
5. Choose **Review for publication**. Check consent, redaction, licensing, and disclosure, and write a safe public review note. The server blocks private cited evidence and missing public reuse consent. A successful review creates a frozen local public-catalog snapshot; it does not upload anything.
6. In **Publication**, select one release per pattern and download the ZIP. “Select latest language” includes the three demo patterns together. Each Markdown claim links to exact public evidence in the same file; relationships link across pattern files. JSON includes stable IDs, revision numbers, claim anchors, public evidence, author/reviewer dates, reuse terms, and input hashes. `manifest.json` identifies the chosen releases.
7. Edit a pattern and save it. **Revision history** shows before/after field values and the author, date, and reason. The previous approved revision and release remain unchanged. Edit an excerpt: existing pattern anchors still resolve to its earlier revision. To cite the new excerpt, remove and re-add the claim anchor, then approve and publish a new revision.

The ready-made publication is in the `examples/language/` folder. Its three patterns are “A named decision lane,” “Rehearse the stop rule,” and “An acknowledged handoff.” You can generate a ZIP from the application's Publication screen. All prose is original and explicitly fictional. Inspiration from Alexander’s approach does not include copied pattern text.

## Try one real interview together

Create a **New project**; define the objective, scope, and whether reviewed publication is permitted. Create a session using a pseudonym if useful, record consent and its limits, then begin with a specific incident. Keep raw notes private. Save notes before advancing the guide, and use **Prompt feedback** to record questions that felt leading, vague, or premature. Save explicitly before leaving the page.

A useful first trial is 30–45 minutes: reconstruct one incident, test one counterexample, and draft one candidate together. Keep unresolved alternatives in **Competing accounts**, rather than forcing agreement. At the end, note which prompt should change and why; `seed.py`'s `PROMPTS` list is the small source file to revise. Existing sessions retain their notes and position; prompts currently use the application's installed list, not a per-session versioned template.

Capture an excerpt with a source title or URL and a timestamp, page, or paragraph anchor. For public reuse, create a **separate redacted public summary** instead of changing the original private transcript. Record permission on the project, session, and public excerpt. Both private and public evidence may support internal patterns, but a pattern that still cites private evidence cannot be promoted.

Before we use real material here in chat, agree on what may be shared. The app itself sends no interview data to AI or any outside service.

## Publication boundaries and reproducibility

- All entity edits append a revision; optimistic revision checking rejects stale writes. Editorial reasons are stored alongside immutable revisions. Local database owners can still modify the SQLite file directly; this is not a tamper-proof audit system.
- Claim anchors identify an excerpt ID and exact revision. Publication freezes the selected approved pattern and allowlisted public evidence fields in a separate SQLite table. It never serializes raw sessions, private notes, other excerpts, full histories, or project metadata.
- Publication checks use current project/session consent and current excerpt visibility and consent as well as the cited evidence revision. Existing publications are immutable snapshots. Revoking later consent does not erase an already created or downloaded release; withdrawal/deletion and remote publication are not implemented. Manage a withdrawal outside this prototype before sharing more copies.
- Redaction of pattern prose, public links, reviewer names, and publication notes requires human review. The software cannot detect a private detail manually copied into a public field. The server's automatic check is against cited evidence visibility and permissions.
- Exports include one selected release per pattern. The exact release snapshots, exporter version, input SHA-256 hashes, and version manifest are retained. Re-exporting the same release selection with this exporter produces identical ZIP bytes. Regenerate through the Publication screen or `server.bundle(store.releases())`; select the original release IDs for an older selection. JSON preserves the public inputs; private histories are intentionally excluded.
- Relationship links resolve when the target is selected too; otherwise they remain stable-ID references to a pattern outside the export. The demo exports all linked patterns together.
- This is a single-user, one-local-tenant prototype. Projects scope evidence and relationship references; the public catalog is a separate snapshot store. The optional iPhone launcher restricts HTTPS Serve access to the Mac owner’s Tailscale login. There is no multi-user role system, hosted tenant isolation, remote publication, storage encryption layer, or general-purpose deployment security. Only use the guarded Tailscale launcher for remote access; do not expose the ordinary local server through a proxy or public interface. Author/reviewer fields remain recorded assertions, not verified editorial identities.
- AI is disabled and there are no API calls, model credentials, prompts, or model outputs to retain. AI extraction, duplicate detection, and suggestions are deferred. If added, they must retain model/version/prompt and source anchors privately and require explicit editorial approval.
- The GAO Green Book is linked as a potential public input for qualified review: https://www.gao.gov/greenbook. No standard text was copied and no edition-specific compliance mapping was validated. Candidate control/evidence fields support discussion, not an assessment. System generation, ontology mapping, and assessment-artifact automation are deferred.

## Verify

```sh
python3 -m unittest discover -s tests -v
node --check static/app.js  # optional syntax check if Node is installed
```

Thirteen standard-library tests verify Tailscale owner/host/origin enforcement, safe launcher configuration detection, and a fresh captured excerpt → candidate → approved revision → release; traceability; revision preservation, persistence and conflict rejection; cross-project references; mandatory claims/review checks; consent/private-evidence rejection; and deterministic exports without the private sentinel. The tests use temporary databases. An additional loopback HTTP integration check is available with `python3 tests/http_access_smoke.py`; it verifies guarded reads, writes, and exports using simulated Serve headers. It does not connect a real tailnet.

An optional browser check needs Playwright and Chromium, only in a development environment:

```sh
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tests/browser_smoke.py
```

Or set `CHROMIUM_PATH` to an installed Chromium binary. The browser test uses a temporary database and port 8877, creates a fresh project/interview, captures evidence, drafts/approves/publishes/exports a pattern, resumes saved notes, checks a mobile viewport, and checks for JavaScript errors. It writes UI screenshots to the project root. The prototype was verified on Linux; native macOS execution has not been tested in this workspace.

## Files and licenses

`iphone.py`: Mac/iPhone Tailscale launcher. `access.py`: local/Serve access policy. `server.py`: localhost HTTP service and deterministic ZIP exporter. `core.py`: SQLite revisions and release policy. `seed.py`: original fictional interview and prompts. `static/`: dependency-free interface. `tests/`: workflow and optional browser verification.

Application code: MIT (see `LICENSE`). Fictional demo interview summaries, pattern text, and example exports: CC0-1.0 (see `DEMO-LICENSE.md`). A real project's reuse rights must be recorded separately; no default demo license is applied to real interview content.
