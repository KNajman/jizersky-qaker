# Jizerský Qaker – podklady pro závodníky

Statický web (GitHub Pages) s přehledem lezeckých objektů oblasti Jizerské hory
(databáze ČHS, oblast 43) pro závod Jizerský Qaker. Start: Hausmanka, Oldřichovské sedlo.
Web slouží jen jako podklad, žádné odškrtávání ani přihlašování. Princip: KISS.

## Soubory
Web v kořeni (`index.html`, `data.json`, `obrazky/`), DB a schéma v `data/`, skripty v `skripty/` (spouštět z kořene).
- `schema.sql` – SQLite schéma (česky): sektor, podsektor, klasifikace, objekt, cesta, pohled prehled
- `jizerky.db` – databáze, zdroj pravdy (commitovat)
- `nacti.py` – stáhne/aktualizuje data z horosvaz.cz (upsert podle ID z ČHS)
- `trasy.py` – pěší vzdálenost + převýšení z Hausmanky k sektorům (OSRM foot + opentopodata EU-DEM)
- `doplnky.py` – věže přidané pořadatelem mimo ČHS (záporná ID) + chybějící cesty/GPS
- `druhy.py` – druh objektu (věž/kámen/masiv) ze seznamu skalnioblasti.cz v `data/zdroje/` (uložen ručně z prohlížeče,
  web má ochranu proti robotům); boulder = kámen. Sloupce `kniha`, `slanak` (1/0/NULL); slaňáky ručně v `doplnky.py` (SLANAK), na webu sloupec s kolečkem (druh se zatím neukazuje).
- `podsektory.py` – podsektory podle terénu: objekty do 300 m bez údolí hlubšího než 6 m mezi sebou (EU-DEM)
  tvoří skupinu, názvy z nejbližších vrcholů OSM; cache výšek `data/dem_cache.json` (necommitovat)
- `export.py` – DB -> `data.json` (bez lomů)
- `sw.js` – offline režim (stránka a data ze sítě, při výpadku z cache; mapové dlaždice se neukládají)
- `index.html` – web, Bootstrap + Leaflet z cdnjs, OSM dlaždice, načítá data.json
- `vrstevnice.py` – jednorázově vygeneruje pozadí `vrstevnice.svg` (EU-DEM + vrcholy z OSM; numpy, matplotlib)

Aktualizace jen ručně: GitHub Actions → „Aktualizace dat“ → Run workflow (`.github/workflows/aktualizace.yml`), nebo lokálně
`python3 skripty/nacti.py && python3 skripty/doplnky.py && python3 skripty/druhy.py && python3 skripty/podsektory.py && python3 skripty/trasy.py && python3 skripty/export.py`

## Pravidla bodování (potvrzeno uživatelem)
- Body objektu = body sektoru + body nejlehčí cesty.
- Body sektoru jsou FIXNÍ, zadávají se ručně (`UPDATE sektor SET body = …`). Žádný skript je nepřepisuje.
  Aktuálně: 1 Oldřichovské sedlo, Srázy a Poledník, Stržový vrch a Kopřivník;
  2 Vřesoviště, Štolpich (vč. podsektoru Svah pod Aplitovými skalami, v ČHS samostatný sektor); 3 Polední kameny a Hlídači;
  5 Rudolfov, Tišina a Smrk, Paličník.
- Odlehlé skály: body za umístění podle pěší vzdálenosti objektu z Hausmanky (`objekt.pesky_km`, plní `trasy.py`):
  do 10 km 2, do 18 km 5, dál 6 (pohled `prehled`). Na webu km u objektu a rozpětí 2–6 b.
