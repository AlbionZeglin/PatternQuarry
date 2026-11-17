# Start on your Mac M1

1. Install Python 3.10+ from https://www.python.org/downloads/macos/ (universal2 installer).
2. In Terminal:
   ```sh
   git clone https://github.com/AlbionZeglin/PatternQuarry.git
   cd PatternQuarry
   python3 server.py
   ```
3. Open http://localhost:8765. Control-C stops it; rerun the command to resume saved work.

No packages, API keys, or cloud account needed.

If you downloaded the repository ZIP instead, extract it and run `python3 server.py` from the extracted folder.

**See the example:** Interview → select a public excerpt → Draft from selection → fill and anchor the claim fields → Approve new revision → Review for publication → Publication → Download ZIP. The three complete seeded patterns can already be explored and exported. `examples/language/` contains a ready-made public sample.

**Try a real interview:** New project → objective/scope/consent → New session → record note-taking consent → ask for one real incident → save notes → capture private excerpts. Keep questions and competing accounts open; use Prompt feedback to record what should change. Only create a public summary with explicit permission.

For your **iPhone**, connect Tailscale on both devices with the same login and run `python3 iphone.py` on the Mac. Open its printed HTTPS URL in Safari. See [IPHONE.md](IPHONE.md).

This is a **single-user prototype**. The backend stays on localhost; the optional iPhone launcher adds owner-only Tailscale Serve access. The SQLite database is unencrypted; protect your Mac and backups. Saving is explicit. Publication review creates an immutable snapshot and cannot recall downloaded copies.

See [README.md](README.md) for the full walkthrough, limitations, backups, and tests. No native Mac run was available during development; automated backend and Chromium workflow tests passed on Linux.
