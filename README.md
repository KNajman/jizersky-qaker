# Jizerský Qaker – podklady pro závodníky

Statický web: tabulka objektů oblasti Jizerské hory (ČHS) po sektorech,
nejlehčí cesta, body a mapa.

## Soubory
- `schema.sql` – struktura DB (sektor, klasifikace, objekt, cesta, pohled prehled)
- `jizerky.db` – SQLite databáze, zdroj pravdy
- `nacti.py` – stáhne/aktualizuje data z ČHS do DB (opakovatelně, podle ID z ČHS)
- `trasy.py` – pěší vzdálenost a převýšení z Hausmanky k sektorům (OSRM + EU-DEM), body neovlivňuje
- `export.py` – z DB vytvoří `data.json` pro web (bez lomů)
- `index.html` – web

## Aktualizace
    python3 nacti.py && python3 trasy.py && python3 export.py
    git commit -am "aktualizace dat" && git push

Body sektorů jsou fixní, zadávají se ručně:
    UPDATE sektor SET body = 4 WHERE nazev = 'Rudolfov';
Cíl měření vzdálenosti lze přepsat a pak spustit trasy.py:
    UPDATE sektor SET cil_lat = 50.85, cil_lon = 15.2 WHERE nazev = 'Rudolfov';
Ruční úprava typu objektu se při novém načtení nepřepisuje:
    UPDATE objekt SET typ = 'boulder' WHERE id = 12345;

## GitHub Pages
Settings → Pages → Deploy from branch → main / root.
Lokálně otevřít přes `python3 -m http.server` (fetch z file:// nefunguje).
