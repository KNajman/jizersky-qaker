"""Pozadí webu: vrstevnice Jizerských hor (EU-DEM 25 m, opentopodata) + vrcholy (OSM) -> vrstevnice.svg.
Spouští se jen jednou, výsledek se commituje. Potřebuje numpy + matplotlib."""
import json, os, time, urllib.parse, urllib.request
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
S, N, W, E = 50.74, 50.93, 14.98, 15.42   # výřez
NX, NY = 110, 80                          # mřížka (~370 × 260 m)
KROK = 50                                 # vrstevnice po 50 m, každá 200 m zvýrazněná
SIRKA = 1400; VYSKA = round(SIRKA * (N - S) * 111.3 / ((E - W) * 70.2))

def get(url, data=None):
    req = urllib.request.Request(url, data, headers={'User-Agent': 'jizersky-qaker'})
    return json.load(urllib.request.urlopen(req, timeout=120))

def dem():
    if os.path.exists('dem.json'): return json.load(open('dem.json'))
    body = [(S + (N - S) * j / (NY - 1), W + (E - W) * i / (NX - 1)) for j in range(NY) for i in range(NX)]
    v = []
    for k in range(0, len(body), 100):
        loc = '|'.join(f'{a:.5f},{b:.5f}' for a, b in body[k:k + 100])
        v += [r['elevation'] for r in get(f'https://api.opentopodata.org/v1/eudem25m?locations={loc}')['results']]
        time.sleep(1.1)
    g = [v[j * NX:(j + 1) * NX] for j in range(NY)]
    json.dump(g, open('dem.json', 'w'))
    return g

def hladka(g, k=4):
    """Bilineární zjemnění k× a rozmazání 3×3 -> hladké vrstevnice."""
    g = np.array([[v if v is not None else 0 for v in r] for r in g], float)
    y, x = np.linspace(0, NY - 1, (NY - 1) * k + 1), np.linspace(0, NX - 1, (NX - 1) * k + 1)
    g = np.array([np.interp(x, np.arange(NX), r) for r in g])
    g = np.array([np.interp(y, np.arange(NY), c) for c in g.T]).T
    for _ in range(k):
        p = np.pad(g, 1, mode='edge')
        g = sum(p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9
    return g

g = hladka(dem())
lo, hi = g.min(), g.max()
X = np.linspace(0, SIRKA, g.shape[1]); Y = np.linspace(VYSKA, 0, g.shape[0])  # sever nahoře
urovne = list(range(int(lo // KROK + 1) * KROK, int(hi) + 1, KROK))
cs = plt.contour(X, Y, g, levels=urovne)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIRKA} {VYSKA}" fill="none" stroke="#3d5a40" '
       f'stroke-linecap="round" stroke-linejoin="round">']
for h, segs in zip(urovne, cs.allsegs):
    w = '1.4" opacity=".55' if h % 200 == 0 else '.7" opacity=".3'
    d = ''.join('M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in s[::2]) for s in segs if len(s) > 6)
    svg.append(f'<path stroke-width="{w}" d="{d}"/>')

q = f'[out:json];node[natural=peak][name][ele]({S},{W},{N},{E});out;'
vrch = get('https://overpass-api.de/api/interpreter', urllib.parse.urlencode({'data': q}).encode())['elements']
vrch = sorted(vrch, key=lambda e: -float(e['tags']['ele'].split()[0].replace(',', '.')))[:25]
svg.append('<g fill="#3d5a40" stroke="none" font-family="system-ui,sans-serif" font-size="13" opacity=".75">')
hotovo = []  # popisky blíž než 60 × 14 px k vyššímu vrcholu se vynechají
for e in vrch:
    x = (e['lon'] - W) / (E - W) * SIRKA; y = (N - e['lat']) / (N - S) * VYSKA
    if any(abs(x - a) < 60 and abs(y - b) < 14 for a, b in hotovo): continue
    hotovo.append((x, y))
    ele = round(float(e['tags']['ele'].split()[0].replace(',', '.')))
    svg.append(f'<path d="M{x:.0f} {y-5:.0f}l5 8h-10z"/><text x="{x+8:.0f}" y="{y+4:.0f}">'
               f'{e["tags"]["name"]} {ele}</text>')
svg.append('</g></svg>')
open('vrstevnice.svg', 'w', encoding='utf-8').write('\n'.join(svg))
print(f'{lo:.0f}–{hi:.0f} m, {len(vrch)} vrcholů, {os.path.getsize("vrstevnice.svg") // 1024} kB')
