"""Druh objektu (věž / kámen / masiv / stěna / led) ze seznamu skal na skalnioblasti.cz uloženého v data/zdroje/
(bez značky = věž, „- K“ a „- B“ = kámen, „- M“ = masiv). Páruje se podle názvu v rámci oblasti;
nespárované vypíše. Stránka má ochranu proti robotům, seznam se proto ukládá ručně z prohlížeče."""
import html, re, sqlite3, unicodedata
SEZNAM = 'data/zdroje/skalnioblasti-seznam.html'
DRUH = {'': 'věž', 'K': 'kámen', 'B': 'kámen', 'M': 'masiv'}

def klic(n):  # bez diakritiky, závorek a interpunkce
    n = unicodedata.normalize('NFD', n.lower())
    n = re.sub(r'\(.*?\)', '', ''.join(c for c in n if not unicodedata.combining(c)))
    return ' '.join(re.findall(r'[a-z0-9]+', n))

s = open(SEZNAM, encoding='utf-8', errors='replace').read()
so = {}
for sid, n in re.findall(r'skala_id=(\d+)"[^>]*><font[^>]*>([^<]+)</font>', s):
    n, z = re.match(r'(.*?)(?: - ([A-Z]))?$', html.unescape(n).strip()).groups()
    so[klic(n)] = (int(sid), DRUH[z or ''])
db = sqlite3.connect('data/jizerky.db')
nic = []
for oid, n in db.execute('SELECT id, nazev FROM objekt').fetchall():
    k = klic(n)
    if k in so: db.execute('UPDATE objekt SET so_id=?, druh=? WHERE id=?', (*so[k], oid))
    else: nic.append(n)
db.execute("UPDATE objekt SET druh='kámen' WHERE typ='boulder'")  # boulder = kámen (dle pořadatele)
for vzor, d in (('%věž%', 'věž'), ('%kámen%', 'kámen')):  # bez shody podle názvu
    db.execute("UPDATE objekt SET druh=? WHERE druh IS NULL AND nazev LIKE ?", (d, vzor))
# pravidla pořadatele: „- M“ v ČHS (kromě věží) a plotny, předskalí, masivy = masiv; stěny a lomy = stěna;
# led = objekt jen s ledovými/drytoolovými cestami (WI, M)
db.execute("UPDATE objekt SET druh='masiv' WHERE masiv=1 AND nazev NOT LIKE '%věž%'")
for vzor in ('%masiv%', '%masív%', '%stěn%', '%plotn%', '%předskal%'):
    db.execute("UPDATE objekt SET druh='masiv' WHERE nazev LIKE ?", (vzor,))
db.execute("UPDATE objekt SET druh='stěna' WHERE nazev LIKE '%stěn%' OR typ='lom' OR nazev LIKE 'Lom %'")
db.execute("""UPDATE objekt SET druh='led' WHERE EXISTS (SELECT 1 FROM cesta WHERE objekt_id=objekt.id)
              AND NOT EXISTS (SELECT 1 FROM cesta WHERE objekt_id=objekt.id AND zapis NOT LIKE 'WI%' AND zapis NOT LIKE 'M%')""")
RUCNE = {16979: 'kámen', 8345: 'masiv', 17722: 'kámen', 17718: 'kámen'}  # Tank B, Vodopádový solitér, Tlustoprd, Skalní hřib
db.executemany('UPDATE objekt SET druh=? WHERE id=?', [(d, i) for i, d in RUCNE.items()])
db.commit()
print(db.execute('SELECT druh, count(*) FROM objekt GROUP BY druh').fetchall())
print(len(nic), 'bez shody:', ', '.join(sorted(nic)))
