"""Věže přidané pořadatelem (doplnky.pdf + mapa „Qaker přidané“ na mapy.com).
Objekty a cesty mimo ČHS mají záporné ID, nacti.py je tedy nepřepíše. Opakovatelné."""
import sqlite3

ROZ, STR, STO = 621, 44, 39  # Rudolfov, Stržový vrch a Kopřivník, Malý a Velký Štolpich
# id, sektor, název, lat, lon
OBJEKTY = [
    (-1, ROZ, 'Malý Strážce', 50.8173003, 15.1181425),
    (-2, ROZ, 'Žižiho věžička (Aiguille du Žiži)', 50.7924744, 15.1069656),
    (-3, STR, 'Hranáč', 50.8735847, 15.0949658),
    (-4, STR, 'Kuláč', 50.8735711, 15.0951506),
    (-5, STR, 'Teribl', 50.8701594, 15.0774172),
    (-6, STR, 'Kančí zub', 50.8718333, 15.0829167),
    (-7, STO, 'Jožin z bážin', 50.8593039, 15.1984108),
]
GPS = {12620: (50.8027214, 15.1069553)}  # K2 (Čchokori) v ČHS bez GPS
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

db = sqlite3.connect('jizerky.db')
db.execute('PRAGMA foreign_keys = ON')
for oid, sid, n, lat, lon in OBJEKTY:
    db.execute('INSERT OR REPLACE INTO objekt(id,sektor_id,nazev,typ,lat,lon) VALUES (?,?,?,?,?,?)',
               (oid, sid, n, 'skála', lat, lon))
for oid, (lat, lon) in GPS.items():
    db.execute('UPDATE objekt SET lat=?, lon=? WHERE id=? AND lat IS NULL', (lat, lon, oid))
db.execute('DELETE FROM cesta WHERE id < 0')
cid = 0
for oid, cesty in CESTY.items():
    for n, z in cesty:
        cid -= 1
        db.execute('INSERT INTO cesta VALUES (?,?,?,?,?)', (cid, oid, n, z, z.split('-')[0]))
db.commit()
print(len(OBJEKTY), 'objektů,', -cid, 'cest doplněno')
