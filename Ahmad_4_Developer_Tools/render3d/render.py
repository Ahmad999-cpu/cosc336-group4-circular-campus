import sys, subprocess, time
from playwright.sync_api import sync_playwright
jobs = [('logoA',1200,1200),('logoB',1200,1200),('ribbon',2600,1000)]
if len(sys.argv)>1: jobs=[j for j in jobs if j[0] in sys.argv[1:]]
srv = subprocess.Popen(['python','-m','http.server','8765','-d','www'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    for w,W,H in jobs:
        pg = b.new_page(viewport={'width':W,'height':H})
        msgs=[]; pg.on('console', lambda m: msgs.append(m.text)); pg.on('pageerror', lambda e: msgs.append(str(e)))
        pg.goto(f'http://127.0.0.1:8765/index.html?w={w}&W={W}&H={H}')
        pg.wait_for_function('window.__done===true', timeout=120000)
        pg.locator('canvas').screenshot(path=f'out/{w}.png', omit_background=True)
        print(w, 'ok', msgs[:3])
    b.close()
finally: srv.terminate()
