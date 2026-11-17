"""Optional UI check. Requires Playwright + Chromium; not needed to run the app."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temp:
    port='8877'
    server=subprocess.Popen([sys.executable,str(ROOT/'server.py'),'--port',port,'--data',temp+'/studio.sqlite3'],stdout=subprocess.PIPE)
    try:
        with sync_playwright() as p:
            executable=os.environ.get('CHROMIUM_PATH')
            browser=p.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}))
            page=browser.new_page(viewport={'width':1440,'height':1100})
            errors=[]
            page.on('pageerror', lambda e: errors.append(str(e)))
            for _ in range(30):
                try:
                    page.goto('http://localhost:'+port)
                    break
                except Exception:
                    time.sleep(.1)
            page.get_by_role('heading',name='Every pattern begins with an incident.').wait_for()
            page.screenshot(path=str(ROOT/'screenshot.png'),full_page=True)
            # Demonstration catalog and pinned evidence.
            page.locator('[data-nav="catalog"]').click()
            page.get_by_role('button',name='A named decision lane',exact=False).click()
            page.get_by_role('heading',name='The candidate pattern').wait_for()
            page.locator('[data-exact]').first.click()
            page.get_by_role('heading',name='Evidence · revision 1').wait_for()
            page.locator('#close-dialog').click()
            page.screenshot(path=str(ROOT/'workbench.png'),full_page=True)
            # New project and real-interview workflow, using fictional input.
            page.locator('#new-project').click()
            page.locator('#modal [name="name"]').fill('Browser test project')
            page.locator('#modal [name="objective"]').fill('Practice the reusable interview workflow')
            page.get_by_role('button',name='Create project',exact=True).click()
            page.get_by_label('Project permits explicitly reviewed public releases').check()
            page.get_by_role('button',name='Save new revision',exact=True).click()
            page.locator('[data-nav="interview"]').click()
            page.get_by_role('button',name='New session',exact=False).click()
            page.locator('#modal [name="name"]').fill('A test interview')
            page.locator('#modal [name="expert"]').fill('Fictional expert')
            page.get_by_label('Expert consents to capture and retain notes').check()
            page.get_by_role('button',name='Create session',exact=True).click()
            page.locator('#notes').fill('We lost time at a handoff, then used an acknowledgement.')
            page.get_by_text('Consent, visibility & reuse',exact=True).click()
            page.get_by_label('Expert explicitly consents to reviewed public excerpts').check()
            page.get_by_role('button',name='Save new revision',exact=True).click()
            page.get_by_role('button',name='Next question',exact=False).click()
            page.get_by_text('PROMPT 2 / 10',exact=True).wait_for()
            page.get_by_role('button',name='Capture excerpt',exact=False).click()
            page.locator('#modal [name="text"]').fill('An original fictional public incident about a missed handoff and an acknowledgement.')
            page.locator('#modal [name="source"]').fill('Fictional test interview')
            page.locator('#modal [name="anchor"]').fill('00:01–00:02')
            page.locator('#modal [name="visibility"]').select_option('public')
            page.locator('#modal [name="license"]').fill('CC0-1.0')
            page.get_by_label('Consent covers public reuse of this exact text').check()
            page.get_by_role('button',name='Save excerpt',exact=True).click()
            page.locator('[data-evidence]').first.check()
            page.get_by_role('button',name='Draft from selection',exact=False).click()
            page.locator('#modal [name="name"]').fill('A tested handoff')
            page.get_by_role('button',name='Create candidate',exact=True).click()
            for field in ['context','problem','forces','solution','resulting_context','benefits','costs','instances','exceptions','boundaries','controls']:
                page.locator('#pattern-form [name="'+field+'"]').fill('Fictional example; reviewed evidence. '+field)
            page.locator('#pattern-form [name="license"]').fill('CC0-1.0')
            page.get_by_role('button',name='Approve new revision',exact=True).click()
            page.locator('#publish-pattern').click()
            for cb in page.locator('#publish-form input[type=checkbox]').all():
                cb.check()
            page.locator('#modal [name="_note"]').fill('Reviewed original fictional text, consent and terms.')
            page.get_by_role('button',name='Create public release',exact=True).click()
            page.get_by_role('heading',name='Public catalog',exact=True).wait_for()
            with page.expect_download() as download:
                page.get_by_role('button',name='Download publication ZIP',exact=False).click()
            path=download.value.path()
            with zipfile.ZipFile(path) as z:
                assert any(n.endswith('.md') and n!='README.md' for n in z.namelist())
                assert 'manifest.json' in z.namelist()
            page.locator('[data-nav="interview"]').click()
            page.get_by_role('heading',name='Working interview',exact=True).wait_for()
            assert page.locator('#notes').input_value().startswith('We lost time')
            page.set_viewport_size({'width':390,'height':844})
            page.screenshot(path=str(ROOT/'mobile.png'),full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile overflow'
            assert not errors, errors
            print('PASS: browser capture → draft → approve → publish → ZIP; saved interview resumes; mobile layout; no JS errors')
            browser.close()
    finally:
        server.terminate()
        server.wait()