- Klasifikace: I–VI = 1–6, dál každý stupeň +1: VIb 7, VIc 8, VII(=VIIa) 9, VIIb 10, VIIc 11, VIII 12 …
- Přeskok N = 2N bodů („Přeskok 1+“ = P1).
- Ledy, drytool, „?“ se nehodnotí (stupen NULL).
- Nejlehčí cesta = cesta s nejnižšími body.
- Druh objektu (`objekt.druh`: věž/kámen/masiv/lom) určuje `druhy.py`: skalnioblasti.cz (bez značky věž, - K/- B kámen, - M masiv),
  boulder = kámen; pak pravidla pořadatele: „- M“ v ČHS (kromě věží) a stěna/plotna/předskalí/masiv v názvu = masiv, lom = lom; RUCNE.
- Web (dotaz v `export.py`) ukazuje jen druh věž a kámen s GPS a cestami, bez zákazu lezení v ČHS (`objekt.zakaz`).
  Výjimky: ZOBRAZIT (masivy, které pořadatel chce: Koráb, Nos…) a VYRADIT (jen to, co pravidla nezachytí: ruční skrytí, dál než 22 km pěšky).
  Ze zápisu klasifikace export vynechává metry a RP. Typ (skála/boulder/lom) z názvu, ruční oprava se nepřepisuje.

## Vzdálenosti
- Jen informativní, body neovlivňují. Měří se tam (ne zpět) k objektu nejblíž těžišti sektoru,
  bod je uložen v `sektor.cil_lat/cil_lon` a lze ho ručně přepsat.

## Záložky (index.html)
Lepivé menu: Průvodce (všechny objekty bez filtrů po sektorech a podsektorech, mapa s hranicemi, bez cest a bodů – `data.json` pruvodce), Qaker (výchozí; podmenu Propozice / Mapa / Objekty), Cracker (jaro 2027),
Člověk (propozice, hledání, mapa a seznam celého sektoru Stržový vrch a Kopřivník bez filtrů Qakeru – `data.json` clovek). Přepínání přes #hash, jeden soubor.
Mapy mají tlačítko „kde jsem“ (GPS telefonu). `data.json` = {aktualizace (den stažení z ČHS, tabulka meta), objekty}, datum v zápatí a v tisku.
Tisk (tlačítko / Ctrl+P): všechny objekty na jednu A4 ve 3 sloupcích, první sloupec slaňák.

## Mapa
- Podsektory: automaticky podle terénu (`podsektory.py`), hranice vedou údolími. Výjimka: Svah pod Aplitovými
  skalami (v ČHS samostatný sektor) je ručně podsektorem Štolpichu. Ruční úpravy v `podsektory.py`: JMENA (přejmenování/sloučení),
  ROZDEL (skupina rozdělena podle nejbližšího vrcholu, Dolní Lysá skála -> Stržový vrch + Kopřivník), PRESUN (objekt do podsektoru). Na mapě menší čárkované plochy, body neovlivňují.
- Sektor = konvexní obal jeho objektů se zaoblenými rohy (+~180 m, podsektory +~145 m) s vlastní barvou, objekty mají barvu sektoru.
  Objekty dál než 3 km od mediánu sektoru se do obalu nepočítají; Odlehlé skály polygon nemají, body jsou černé.
- Přesuny objektů mezi sektory (dle pořadatele) jsou v `doplnky.py` (SEKTOR).

## Známé mezery
- Objekty bez GPS se na webu nezobrazují (doplnit případně z lezec.cz / skalnioblasti.cz, pak se ukážou).
- Zákazy lezení: jen ikona „Zákaz lezení“ u objektu v ČHS (`nacti.py`); částečné a dočasné zákazy se neřeší.
- Propozice závodu: sekce nad mapou v index.html (termín 30.–31. 10. 2026, kategorie, doložení výstupu);
  program (18:00 prezence, losování 50 věží), startovné 300 Kč/tým, přespání u Kozy, útrata.

## Styl
Bootstrap 5, paleta Jizerek (smrk #23392c, mech #6f8a4a, žula #ece9e1, borůvka #4d3d6e), pozadí vrstevnice,
start na mapě = domek, žádné logo/emoji. Sektory mají na mapě vlastní barvy. Komunikace česky, věcně, kritika vítána.
