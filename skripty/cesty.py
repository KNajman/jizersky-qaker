"""Zvýrazněné pěší cesty z OpenStreetMap (Overpass) -> cesty.json pro web. Spouštět jednorázově, když se změní seznam."""
import json, urllib.parse, urllib.request
CESTY = ['Viničná cesta', 'Čínská cesta', 'Štolpišská silnice', 'Pavlova cesta', 'Paličníková cesta', 'Kozí stezka',
         'Knížecí cesta', 'Nová poutní cesta']
q = '[out:json][timeout:60];way["highway"]["name"~"^(%s)$"](50.70,14.95,50.95,15.40);out geom;' % '|'.join(CESTY)
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode(),
                             headers={'User-Agent': 'jizersky-qaker'})
d = json.load(urllib.request.urlopen(req, timeout=90))
out = {n: [[[round(p['lat'], 5), round(p['lon'], 5)] for p in w['geometry']] for w in d['elements'] if w['tags']['name'] == n]
       for n in CESTY}
json.dump(out, open('cesty.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print({n: len(v) for n, v in out.items()}, '-> cesty.json')
