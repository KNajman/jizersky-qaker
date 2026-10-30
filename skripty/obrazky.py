"""Obrázky ke skalám z galerií ČHS (skála i cesty s ikonou „Fotky“) -> tabulka obrazek + soubory v data/obrazky/<objekt>/.
ČHS u obrázku neříká, jestli jde o fotku, nebo nákres: druh se odhadne (popisek, barevnost) a ručně opraví
(UPDATE obrazek SET druh='nakres' …); ruční druh se nepřepisuje. Z nákresů se pak napůl ručně kreslí vlastní SVG
(objekt.nakres). Skalnioblasti.cz a průvodce: soubory vložit ručně do data/obrazky/<objekt>/ a zapsat se zdrojem."""
import html, os, re, sqlite3, time, urllib.error, urllib.request, concurrent.futures as cf
from PIL import Image
B = 'https://www.horosvaz.cz'

def get(u, pokus=5):  # jako nacti.py: ČHS občas vrací 503
    for i in range(pokus):
        try:
            req = urllib.request.Request(B + u, headers={'User-Agent': 'Mozilla/5.0'})
            return html.unescape(urllib.request.urlopen(req, timeout=30).read().decode())
        except urllib.error.HTTPError as e:
            if e.code != 503 or i == pokus - 1: raise
            time.sleep(2 * (i + 1))

NAKRES = re.compile(r'topo|n[aá]kres|sch[eé]ma|kresb|skic|pl[aá]nek', re.I)
PROTOKOL = re.compile(r'protokol', re.I)
MAPA = re.compile(r'mapk|mapa', re.I)
FOTO = re.compile(r'foto|v[yý]stup|lez|pohled', re.I)

def galerie(s):  # [(url, popis)] z galerie stránky skály/cesty
    return re.findall(r'<a href="(/res/archive/[^"]+)" title="([^"]*)" class="fancybox"', s)

def stranka(oid):
    s = get(f'/skaly-skala-{oid}/')
    out = [(oid, None, u, p) for u, p in galerie(s)]
    for k in s.split('<a href="/skaly-cesta-')[1:]:
        if 'foto_ano' in k.split('</ul>')[0]:
            cid = int(k[:k.index('/')])
            out += [(oid, cid, u, p) for u, p in galerie(get(f'/skaly-cesta-{cid}/'))]
    return out

def odhad(soubor, popis):
    """'protokol' / 'mapa' / 'nakres' / 'foto' podle popisku, jinak podle obrázku: nákres je hlavně bílý a málo barevný."""
    if PROTOKOL.search(popis): return 'protokol'
    if MAPA.search(popis): return 'mapa'
    if NAKRES.search(popis): return 'nakres'
    if FOTO.search(popis): return 'foto'
    im = Image.open(soubor).convert('RGB'); im.thumbnail((200, 200))
    b = im.tobytes(); px = list(zip(b[0::3], b[1::3], b[2::3]))
    bila = sum(min(p) > 225 for p in px) / len(px)
    barva = sum(max(p) - min(p) > 40 for p in px) / len(px)
    return 'nakres' if bila > .45 and barva < .15 else 'foto'

db = sqlite3.connect('data/jizerky.db')
db.executescript(open('data/schema.sql', encoding='utf-8').read())
objekty = [r[0] for r in db.execute('SELECT id FROM objekt WHERE id > 0')]
with cf.ThreadPoolExecutor(4) as ex:
    nalez = [o for r in ex.map(stranka, objekty) for o in r]
cesty = {r[0] for r in db.execute('SELECT id FROM cesta')}
for oid, cid, url, popis in nalez:
    soubor = f'data/obrazky/{oid}/' + url.split('/')[-1].split('?')[0]
    if not os.path.exists(soubor):
        os.makedirs(os.path.dirname(soubor), exist_ok=True)
        req = urllib.request.Request(B + url, headers={'User-Agent': 'Mozilla/5.0'})
        open(soubor, 'wb').write(urllib.request.urlopen(req, timeout=60).read())
    db.execute("INSERT INTO obrazek(url,objekt_id,cesta_id,zdroj,popis,soubor,odhad) VALUES (?,?,?,'čhs',?,?,?) "
               "ON CONFLICT(url) DO UPDATE SET popis=excluded.popis, odhad=excluded.odhad",
               (B + url, oid, cid if cid in cesty else None, popis, soubor, odhad(soubor, popis)))
db.commit()
print(len(nalez), 'obrázků u', len({n[0] for n in nalez}), 'objektů;',
      db.execute("SELECT odhad, count(*) FROM obrazek GROUP BY odhad").fetchall())
