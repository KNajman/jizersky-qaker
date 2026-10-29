"""Podsektory podle terénu (EU-DEM 25 m): dva objekty do DOSAH km patří k sobě, pokud terén mezi nimi
neklesne o víc než UDOLI m pod nižší z nich – hranice podsektorů tak vedou údolími. Skupiny menší než
MIN objektů se připojí k nejbližší skupině. Název = nejbližší volný pojmenovaný vrchol z OSM. Podsektory s vrcholem NULL
(celý sektor ČHS, doplnky.py) se nemění. Potřebuje numpy; výšky se cachují v dem_cache.json."""
import json, math, os, sqlite3, time, urllib.error, urllib.parse, urllib.request
import numpy as np
DOSAH, UDOLI, MIN = 0.3, 6, 4  # km, m, objektů
KROK = 0.0005       # ° zeměpisné šířky (~55 m), délka se škáluje cos(šířky)
OKRAJ = 0.004       # ° kolem objektů sektoru
BEZ = {40}          # Odlehlé skály – rozeseté po celých horách, bez podsektorů
CACHE = 'data/dem_cache.json'
# ruční názvy (dle pořadatele): (sektor, automatický název) -> název; stejný název = sloučení skupin
JMENA = {(39, 'Stojka'): 'Zahradní stěna', (39, 'u Rakev'): 'Svinské čelo',
         (39, 'u Vajíčko'): 'Ptačí kupy', (39, 'Ořešník'): 'Velký Štolpich', (39, 'Holubník'): 'Malý Štolpich',
         (41, 'Skála'): 'Paličník', (45, 'Kočičí kameny'): 'Francouzské kameny',
         (42, 'Šolcova stěna'): 'Šolcovy kameny', (42, 'Stojka'): 'Hlídači',
         (621, 'Brdo'): 'Milíř', (43, 'Kopřivník'): 'Koňská hlava'}
ROZDEL = {(44, 'Dolní Lysá skála'): ['Stržový vrch', 'Kopřivník'],  # automatický název závisí na objektech
          (44, 'Stržový vrch'): ['Stržový vrch', 'Kopřivník']}  # skupina -> objekty k nejbližšímu z vrcholů OSM
PRESUN = {17959: 'Dračí vrch'}  # Atlas draků; objekt -> podsektor téhož sektoru

def get(url, data=None, pokus=8):
    for i in range(pokus):
        try:
            req = urllib.request.Request(url, data, headers={'User-Agent': 'jizersky-qaker'})
            return json.load(urllib.request.urlopen(req, timeout=120))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if i == pokus - 1: raise
            time.sleep(10 * (i + 1))

cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def vysky(body):
    chybi = [b for b in body if f'{b[0]:.5f},{b[1]:.5f}' not in cache]
    for k in range(0, len(chybi), 100):
        loc = '|'.join(f'{a:.5f},{b:.5f}' for a, b in chybi[k:k + 100])
        for b, r in zip(chybi[k:k + 100], get(f'https://api.opentopodata.org/v1/eudem25m?locations={loc}')['results']):
            cache[f'{b[0]:.5f},{b[1]:.5f}'] = r['elevation'] or 0
        json.dump(cache, open(CACHE, 'w')); time.sleep(1.1)
    return [cache[f'{a:.5f},{b:.5f}'] for a, b in body]

def km(a, b):
    return math.hypot((a[0] - b[0]) * 111.3, (a[1] - b[1]) * 70.2)

def skupiny(obj, h):
    """Union-find přes dvojice objektů nespojené údolím; h(lat, lon) = výška terénu."""
    rodic = list(range(len(obj)))
    def koren(i):
        while rodic[i] != i: rodic[i] = rodic[rodic[i]]; i = rodic[i]
        return i
    for i, a in enumerate(obj):
        for j in range(i):
            b = obj[j]; d = km(a[1:], b[1:])
            if d > DOSAH: continue
            t = np.linspace(0, 1, max(2, int(d * 40)))  # vzorek po ~25 m
            cara = [h(a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f) for f in t]
            if min(cara[0], cara[-1]) - min(cara) < UDOLI: rodic[koren(i)] = koren(j)
    g = {}
    for i in range(len(obj)): g.setdefault(koren(i), []).append(i)
    g = sorted(g.values(), key=len, reverse=True)
    velke = [x for x in g if len(x) >= MIN] or g[:1]
    for x in g:  # malé skupiny k nejbližší velké
        if x in velke: continue
        min(velke, key=lambda v: min(km(obj[i][1:], obj[j][1:]) for i in x for j in v)).extend(x)
    return velke

