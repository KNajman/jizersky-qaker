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
  CHECK ((lat IS NULL) = (lon IS NULL))
);

CREATE TABLE IF NOT EXISTS cesta (
  id        INTEGER PRIMARY KEY,              -- ID cesty v ČHS
  objekt_id INTEGER NOT NULL REFERENCES objekt(id),
  nazev     TEXT NOT NULL,
  zapis     TEXT NOT NULL,                    -- klasifikace jak je v ČHS
  stupen    TEXT REFERENCES klasifikace(stupen) -- NULL = nejde převést (led, AF…)
);

-- nejlehčí cesta a body se počítají, neukládají
DROP VIEW IF EXISTS prehled;
CREATE VIEW prehled AS
SELECT o.id, o.nazev AS objekt, o.typ, o.masiv, s.nazev AS sektor, p.nazev AS podsektor, s.body AS body_sektor,
       s.pesky_km, s.stoupani_m, s.klesani_m, s.cil_lat, s.cil_lon,
       o.lat, o.lon, c.nazev AS cesta, c.zapis, k.body AS body_cesta,
       s.body + k.body AS body,
       (SELECT count(*) FROM cesta WHERE objekt_id = o.id) AS pocet_cest
FROM objekt o
JOIN sektor s ON s.id = o.sektor_id
LEFT JOIN podsektor p ON p.id = o.podsektor_id
LEFT JOIN cesta c ON c.id = (
  SELECT c2.id FROM cesta c2 JOIN klasifikace k2 ON k2.stupen = c2.stupen
  WHERE c2.objekt_id = o.id ORDER BY k2.poradi LIMIT 1)
LEFT JOIN klasifikace k ON k.stupen = c.stupen;
