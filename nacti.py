"""Stáhne oblast Jizerské hory z databáze ČHS do jizerky.db (opakovatelně)."""
import urllib.error, re, html, sqlite3, urllib.request, concurrent.futures as cf
B = "https://www.horosvaz.cz"
OBLAST = "/skaly-oblast-43/"
RIM = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI']

def get(u, pokus=5):
    import time
    for i in range(pokus):
        try: return _get(u)
        except urllib.error.HTTPError as e:
            if e.code != 503 or i == pokus - 1: raise
            time.sleep(2 * (i + 1))

def _get(u):
    req = urllib.request.Request(B + u, headers={'User-Agent': 'Mozilla/5.0'})
    return html.unescape(urllib.request.urlopen(req, timeout=30).read().decode())

def stupen(z):
    """'RP VIc, 6m' -> 'VIc'; arabské 7 -> 'VII'; 'Přeskok 2' -> 'P2'; led -> None."""
    p = re.match(r'P[řr]eskok\s*(\d)', z)
    if p: return 'P' + p.group(1)          # 'Přeskok 1+' -> P1
    z = re.sub(r'^(RP|AF|PP|OS)\s+', '', z.replace('\xa0', ' ').strip())
    m = re.match(r'(XI|X|IX|VIII|VII|VI|V|IV|III|II|I)(?![IVX])([abc]?)', z)
    if m: return m.group(1) + m.group(2)
    m = re.match(r'(\d{1,2})(?!\d)', z)
    if m and 1 <= int(m.group(1)) <= 11 and not z.startswith(('WI', 'M')):
        return RIM[int(m.group(1)) - 1]
    return None

def typ(n):
    n = n.lower()
    return 'lom' if re.search(r'\blom\b|lom ', n) else 'boulder' if 'boulder' in n else 'skála'

def objekt(oid):
    s = get(f"/skaly-skala-{oid}/")
    m = re.search(r'mapy\.cz/turisticka\?y=([\d.]+)&x=([\d.]+)', s)
    cesty = re.findall(r'href="/skaly-cesta-(\d+)/" title="([^"]*)">[^<]*</a>'
                       r'<span class="info-roads">,\s*([^<]*)</span>', s)
    return oid, (float(m[1]), float(m[2])) if m else (None, None), cesty

db = sqlite3.connect("jizerky.db")
try: db.execute('ALTER TABLE objekt ADD COLUMN masiv INTEGER NOT NULL DEFAULT 0')
except sqlite3.OperationalError: pass  # sloupec už existuje
db.executescript(open("schema.sql").read())
# klasifikace: I–VI = 1–6, od VI každé písmeno +1 bod
# (VI 6, VIb 7, VIc 8, VII/VIIa 9, VIIb 10, VIIc 11, VIII/VIIIa 12 …)
# přeskok N = 2N bodů; led se nehodnotí (stupen NULL)
db.execute("DELETE FROM klasifikace WHERE stupen NOT IN (SELECT stupen FROM cesta WHERE stupen IS NOT NULL)")
b = 0
for r in RIM:
    for p in (['', 'b', 'c'] if r == 'VI' else [''] if RIM.index(r) < 5 else ['', 'a', 'b', 'c']):
        if p != 'a': b += 1
        db.execute("INSERT OR REPLACE INTO klasifikace VALUES (?,?,?)", (r + p, b * 10 + (p == 'a'), b))
for n in (1, 2, 3, 4, 5):
    db.execute("INSERT OR REPLACE INTO klasifikace VALUES (?,?,?)", (f"P{n}", 2 * n * 10 + 5, 2 * n))
sektory = re.findall(r'href="https://www\.horosvaz\.cz/skaly-sektor-(\d+)/" title="([^"]*)"\), ', get(OBLAST)) \
       or re.findall(r'<a href="/skaly-sektor-(\d+)/" title="([^"]*)"', get(OBLAST))
sektory = list(dict.fromkeys(sektory))
objekty, masivy = [], set()
for sid, nazev in sektory:
    db.execute("INSERT INTO sektor(id,nazev) VALUES (?,?) "
               "ON CONFLICT(id) DO UPDATE SET nazev=excluded.nazev",  # body plní trasy.py
               (int(sid), nazev))
    for oid, on in dict.fromkeys(re.findall(r'skaly-skala-(\d+)/" title="([^"]*)"', get(f"/skaly-sektor-{sid}/"))):
        if on.endswith(' - M'): masivy.add(int(oid))  # výpis s počty cest uvádí masivy s „- M“
        else: objekty.append((int(oid), int(sid), on))
objekty = list({o[0]: o for o in objekty}.values())

with cf.ThreadPoolExecutor(4) as ex:
    detail = {oid: (gps, c) for oid, gps, c in ex.map(objekt, [o[0] for o in objekty])}

for oid, sid, on in objekty:
    (lat, lon), cesty = detail[oid]
    db.execute("INSERT INTO objekt(id,sektor_id,nazev,typ,lat,lon) VALUES (?,?,?,?,?,?) "
               "ON CONFLICT(id) DO UPDATE SET sektor_id=excluded.sektor_id, nazev=excluded.nazev, "
               "lat=excluded.lat, lon=excluded.lon",  # typ se po ruční opravě nepřepisuje
               (oid, sid, on, typ(on), lat, lon))
    for cid, cn, z in cesty:
        z = z.replace('\xa0', ' ').strip()
        db.execute("INSERT OR REPLACE INTO cesta VALUES (?,?,?,?,?)", (int(cid), oid, cn, z, stupen(z)))
db.execute("UPDATE objekt SET masiv = (id IN (%s))" % ",".join(map(str, masivy or [0])))
db.commit()
print(db.execute("SELECT (SELECT count(*) FROM sektor),(SELECT count(*) FROM objekt),"
                 "(SELECT count(*) FROM cesta),(SELECT count(*) FROM cesta WHERE stupen IS NULL)").fetchone(),
      "= sektory, objekty, cesty, cesty bez převedené klasifikace")
