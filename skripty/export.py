"""jizerky.db -> data.json pro web. Pravidla pořadatele: nezobrazují se lomy, masivy („- M“ v ČHS),
objekty s lom/stěna/masiv/plotna v názvu, Loučeňské cimbuří a objekty bez cest (i duplicitní prázdné záznamy ČHS,
např. Čapí věž, Hanýsek). Věže a ZOBRAZIT se zobrazují vždy (kromě ploten).
Ze zápisu klasifikace se pro web vynechávají metry a RP."""
import re, sqlite3, json
ZOBRAZIT = {'Černá věž', 'Hromová věž', 'Koráb', 'Zlomený kámen'}
VEN = re.compile(r'lom|stěn|masiv|masív', re.I)
db = sqlite3.connect("data/jizerky.db"); db.row_factory = sqlite3.Row
rows = [dict(r) for r in db.execute(
    "SELECT * FROM prehled WHERE id != 18455 AND pocet_cest > 0 ORDER BY sektor, objekt COLLATE NOCASE")]
rows = [r for r in rows if 'plotn' not in r['objekt'].lower() and ('věž' in r['objekt'].lower() or r['objekt'] in ZOBRAZIT
        or not (r['masiv'] or r['typ'] == 'lom' or VEN.search(r['objekt'])))]

def zapis(z):  # „VIc, RP VII, 8m“ -> „VIc“, samotné „RP IV-V“ -> „IV-V“
    c = [x for x in z.split(', ') if not re.fullmatch(r'\d+\s*m', x)]
    return ', '.join(x for x in c if not x.startswith('RP ')) or ', '.join(x[3:] for x in c)
for r in rows:
    if r['zapis']: r['zapis'] = zapis(r['zapis'])
json.dump(rows, open("data.json", "w"), ensure_ascii=False)
print(len(rows), "objektů -> data.json")
