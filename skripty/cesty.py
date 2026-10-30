"""Zvýrazněné pěší cesty z OpenStreetMap (Overpass) -> cesty.json pro web. Spouštět jednorázově, když se změní seznam."""
import json, urllib.parse, urllib.request
CESTY = ['Viničná cesta', 'Čínská cesta', 'Štolpišská silnice', 'Pavlova cesta', 'Paličníková cesta', 'Kozí stezka',
         'Nová poutní cesta', 'Francouzká cesta']
NAZEV = {'Francouzká cesta': 'Francouzská cesta'}  # překlep v OSM
SPOJKY = {  # cesty bez jména v OSM: body z mapy.com, geometrie pěšky z OSRM
    'Spojka Fojtecká cesta – Klobouky': [(50.8124778, 15.0965211), (50.8400286, 15.1129603)],  # mapy.com/s/gozasoveba
}
q = '[out:json][timeout:60];way["highway"]["name"~"^(%s)$"](50.70,14.95,50.95,15.40);out geom;' % '|'.join(CESTY)
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode(),
                             headers={'User-Agent': 'jizersky-qaker'})
d = json.load(urllib.request.urlopen(req, timeout=90))
out = {NAZEV.get(n, n): [[[round(p['lat'], 5), round(p['lon'], 5)] for p in w['geometry']] for w in d['elements'] if w['tags']['name'] == n]
       for n in CESTY}
for n, body in SPOJKY.items():
    u = 'https://routing.openstreetmap.de/routed-foot/route/v1/foot/' + ';'.join(f'{lon},{lat}' for lat, lon in body)
    r = json.load(urllib.request.urlopen(urllib.request.Request(u + '?overview=full&geometries=geojson',
                                                               headers={'User-Agent': 'jizersky-qaker'}), timeout=60))
    out[n] = [[[round(lat, 5), round(lon, 5)] for lon, lat in r['routes'][0]['geometry']['coordinates']]]
    print(n, round(r['routes'][0]['distance'] / 1000, 1), 'km')
json.dump(out, open('cesty.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print({n: len(v) for n, v in out.items()}, '-> cesty.json')
