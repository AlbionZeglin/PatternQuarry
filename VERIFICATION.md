# Verification record

Verified on 2026-11-17 in the Linux development workspace, with Python 3.12 and Chromium. No native macOS run was available.

- `python3 -m unittest discover -s tests -v`: **13 passed**.
- `node --check static/app.js`: **passed**.
- `CHROMIUM_PATH=/usr/bin/chromium python3 tests/browser_smoke.py`: **passed** with guarded Tailscale mode added; original local workflow still passes.

- `python3 tests/http_access_smoke.py`: **passed** for guarded HTTP reads/writes/exports and original local mode.
- Python compilation, launcher shell syntax, and CLI missing-Tailscale guidance: **passed**.

The browser check used an isolated temporary database and exercised a new project, project publication permission, a new consented session, saved notes and guide position, a public excerpt, a candidate with exact evidence anchors, approval, the four publication checks, a downloaded ZIP, and resumed notes. It inspected pinned source evidence in the demo, checked a 390-pixel mobile viewport, and observed no JavaScript errors.

Backend assertions verify that prior revisions remain intact after editing, reopening the database resumes saved state, stale writes are rejected, cross-project references are rejected, every claim resolves to its cited evidence revision, private evidence and missing consent block promotion, and repeated exports of the same releases are byte-identical. The seeded private sentinel is absent from every exported file. The three demo Markdown relationship links point to included files.

These checks establish prototype behavior, not production security, standard conformance, or the effectiveness of the fictional patterns. Public redaction and evidence sufficiency remain editorial decisions.

Tailscale-specific tests reject wrong/missing identity (including a rewritten localhost Host), unknown hosts, duplicated identity/Host headers, non-HTTPS forwarding, Funnel requests, and cross-origin writes. They verify exact owner status detection, RFC2047 identity decoding, and collision detection in background/foreground Serve configurations. HTTP checks simulate Serve headers over a temporary loopback listener. Official Serve/CLI documentation and current proxy source were consulted for identity headers and foreground behavior. No real tailnet, Mac, or iPhone was connected from this workspace.

The Pattern Quarry rename was verified on 2026-11-17: all 13 unit tests, guarded HTTP integration, Python/JavaScript/shell syntax checks, and the Chromium interview-to-export workflow passed from the renamed source directory. Repository source and demo exports contain no previous application branding or personal device hostname. The database keeps its earlier filename for compatibility and is excluded from the repository.
