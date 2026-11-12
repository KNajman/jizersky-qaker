"""Hrubé SVG z nákresu věže (tabulka obrazek, druh 'nakres', objekt.druh 'věž'): jen obrys skály v barvě smrku.
Cesty (červené čáry) a text (malé souvislé útvary: písmena, čísla, šipky) se vynechají; cesty se kreslí z databáze.
Výsledek je podklad k ručnímu dočištění v Inkscapu (vrstva skála, originál jako skrytá vrstva pro obtažení).
Spuštění z kořene: python3 skripty/nakresy.py (všechny věže, existující nepřepíše)
 nebo python3 skripty/nakresy.py <id_objektu> [<id_obrazku>] (přepíše) -> obrazky/nakresy/<id_objektu>.svg"""
import base64, os, sqlite3, sys
import cv2, numpy as np
from PIL import Image
from skimage.morphology import skeletonize
TEXT = .08  # útvar menší než 8 % delší strany obrázku = text nebo značka

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
    skala = cv2.subtract(cary, cv2.dilate(cervena, np.ones((5, 5), np.uint8)))
    n, popisky, st, _ = cv2.connectedComponentsWithStats(skala, connectivity=8)
    velke = [i for i in range(1, n) if max(st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]) >= TEXT * max(w, h)]
    skala = np.isin(popisky, velke).astype(np.uint8) * 255
    b64 = base64.b64encode(open(soubor, 'rb').read()).decode()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
            f'viewBox="0 0 {w} {h}">\n'
            f'<g inkscape:groupmode="layer" inkscape:label="originál" style="display:none">'
            f'<image href="data:{Image.MIME[obr.format]};base64,{b64}" width="{w}" height="{h}"/></g>\n'
            f'<g inkscape:groupmode="layer" inkscape:label="skála">{vrstva(skala, "#23392c", 2)}</g>\n</svg>\n')

db = sqlite3.connect('data/jizerky.db')
os.makedirs('obrazky/nakresy', exist_ok=True)
if len(sys.argv) > 1:  # jeden objekt (přepíše), případně konkrétní obrázek
    q = 'SELECT objekt_id, soubor FROM obrazek WHERE objekt_id=? AND druh=\'nakres\'' + (' AND id=?' if len(sys.argv) > 2 else '') + ' ORDER BY id'
    prace = [db.execute(q, tuple(map(int, sys.argv[1:3]))).fetchone()]
else:  # všechny věže s nákresem, přednostně půdorys, jinak první; existující SVG (ruční úpravy) se nepřepisují
    prace = {}
    for oid, soubor in db.execute("SELECT b.objekt_id, b.soubor FROM obrazek b JOIN objekt o ON o.id = b.objekt_id "
                                  "WHERE b.druh='nakres' AND o.druh='věž' ORDER BY b.pohled IS NOT 'pudorys', b.id"):
        prace.setdefault(oid, soubor)
    prace = [(o, s) for o, s in prace.items() if not os.path.exists(f'obrazky/nakresy/{o}.svg')]
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
