# Jizerský Qaker – podklady pro závodníky

Statický web: tabulka objektů oblasti Jizerské hory (ČHS) po sektorech,
nejlehčí cesta, body a mapa.

## Struktura
- `index.html`, `data.json` – web (GitHub Pages z kořene), `obrazky/` – pozadí s vrstevnicemi, logo Mapy.cz
- `data/` – `jizerky.db` (SQLite, zdroj pravdy), `schema.sql`; cache výšek `dem_cache.json` se necommituje
- `skripty/` – Python, spouští se z kořene repozitáře:
  - `nacti.py` – stáhne/aktualizuje data z ČHS (podle ID z ČHS)
  - `doplnky.py` – věže přidané pořadatelem, opravy GPS, přesuny mezi sektory
  - `druhy.py` – druh objektu (věž/kámen/masiv) ze seznamu skalnioblasti.cz (`data/zdroje/`)
  - `podsektory.py` – podsektory podle terénu (numpy)
  - `trasy.py` – pěší vzdálenost a převýšení z Hausmanky, body neovlivňuje
  - `export.py` – DB -> `data.json` (filtr lomů, masivů…)
  - `vrstevnice.py` – jednorázově vygeneruje `obrazky/vrstevnice.svg` (numpy, matplotlib)

## Aktualizace
Ručně: GitHub Actions → Aktualizace dat → Run workflow, nebo lokálně:

    python3 skripty/nacti.py && python3 skripty/doplnky.py && python3 skripty/druhy.py && python3 skripty/podsektory.py && python3 skripty/trasy.py && python3 skripty/export.py

Body sektorů jsou fixní, zadávají se ručně:
    UPDATE sektor SET body = 4 WHERE nazev = 'Rudolfov';
Cíl měření vzdálenosti lze přepsat a pak spustit trasy.py:
    UPDATE sektor SET cil_lat = 50.85, cil_lon = 15.2 WHERE nazev = 'Rudolfov';
Ruční úprava typu objektu se při novém načtení nepřepisuje:
    UPDATE objekt SET typ = 'boulder' WHERE id = 12345;

## GitHub Pages
Settings → Pages → Deploy from branch → main / root.
Lokálně otevřít přes `python3 -m http.server` (fetch z file:// nefunguje).
