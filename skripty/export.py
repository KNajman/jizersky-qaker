"""jizerky.db -> data.json pro web. Zobrazují se jen věže a kameny (objekt.druh, pravidla v druhy.py) s GPS a cestami,
bez zákazu lezení v ČHS; výjimky ZOBRAZIT (vždy) a VYRADIT (nikdy).
Ze zápisu klasifikace se pro web vynechávají metry a RP."""
import re, sqlite3, json
ZOBRAZIT = {'Černá věž', 'Hromová věž', 'Koráb', 'Zlomený kámen', 'Plotnová věž',
            'Hranatá skála', 'Nos', 'Utečenec'}  # masivy na skalnioblasti.cz, ale v kamarádově seznamu
VYRADIT = {8387, 8415,  # Kočičí kámen (vedou na něj schody), Podsvětí (masiv)
           274, 8403, 9088, 9074,  # Gumáček, Kohoutí hřeben, Paličník, Bivak
           15801, 17168, 18483, 16486, 16253, 17245, 19279, 19280, 16947, 16252, 12448,
           # ↑ Vrátnej, Náhrobní kámen, Patka, Vodojem, Boží Muka, Bushman, Dračí doupě, Fojtecký drak, Páže, Špičoun (Raketa), Tvrz
           9385, 14221, 10456, 16488,  # Karetní stůl, Podhradí, Palisáda, Žezlo
           10440, 10434, 14232, 10431,  # Saloon, Ruplá, Schody, Regál
           17456, 10362,  # Koňská hlava - Amfiteátr, Frýdlantské cimbuří - západní vrchol
           19289, 19557, 17662, 8900, 8948, 8873, 9394, 18455,  # dál než 22 km pěšky: Dědova skála, Narozeninová, Rybář, Polubenský hřib, Kuchař, Otesánek v Albrechtickém sedle, Kubíkovy kameny, Loučeňské cimbuří
           8389, 12429,  # Trniště, Skleník (podsektor Koňská hlava, chybí GPS – po doplnění vrátit)
           7485, 15799, 16971, 14227, 12330, 10449, 8994, 10429, 14223, 8108, 14214, 282, 9384, 9063, 9059, 12650, 10274, 9181, 12106, 12642, 17436, 10432, 12104, 8345}  # „- M“ na skalnioblasti.cz (kromě kamarádova seznamu), Vodopádový solitér (masiv)
db = sqlite3.connect("data/jizerky.db"); db.row_factory = sqlite3.Row
q = lambda m: ",".join("?" * len(m))
rows = [dict(r) for r in db.execute(
    f"""SELECT * FROM prehled WHERE lat IS NOT NULL AND pocet_cest > 0 AND zakaz = 0 AND id NOT IN ({q(VYRADIT)})
        AND (druh IN ('věž', 'kámen') OR objekt IN ({q(ZOBRAZIT)})) ORDER BY sektor, objekt COLLATE NOCASE""",
    [*VYRADIT, *ZOBRAZIT])]

def zapis(z):  # „VIc, RP VII, 8m“ -> „VIc“, samotné „RP IV-V“ -> „IV-V“
    c = [x for x in z.split(', ') if not re.fullmatch(r'\d+\s*m', x)]
    return ', '.join(x for x in c if not x.startswith('RP ')) or ', '.join(x[3:] for x in c)
for r in rows:
    if r['zapis']: r['zapis'] = zapis(r['zapis'])
json.dump(rows, open("data.json", "w"), ensure_ascii=False)
print(len(rows), "objektů -> data.json")
