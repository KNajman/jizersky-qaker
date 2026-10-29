# Jizerský Qaker – podklady pro závodníky

Statický web (GitHub Pages) s přehledem lezeckých objektů oblasti Jizerské hory
(databáze ČHS, oblast 43) pro závod Jizerský Qaker. Start: Hausmanka, Oldřichovské sedlo.
Web slouží jen jako podklad, žádné odškrtávání ani přihlašování. Princip: KISS.

## Soubory
- `schema.sql` – SQLite schéma (česky): sektor, podsektor, klasifikace, objekt, cesta, pohled prehled
- `jizerky.db` – databáze, zdroj pravdy (commitovat)
- `nacti.py` – stáhne/aktualizuje data z horosvaz.cz (upsert podle ID z ČHS)
- `trasy.py` – pěší vzdálenost + převýšení z Hausmanky k sektorům (OSRM foot + opentopodata EU-DEM)
- `doplnky.py` – věže přidané pořadatelem mimo ČHS (záporná ID) + chybějící cesty/GPS
- `export.py` – DB -> `data.json` (bez lomů)
- `index.html` – web, Bootstrap + Leaflet z cdnjs, OSM dlaždice, načítá data.json
- `vrstevnice.py` – jednorázově vygeneruje pozadí `vrstevnice.svg` (EU-DEM + vrcholy z OSM; numpy, matplotlib)

Aktualizace jen ručně: GitHub Actions → „Aktualizace dat“ → Run workflow (`.github/workflows/aktualizace.yml`), nebo lokálně
`python3 nacti.py && python3 doplnky.py && python3 trasy.py && python3 export.py`

## Pravidla bodování (potvrzeno uživatelem)
- Body objektu = body sektoru + body nejlehčí cesty.
- Body sektoru jsou FIXNÍ, zadávají se ručně (`UPDATE sektor SET body = …`). Žádný skript je nepřepisuje.
  Aktuálně: 1 Oldřichovské sedlo, Srázy a Poledník, Stržový vrch a Kopřivník;
  2 Vřesoviště; 3 Štolpich, Svah pod Aplitovými skalami; 4 Rudolfov, Polední kameny a Hlídači;
  5 Odlehlé skály, Tišina a Smrk, Paličník. (Odlehlé skály bonifikované kvůli dostupnosti.)
- Klasifikace: I–VI = 1–6, dál každý stupeň +1: VIb 7, VIc 8, VII(=VIIa) 9, VIIb 10, VIIc 11, VIII 12 …
- Přeskok N = 2N bodů („Přeskok 1+“ = P1).
- Ledy, drytool, „?“ se nehodnotí (stupen NULL).
- Nejlehčí cesta = cesta s nejnižšími body.
- Lomy, masivy, Loučeňské cimbuří (příliš daleko) a objekty bez cest (vč. duplicit ČHS) se na webu nezobrazují (filtr v `export.py`), bouldery ano. Typ objektu (skála/boulder/lom) určen z názvu, ruční oprava se při novém načtení nepřepisuje.

## Vzdálenosti
- Jen informativní, body neovlivňují. Měří se tam (ne zpět) k objektu nejblíž těžišti sektoru,
  bod je uložen v `sektor.cil_lat/cil_lon` a lze ho ručně přepsat.

## Mapa
- Podsektory: v `doplnky.py` (PODSEKTORY) se zadá vedoucí objekt, ostatní objekty sektoru s GPS
  se přiřadí k nejbližšímu. Na mapě menší čárkované plochy, body neovlivňují.
- Sektor = konvexní obal jeho objektů (+~80 m) s vlastní barvou, objekty mají barvu sektoru.
  Objekty dál než 3 km od mediánu sektoru se do obalu nepočítají; Odlehlé skály polygon nemají, body jsou černé.
- Přesuny objektů mezi sektory (dle pořadatele) jsou v `doplnky.py` (SEKTOR).

## Známé mezery
- Objekty bez GPS se na webu ukazují jen v seznamu (doplnit případně z lezec.cz / skalnioblasti.cz).
- Zákazy lezení (NPR Jizerskohorské bučiny) nejsou v datech zachyceny.
- Propozice závodu: sekce nad mapou v index.html (termín 30.–31. 10. 2026, kategorie, doložení výstupu);
  chybí jen přihlášky/startovné („doplní pořadatel“).

## Styl
Bootstrap 5, paleta Jizerek (smrk #23392c, mech #6f8a4a, žula #ece9e1, borůvka #4d3d6e), pozadí vrstevnice,
start na mapě = domek, žádné logo/emoji. Sektory mají na mapě vlastní barvy. Komunikace česky, věcně, kritika vítána.
