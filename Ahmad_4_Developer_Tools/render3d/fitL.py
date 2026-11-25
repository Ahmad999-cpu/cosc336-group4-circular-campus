import subprocess, sys, time, itertools
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
# reference mask: left arrow only
a=np.asarray(Image.open('/mnt/user-data/uploads/3ef61820-image.png').convert('RGB')).astype(int)
r,g,b=a[...,0],a[...,1],a[...,2]; ref=(r>170)&(r-g>70)&(r-b>60)
ref[:420,:]=False; ref[:,330:]=False; ref[585:668,190:]=False
REF=ref[:841,:330]
def score(alpha, W, L, T):
    im=Image.fromarray((alpha*255).astype(np.uint8)).resize((W, int(W*alpha.shape[0]/alpha.shape[1])))
    m=np.asarray(im)>120; canvas=np.zeros((841+2000,330+2000),bool)
    canvas[1000+T:1000+T+m.shape[0], 1000+L:1000+L+m.shape[1]] |= m
    c=canvas[1000:1000+841,1000:1000+330].copy(); c[:420,:]=False; c[585:668,190:]=False
    inter=(c&REF).sum(); uni=(c|REF).sum(); return inter/uni
combos=[(ry,rz,rx) for ry in (38,46) for rz in (12,20) for rx in (-40,-50)]
srv=subprocess.Popen(['python','-m','http.server','8765','-d','www'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
best=(0,None)
try:
  with sync_playwright() as p:
    bw=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    for ry,rz,rx in combos:
        qs=f'head=70&tail=318&t=.24&hw=2.1&hl=30&rx={rx}&ry={ry}&rz={rz}&dist=6.0'
        pg=bw.new_page(viewport={'width':800,'height':800})
        pg.goto(f'http://127.0.0.1:8765/index.html?w=heroL&W=800&H=800&crisp=1&{qs}'); pg.wait_for_function('window.__done===true',timeout=180000)
        pg.locator('canvas').screenshot(path='/tmp/fit.png',omit_background=True); pg.close()
        im=Image.open('/tmp/fit.png'); im=im.crop(im.getbbox()); al=np.asarray(im)[...,3]/255.
        loc=(0,None)
        for W in range(200,380,15):
            for L in range(-200,40,12):
                for T in range(330,520,15):
                    s=score(al,W,L,T)
                    if s>loc[0]: loc=(s,(W,L,T))
        print(ry,rz,rx,'IoU',round(loc[0],3),loc[1], flush=True)
        if loc[0]>best[0]: best=(loc[0],(qs,)+loc[1])
    bw.close()
finally: srv.terminate()
print('BEST',best)
