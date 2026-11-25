"""Render the two hero arrows. Usage: python hero.py  (writes out/heroL.png, out/heroR.png at 1600x1600)."""
import subprocess, sys, time
from playwright.sync_api import sync_playwright
P = {
  'heroL': 'head=70&tail=318&t=.24&hw=2.1&hl=30&rx=-40&ry=46&rz=20&dist=6.0',
  'heroR': 'head=32&tail=322&t=.24&hw=2.1&hl=30&rx=22&ry=-28&rz=0&dist=6.2',
}
if len(sys.argv) > 2: P = {sys.argv[1]: sys.argv[2]}
srv = subprocess.Popen(['python', '-m', 'http.server', '8765', '-d', 'www'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
  with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    for name, qs in P.items():
      pg = b.new_page(viewport={'width': 1600, 'height': 1600})
      pg.goto(f'http://127.0.0.1:8765/index.html?w={name}&W=1600&H=1600&crisp=1&{qs}')
      pg.wait_for_function('window.__done===true', timeout=180000)
      pg.locator('canvas').screenshot(path=f'out/{name}.png', omit_background=True); print(name, 'ok')
    b.close()
finally: srv.terminate()
