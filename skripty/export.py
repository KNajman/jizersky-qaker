"""jizerky.db -> data.json pro web. Pravidla pořadatele: nezobrazují se lomy, masivy („- M“ v ČHS),
objekty s lom/stěna/masiv/plotna v názvu, Loučeňské cimbuří a objekty bez cest (i duplicitní prázdné záznamy ČHS,
např. Čapí věž, Hanýsek). Věže se zobrazují vždy (kromě ploten), ZOBRAZIT vždy.
Ze zápisu klasifikace se pro web vynechávají metry a RP."""
import re, sqlite3, json
ZOBRAZIT = {'Černá věž', 'Hromová věž', 'Koráb', 'Zlomený kámen', 'Plotnová věž'}
VYRADIT = {8387, 8415,  # Kočičí kámen (vedou na něj schody), Podsvětí (masiv)
           274, 8403, 9088, 9074,  # Gumáček, Kohoutí hřeben, Paličník, Bivak
           15801, 17168, 18483, 16486, 16253, 17245, 19279, 19280, 16947, 16252, 12448,
           # ↑ Vrátnej, Náhrobní kámen, Patka, Vodojem, Boží Muka, Bushman, Dračí doupě, Fojtecký drak, Páže, Špičoun (Raketa), Tvrz
           9385, 14221, 10456, 16488}  # Karetní stůl, Podhradí, Palisáda, Žezlo
VEN = re.compile(r'\blom\b|stěn|masiv|masív', re.I)
db = sqlite3.connect("data/jizerky.db"); db.row_factory = sqlite3.Row
rows = [dict(r) for r in db.execute(
    "SELECT * FROM prehled WHERE id != 18455 AND id NOT IN (%s) AND pocet_cest > 0 ORDER BY sektor, objekt COLLATE NOCASE" % ",".join(map(str, VYRADIT)))]
rows = [r for r in rows if r['objekt'] in ZOBRAZIT or 'plotn' not in r['objekt'].lower() and ('věž' in r['objekt'].lower()
        or not (r['masiv'] or r['typ'] == 'lom' or VEN.search(r['objekt'])))]

def zapis(z):  # „VIc, RP VII, 8m“ -> „VIc“, samotné „RP IV-V“ -> „IV-V“
    c = [x for x in z.split(', ') if not re.fullmatch(r'\d+\s*m', x)]
    return ', '.join(x for x in c if not x.startswith('RP ')) or ', '.join(x[3:] for x in c)
for r in rows:
    if r['zapis']: r['zapis'] = zapis(r['zapis'])
json.dump(rows, open("data.json", "w"), ensure_ascii=False)
print(len(rows), "objektů -> data.json")
