"""jizerky.db -> data.json pro web. Zobrazují se jen věže a kameny (objekt.druh, pravidla v druhy.py) s GPS a cestami,
bez zákazu lezení v ČHS; výjimky ZOBRAZIT (vždy) a VYRADIT (nikdy).
Ze zápisu klasifikace se pro web vynechávají metry a RP."""
import re, sqlite3, json
ZOBRAZIT = {'Plotnová věž', 'Koráb', 'Hranatá skála', 'Nos', 'Utečenec'}  # podle pravidel masivy, dle pořadatele zobrazit
VYRADIT = {  # ručně skryté (dle pořadatele); masivy, objekty bez GPS a se zákazem řeší pravidla, sem nepatří
    8387,   # Kočičí kámen – vedou na něj schody
    17456,  # Koňská hlava - Amfiteátr – část skály, ne samostatný vrchol
    17168,  # Náhrobní kámen (zatím bez GPS)
    9088, 9074, 15801, 18483, 16947, 16252, 12448, 10456, 16488, 8994,
    # ↑ Paličník, Bivak, Vrátnej, Patka, Páže, Špičoun (Raketa), Tvrz, Palisáda, Žezlo, Oltář
    19289, 19557, 17662, 8900, 8948, 8873, 9394, 8389}
    # ↑ dál než 22 km pěšky: Dědova skála, Narozeninová, Rybář, Polubenský hřib, Kuchař, Otesánek, Kubíkovy kameny; Trniště
db = sqlite3.connect("data/jizerky.db"); db.row_factory = sqlite3.Row
q = lambda m: ",".join("?" * len(m))
rows = [dict(r) for r in db.execute(
    f"""SELECT * FROM prehled WHERE lat IS NOT NULL AND pocet_cest > 0 AND zakaz = 0 AND id NOT IN ({q(VYRADIT)})
        AND (druh IN ('věž', 'kámen') OR objekt IN ({q(ZOBRAZIT)})) ORDER BY sektor, objekt COLLATE NOCASE""",
    [*VYRADIT, *ZOBRAZIT])]

def zapis(z):  # „VIc, RP VII, 8m“ -> „VIc“, samotné „RP IV-V“ -> „IV-V“
    c = [x for x in z.split(', ') if not re.fullmatch(r'\d+\s*m', x)]
    return ', '.join(x for x in c if not x.startswith('RP ')) or ', '.join(x[3:] for x in c)
# Jizerský Člověk: celý sektor Stržový vrch a Kopřivník bez filtrů (pravidla Qakeru neplatí)
clovek = [dict(r) for r in db.execute(
    "SELECT * FROM prehled WHERE sektor = 'Stržový vrch a Kopřivník' ORDER BY objekt COLLATE NOCASE")]
for r in rows + clovek:
    if r['zapis']: r['zapis'] = zapis(r['zapis'])
akt = db.execute("SELECT hodnota FROM meta WHERE klic = 'aktualizace'").fetchone()
json.dump({"aktualizace": akt and akt[0], "objekty": rows, "clovek": clovek}, open("data.json", "w"), ensure_ascii=False)
print(len(rows), "objektů,", len(clovek), "pro Člověka -> data.json")
