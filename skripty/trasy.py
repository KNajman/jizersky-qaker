"""Pěší vzdálenost a převýšení z Hausmanky ke každému sektoru (informativní, body neovlivňuje).
Trasa: OSRM foot (OpenStreetMap), výšky: EU-DEM 25 m (opentopodata).
Cíl sektoru = objekt nejblíž těžišti sektoru. Hodnoty jsou orientační."""
import json, math, sqlite3, time, urllib.request
START = (50.8638, 15.1046)  # Hausmanka, Oldřichovské sedlo
KROK = 100                  # vzorkování výšek po 100 m
def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'jizersky-qaker'})
    return json.load(urllib.request.urlopen(req, timeout=60))

def km(a, b):
    return math.hypot((a[0]-b[0])*111.32, (a[1]-b[1])*111.32*math.cos(math.radians(a[0])))

def vzorkuj(body):
    """Body trasy (lat,lon) po cca KROK metrech."""
    out, zbyva = [body[0]], 0
    for a, b in zip(body, body[1:]):
        d = km(a, b)*1000; t = KROK - zbyva
        while t < d:
            f = t/d; out.append((a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f)); t += KROK
        zbyva = (zbyva + d) % KROK
    return out + [body[-1]]

def vysky(body):
    v = []
    for i in range(0, len(body), 100):
        loc = '|'.join(f'{a:.5f},{b:.5f}' for a, b in body[i:i+100])
        v += [r['elevation'] for r in get(f'https://api.opentopodata.org/v1/eudem25m?locations={loc}')['results']]
        time.sleep(1.1)
    return v

db = sqlite3.connect('data/jizerky.db')
for col in ('pesky_km REAL', 'stoupani_m INTEGER', 'klesani_m INTEGER', 'cil_lat REAL', 'cil_lon REAL'):
    try: db.execute(f'ALTER TABLE sektor ADD COLUMN {col}')
    except sqlite3.OperationalError: pass  # sloupec už existuje

for sid, nazev in db.execute('SELECT id, nazev FROM sektor').fetchall():
    obj = db.execute('SELECT lat, lon FROM objekt WHERE sektor_id=? AND lat IS NOT NULL', (sid,)).fetchall()
    if not obj: continue  # sektor sloučený do jiného (doplnky.py)
    t = (sum(o[0] for o in obj)/len(obj), sum(o[1] for o in obj)/len(obj))
    ruc = db.execute('SELECT cil_lat, cil_lon FROM sektor WHERE id=?', (sid,)).fetchone()
    cil = ruc if ruc and ruc[0] is not None else min(obj, key=lambda o: km(o, t))  # ručně zadaný cíl má přednost
    r = get(f'https://routing.openstreetmap.de/routed-foot/route/v1/foot/'
            f'{START[1]},{START[0]};{cil[1]},{cil[0]}?overview=full&geometries=geojson')['routes'][0]
    v = vysky(vzorkuj([(b, a) for a, b in r['geometry']['coordinates']]))
    dif = [b - a for a, b in zip(v, v[1:])]
    up, down = round(sum(d for d in dif if d > 0)), round(-sum(d for d in dif if d < 0))
    d = round(r['distance']/1000, 1)
    db.execute('UPDATE sektor SET pesky_km=?, stoupani_m=?, klesani_m=?, cil_lat=?, cil_lon=? WHERE id=?',
               (d, up, down, cil[0], cil[1], sid))
    print(f"{d:5.1f} km  +{up:4d} / -{down:4d} m  {nazev}")
db.commit()
