-- Jizerský Qaker – podklady pro závodníky
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sektor (
  id     INTEGER PRIMARY KEY,                 -- ID sektoru v ČHS
  nazev  TEXT NOT NULL UNIQUE,
  body   INTEGER CHECK (body BETWEEN 1 AND 5), -- fixní body dle pořadatele, zadávají se ručně
  pesky_km   REAL,     -- z Hausmanky, plní trasy.py
  stoupani_m INTEGER,  -- převýšení nahoru cestou tam
  klesani_m  INTEGER,  -- převýšení dolů cestou tam
  cil_lat REAL, cil_lon REAL -- bod, ke kterému se měří (lze přepsat ručně)
);

CREATE TABLE IF NOT EXISTS klasifikace (
  stupen TEXT PRIMARY KEY,                    -- 'I' … 'XI', 'VIIb' …
  poradi INTEGER NOT NULL UNIQUE,             -- pro řazení obtížnosti
  body   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS podsektor (     -- členění sektoru podle terénu, plní podsektory.py
  id        INTEGER PRIMARY KEY,
  sektor_id INTEGER NOT NULL REFERENCES sektor(id),
  nazev     TEXT NOT NULL,
  vrchol_lat REAL, vrchol_lon REAL, vyska INTEGER, -- vrchol, ke kterému objekty „stékají“;
                                                   -- NULL = celý sektor ČHS (doplnky.py), podsektory.py nepřepisuje
  UNIQUE (sektor_id, nazev)
);

CREATE TABLE IF NOT EXISTS objekt (
  id        INTEGER PRIMARY KEY,              -- ID skály v ČHS
  sektor_id INTEGER NOT NULL REFERENCES sektor(id),
  nazev     TEXT NOT NULL,
  typ       TEXT NOT NULL DEFAULT 'skála' CHECK (typ IN ('skála','boulder','lom')),
  lat REAL, lon REAL,
  podsektor_id INTEGER REFERENCES podsektor(id),
  masiv     INTEGER NOT NULL DEFAULT 0,       -- 1 = v ČHS označen „- M“
  zakaz     INTEGER NOT NULL DEFAULT 0,       -- 1 = v ČHS ikona „Zákaz lezení“
  druh      TEXT CHECK (druh IN ('věž','kámen','masiv','stěna','led')), -- druhy.py: skalnioblasti.cz + pravidla pořadatele
  so_id     INTEGER,                          -- ID skály na skalnioblasti.cz
  kniha     INTEGER,                          -- vrcholová kniha: 1 ano, 0 ne, NULL nevíme
  slanak    INTEGER,                          -- slaňovací kruh: 1 ano, 0 ne, NULL nevíme
  pesky_km  REAL,                             -- z Hausmanky k objektu, jen Odlehlé skály (trasy.py)
  nakres    TEXT,                             -- vlastní nákres (SVG překreslené ze schématu), např. obrazky/nakresy/8335.svg
  CHECK ((lat IS NULL) = (lon IS NULL))
);

CREATE TABLE IF NOT EXISTS cesta (
  id        INTEGER PRIMARY KEY,              -- ID cesty v ČHS
  objekt_id INTEGER NOT NULL REFERENCES objekt(id),
  nazev     TEXT NOT NULL,
  zapis     TEXT NOT NULL,                    -- klasifikace jak je v ČHS
  stupen    TEXT REFERENCES klasifikace(stupen), -- NULL = nejde převést (led, AF…)
  popis     TEXT,                             -- popis cesty z ČHS
  prvovystup TEXT,                            -- jak je v ČHS: 'Bruno Ullrich, E. Hütter,1922'
  datum     TEXT,                             -- datum prvovýstupu jak je v ČHS (15.6.1991, 1922)
  rok       INTEGER,                          -- rok prvovýstupu (pro řazení)
  kruhy     INTEGER                           -- fixní jištění (kruhy, skoby, nýty) dle ikony ČHS: 1 ano, 0 ne
);

CREATE TABLE IF NOT EXISTS autor (            -- autoři prvovýstupů, plní nacti.py
  id    INTEGER PRIMARY KEY,
  jmeno TEXT NOT NULL UNIQUE                  -- jak je v ČHS ('Rudolf Kauschka', 'E. Hütter')
);

CREATE TABLE IF NOT EXISTS cesta_autor (      -- cesta může mít více autorů
  cesta_id INTEGER NOT NULL REFERENCES cesta(id) ON DELETE CASCADE,
  autor_id INTEGER NOT NULL REFERENCES autor(id),
  poradi   INTEGER NOT NULL,                  -- pořadí v zápisu prvovýstupu
  PRIMARY KEY (cesta_id, autor_id)
);

CREATE TABLE IF NOT EXISTS obrazek (          -- fotky a nákresy ke skalám, plní obrazky.py (ČHS), ručně (skalnioblasti, průvodce)
  id        INTEGER PRIMARY KEY,
  url       TEXT UNIQUE,                      -- původní adresa (NULL u skenu z průvodce)
  objekt_id INTEGER NOT NULL REFERENCES objekt(id),
  cesta_id  INTEGER REFERENCES cesta(id),     -- obrázek z galerie cesty
  zdroj     TEXT NOT NULL CHECK (zdroj IN ('čhs','skalnioblasti','průvodce')),
  popis     TEXT,                             -- popisek z galerie ('topo', 'protokol' …)
  soubor    TEXT,                             -- data/obrazky/<objekt>/<soubor> (necommitovat)
  odhad     TEXT CHECK (odhad IN ('foto','nakres','protokol','mapa')),  -- automaticky (popisek, barevnost)
  druh      TEXT CHECK (druh IN ('foto','nakres','protokol','mapa','jine'))  -- ručně, má přednost před odhadem
);

CREATE TABLE IF NOT EXISTS meta (klic TEXT PRIMARY KEY, hodnota TEXT);  -- aktualizace = den stažení z ČHS

-- nejlehčí cesta a body se počítají, neukládají
-- Odlehlé skály: body za umístění podle pěší vzdálenosti objektu (do 10 km 2, do 18 km 5, dál 6)
DROP VIEW IF EXISTS prehled;
CREATE VIEW prehled AS
SELECT o.id, o.nazev AS objekt, o.typ, o.masiv, o.zakaz, o.druh, o.kniha, o.slanak, s.nazev AS sektor, p.nazev AS podsektor, 
       CASE WHEN o.pesky_km IS NULL THEN s.body WHEN o.pesky_km <= 10 THEN 2 WHEN o.pesky_km <= 18 THEN 5 ELSE 6 END AS body_sektor,
       o.pesky_km AS km_objekt, s.pesky_km, s.stoupani_m, s.klesani_m, s.cil_lat, s.cil_lon,
       o.lat, o.lon, c.nazev AS cesta, c.zapis, k.body AS body_cesta,
       CASE WHEN o.pesky_km IS NULL THEN s.body WHEN o.pesky_km <= 10 THEN 2 WHEN o.pesky_km <= 18 THEN 5 ELSE 6 END + k.body AS body,
       (SELECT count(*) FROM cesta WHERE objekt_id = o.id) AS pocet_cest
FROM objekt o
JOIN sektor s ON s.id = o.sektor_id
LEFT JOIN podsektor p ON p.id = o.podsektor_id
LEFT JOIN cesta c ON c.id = (
  SELECT c2.id FROM cesta c2 JOIN klasifikace k2 ON k2.stupen = c2.stupen
  WHERE c2.objekt_id = o.id ORDER BY k2.poradi LIMIT 1)
LEFT JOIN klasifikace k ON k.stupen = c.stupen;