if 'vrcholy' not in cache:  # pojmenované vrcholy OSM pro celé hory, jednou
    q = '[out:json];node[natural=peak][name](50.70,14.95,51.00,15.45);out;'
    cache['vrcholy'] = get('https://overpass-api.de/api/interpreter', urllib.parse.urlencode({'data': q}).encode())['elements']
    json.dump(cache, open(CACHE, 'w'))
osm = cache['vrcholy']

db = sqlite3.connect('data/jizerky.db')
db.execute('PRAGMA foreign_keys = ON')
db.execute('UPDATE objekt SET podsektor_id = NULL WHERE podsektor_id IN '
           '(SELECT id FROM podsektor WHERE vrchol_lat IS NOT NULL)')
db.execute('DELETE FROM podsektor WHERE vrchol_lat IS NOT NULL')
for sid, sn in db.execute('SELECT id, nazev FROM sektor').fetchall():
    if sid in BEZ: continue
    obj = db.execute('SELECT id, lat, lon, nazev FROM objekt WHERE sektor_id=? AND lat IS NOT NULL '
                     'AND podsektor_id IS NULL', (sid,)).fetchall()
    if len(obj) < 2: continue
    lat = np.array([o[1] for o in obj]); lon = np.array([o[2] for o in obj])
    med = np.median(lat), np.median(lon)  # odlehlé objekty (>3 km) by zbytečně zvětšily mřížku
    blizko = [math.hypot((a - med[0]) * 111, (b - med[1]) * 70) < 3 for a, b in zip(lat, lon)]
    S, N = lat[blizko].min() - OKRAJ, lat[blizko].max() + OKRAJ
    kl = KROK / math.cos(math.radians(med[0]))
    W, E = lon[blizko].min() - OKRAJ / .63, lon[blizko].max() + OKRAJ / .63
    ys, xs = np.arange(S, N + KROK, KROK), np.arange(W, E + kl, kl)
    z = np.array(vysky([(a, b) for a in ys for b in xs]), float).reshape(len(ys), len(xs))
    def h(a, b):  # bilineární výška z mřížky
        y = min(max((a - S) / KROK, 0), len(ys) - 1.001); x = min(max((b - W) / kl, 0), len(xs) - 1.001)
        y0, x0 = int(y), int(x); fy, fx = y - y0, x - x0
        return (z[y0, x0] * (1 - fy) * (1 - fx) + z[y0, x0 + 1] * (1 - fy) * fx
                + z[y0 + 1, x0] * fy * (1 - fx) + z[y0 + 1, x0 + 1] * fy * fx)
    sk = skupiny(obj, h)
    if len(sk) < 2: print(f'{sn}: jedna skupina, bez podsektorů'); continue
    volne = list(osm)
    for x in sk:
        a, b = float(np.mean([obj[i][1] for i in x])), float(np.mean([obj[i][2] for i in x]))
        p = min(volne, key=lambda e: km((e['lat'], e['lon']), (a, b)), default=None)
        if p and km((p['lat'], p['lon']), (a, b)) < 1.5: n = p['tags']['name']; volne.remove(p)
        else: n = 'u ' + max((obj[i] for i in x), key=lambda o: h(o[1], o[2]))[3]
        n = JMENA.get((sid, n), n)
        vr = [e for e in osm if e['tags']['name'] in ROZDEL.get((sid, n), ())]
        casti = [(e['tags']['name'], e['lat'], e['lon'], [i for i in x if min(
                  vr, key=lambda v: km((v['lat'], v['lon']), obj[i][1:3])) is e]) for e in vr] or [(n, a, b, x)]
        for n, a, b, y in casti:
            pid = (db.execute('SELECT id FROM podsektor WHERE sektor_id=? AND nazev=?', (sid, n)).fetchone() or
                   [db.execute('INSERT INTO podsektor(sektor_id,nazev,vrchol_lat,vrchol_lon,vyska) VALUES (?,?,?,?,?)',
                               (sid, n, a, b, round(h(a, b)))).lastrowid])[0]
            db.executemany('UPDATE objekt SET podsektor_id=? WHERE id=?', [(pid, obj[i][0]) for i in y])
            print(f'{sn:28} {n:30} {len(y):3} obj.')
for oid, n in PRESUN.items():
    db.execute('UPDATE objekt SET podsektor_id = (SELECT p.id FROM podsektor p JOIN objekt o ON o.sektor_id = p.sektor_id '
               'WHERE o.id = ? AND p.nazev = ?) WHERE id = ?', (oid, n, oid))
db.commit()
