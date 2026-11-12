"""Hrubé SVG z nákresu (tabulka obrazek, druh 'nakres'): čáry obrázku -> křivky v barvách Jizerek, cesty (červená) zvlášť.
Výsledek je podklad k ručnímu dočištění v Inkscapu (vrstvy skála / cesty, originál jako skrytá vrstva pro obtažení).
Spuštění z kořene: python3 skripty/nakresy.py (všechny, existující nepřepíše)
 nebo python3 skripty/nakresy.py <id_objektu> [<id_obrazku>] (přepíše) -> obrazky/nakresy/<id_objektu>.svg"""
import base64, os, sqlite3, sys
import cv2, numpy as np
from PIL import Image
from skimage.morphology import skeletonize

def vrstva(maska, barva, sirka):
    """Maska čar -> kostra -> lomené čáry (cv2 obrysy kostry, zjednodušené)."""
    maska = cv2.morphologyEx(maska, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    kostra = skeletonize(maska > 0).astype(np.uint8) * 255
    obrysy, _ = cv2.findContours(kostra, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    d = []
    for o in obrysy:
        if cv2.arcLength(o, False) < 25: continue  # šum
        o = cv2.approxPolyDP(o, 1.5, False)[:, 0]
        d.append('M' + ' '.join(f'{x},{y}' for x, y in o))
    return (f'<path d="{" ".join(d)}" fill="none" stroke="{barva}" stroke-width="{sirka}" '
            'stroke-linecap="round" stroke-linejoin="round"/>')

def svg(soubor):
    obr = Image.open(soubor)  # i GIF/PNG, které cv2 nenačte
    im = cv2.cvtColor(np.array(obr.convert('RGB')), cv2.COLOR_RGB2BGR); h, w = im.shape[:2]
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    cervena = (((hsv[..., 0] < 10) | (hsv[..., 0] > 165)) & (hsv[..., 1] > 90) & (hsv[..., 2] > 80)).astype(np.uint8) * 255
    seda = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    cary = cv2.adaptiveThreshold(seda, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 12)
    skala = cv2.subtract(cary, cv2.dilate(cervena, np.ones((3, 3), np.uint8)))
    b64 = base64.b64encode(open(soubor, 'rb').read()).decode()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
            f'viewBox="0 0 {w} {h}">\n'
            f'<g inkscape:groupmode="layer" inkscape:label="originál" style="display:none">'
            f'<image href="data:{Image.MIME[obr.format]};base64,{b64}" width="{w}" height="{h}"/></g>\n'
            f'<g inkscape:groupmode="layer" inkscape:label="skála">{vrstva(skala, "#23392c", 2)}</g>\n'
            f'<g inkscape:groupmode="layer" inkscape:label="cesty">{vrstva(cervena, "#c0392b", 3)}</g>\n</svg>\n')

db = sqlite3.connect('data/jizerky.db')
os.makedirs('obrazky/nakresy', exist_ok=True)
if len(sys.argv) > 1:  # jeden objekt (přepíše), případně konkrétní obrázek
    q = 'SELECT objekt_id, soubor FROM obrazek WHERE objekt_id=? AND druh=\'nakres\'' + (' AND id=?' if len(sys.argv) > 2 else '') + ' ORDER BY id'
    prace = [db.execute(q, tuple(map(int, sys.argv[1:3]))).fetchone()]
else:  # všechny objekty s nákresem, první nákres; existující SVG (ruční úpravy) se nepřepisují
    prace = [r for r in db.execute("SELECT objekt_id, soubor FROM obrazek WHERE druh='nakres' AND id IN "
                                   "(SELECT min(id) FROM obrazek WHERE druh='nakres' GROUP BY objekt_id)")
             if not os.path.exists(f'obrazky/nakresy/{r[0]}.svg')]
for oid, soubor in prace:
    cil = f'obrazky/nakresy/{oid}.svg'
    open(cil, 'w', encoding='utf-8').write(svg(soubor))
    print(soubor, '->', cil)
# objekt.nakres = cesta k SVG pro web (u všech existujících souborů)
db.execute('UPDATE objekt SET nakres=NULL')
for f in os.listdir('obrazky/nakresy'):
    db.execute('UPDATE objekt SET nakres=? WHERE id=?', ('obrazky/nakresy/' + f, int(f[:-4])))
db.commit()
print(len(prace), 'SVG')
