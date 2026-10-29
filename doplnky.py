"""Věže přidané pořadatelem (doplnky.pdf + mapa „Qaker přidané“ na mapy.com).
Objekty a cesty mimo ČHS mají záporné ID, nacti.py je tedy nepřepíše. Opakovatelné."""
import sqlite3

ROZ, STR, SVA = 621, 44, 1242  # Rudolfov, Stržový vrch a Kopřivník, Svah pod Aplitovými skalami
VRE, SRA, ODL = 1260, 43, 40  # Vřesoviště, Srázy a Poledník, Odlehlé skály
STO = 39  # Malý a Velký Štolpich
# id, sektor, název, lat, lon
OBJEKTY = [
    (-1, ROZ, 'Malý Strážce', 50.8173003, 15.1181425),
    (-2, ROZ, 'Žižiho věžička (Aiguille du Žiži)', 50.7924744, 15.1069656),
    (-3, STR, 'Hranáč', 50.8735847, 15.0949658),
    (-4, STR, 'Kuláč', 50.8735711, 15.0951506),
    (-5, STR, 'Teribl', 50.8701594, 15.0774172),
    (-6, STR, 'Kančí zub', 50.8718333, 15.0829167),
    (-7, SVA, 'Jožin z bážin', 50.8593039, 15.1984108),
]
GPS = {  # objekty v ČHS bez GPS nebo se špatnou GPS (přepisuje ČHS)
    12620: (50.8027214, 15.1069553),  # K2 (Čchokori)
    17437: (50.8701708, 15.0985275),  # Kotel
    14219: (50.8637872, 15.0891208),  # Předskalí pyramidy
    17303: (50.8755892, 15.1023303),  # Punťa
    17718: (50.8697072, 15.0916769),  # Skalní hřib
    18268: (50.8609567, 15.0812381),  # Stěna zpívajícího stromu
    16485: (50.8593989, 15.0757769),  # The Zeď
    16488: (50.8669242, 15.0757742),  # Žezlo
    8991: (50.8693583, 15.1011372),   # Skalní brána (ČHS má souřadnice u Štolpichu)
}
CESTY = {
    -1: [('Cesta zapadajícího slunce', 'V'), ('Smrčková cesta', 'IV'), ('Jitřní červánky', 'VIb')],
    -2: [('Sloní ucho', 'II'), ('Horská túra', 'III'), ('Mirkova cesta', 'IV'), ('Balkónová zápletka', 'III'),
         ('Údolím kopretin', 'II'), ('Cesta rudolfovských rabiátů', 'IV'), ('Nepálská', 'III')],
    -3: [('Špárka', 'V'), ('Peckochyt', 'VI'), ('Hry bez hranic', 'VIb'), ('Zarovnávač nehtů', 'VIc'),
         ('Náhradní encéčko', 'V')],
    -4: [('Normální cesta', 'V'), ('Žlábek', 'V-VI'), ('Seskoková', 'VIb'), ('Hranka', 'V-VI')],
    -5: [('Přes pecky', 'V'), ('Žádná pecka', 'VI'), ('Klíčko', 'VI')],
    -6: [('Normální cesta', 'VI'), ('Dynamo kanec', 'VI'), ('Neblahý pocit', 'VI')],
    -7: [('Normální cesta', 'II'), ('Českej Shrek', 'VIc'), ('Smrt z vyděšení', 'VI'), ('Jožinova stezka', 'IV'),
         ('Procházka nad bažinou', 'V')],
    18480: [('Přes jehlu', 'VIb'), ('Náhorní sokolík', 'VI'), ('Krystalová varianta NC', 'VIb'),
            ('Normální cesta', 'VI'), ('Hyperbola', 'VIb'), ('Hrana sťa čepel', 'VIb'),
            ('NC varianta Mantl', 'VI')],  # Morion: v ČHS bez cest
    14220: [('Plameny pekelné', 'VI')],  # Ďáblík: chybí v ČHS
    17513: [('Normální cesta', 'II')],   # Sklínková věž: chybí v ČHS
}
# objekty, které jsou v ČHS historicky v jiném sektoru (dle pořadatele); nacti.py sektor přepisuje
SEKTOR = {17714: VRE, 17435: VRE, 17434: VRE, 9047: VRE,  # Klobouky, Bezinka, Pól, Hanýsek
          8388: SRA, 12330: STO,               # František, Stínová věž
          17528: ODL, 17722: ODL, 17457: ODL,  # Filipovka, Tlustoprd, Pánská jízda
          8108: ROZ, 282: ROZ}                 # Fojt, Jezdec
db = sqlite3.connect('jizerky.db')
try: db.execute('ALTER TABLE objekt ADD COLUMN podsektor_id INTEGER REFERENCES podsektor(id)')
except sqlite3.OperationalError: pass  # sloupec už existuje
db.executescript(open('schema.sql', encoding='utf-8').read())
db.execute('PRAGMA foreign_keys = ON')
for oid, sid, n, lat, lon in OBJEKTY:
    db.execute('INSERT OR REPLACE INTO objekt(id,sektor_id,nazev,typ,lat,lon) VALUES (?,?,?,?,?,?)',
               (oid, sid, n, 'skála', lat, lon))
for oid, (lat, lon) in GPS.items():
    db.execute('UPDATE objekt SET lat=?, lon=? WHERE id=?', (lat, lon, oid))
for oid, sid in SEKTOR.items():
    db.execute('UPDATE objekt SET sektor_id=? WHERE id=?', (sid, oid))
db.execute('DELETE FROM cesta WHERE id < 0')
cid = 0
for oid, cesty in CESTY.items():
    for n, z in cesty:
        cid -= 1
        db.execute('INSERT INTO cesta VALUES (?,?,?,?,?)', (cid, oid, n, z, z.split('-')[0]))
# celý sektor ČHS jako podsektor jiného sektoru (dle pořadatele): sektor ČHS -> (sektor, podsektor)
for z, (sid, n) in {SVA: (STO, 'Svah pod Aplitovými skalami')}.items():
    db.execute('INSERT OR IGNORE INTO podsektor(sektor_id,nazev) VALUES (?,?)', (sid, n))
    pid = db.execute('SELECT id FROM podsektor WHERE sektor_id=? AND nazev=?', (sid, n)).fetchone()[0]
    db.execute('UPDATE objekt SET sektor_id=?, podsektor_id=? WHERE sektor_id=?', (sid, pid, z))
db.commit()
print(len(OBJEKTY), 'objektů,', -cid, 'cest doplněno')
