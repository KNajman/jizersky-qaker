"""Místní třídič obrázků (tabulka obrazek): náhledy po objektech, kliknutím se uloží ruční druh.
Spuštění z kořene: python3 skripty/tridic.py, pak http://localhost:8766 (jen na tomto počítači)."""
import json, os, sqlite3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

DRUHY = ['nakres', 'foto', 'protokol', 'mapa', 'jine']
STRANKA = """<!doctype html><html lang="cs"><head><meta charset="utf-8"><title>Třídič obrázků</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--les:#23392c;--mech:#6f8a4a;--zula:#ece9e1;--boruvka:#4d3d6e}
body{margin:0;font:15px system-ui,sans-serif;background:var(--zula);color:#222}
header{position:sticky;top:0;z-index:2;background:var(--les);color:#fff;padding:.5rem 1rem;display:flex;gap:1rem;flex-wrap:wrap;align-items:center}
header select,header label{font:inherit}
main{padding:1rem}h2{margin:1.2rem 0 .4rem;font-size:1.1rem}
.mrizka{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.6rem}
.obr{background:#fff;border-radius:.4rem;padding:.4rem;border:3px solid transparent}
.obr.rucne{border-color:var(--mech)}
.obr img{width:100%;height:200px;object-fit:contain;background:#f6f6f6;cursor:zoom-in}
.obr p{margin:.3rem 0;font-size:.8rem;color:#555;min-height:1.1em}
.tl{display:flex;flex-wrap:wrap;gap:.2rem}
.tl button{flex:1;border:1px solid #bbb;background:#fff;border-radius:.3rem;padding:.25rem;font-size:.8rem;cursor:pointer}
.tl button.odhad{border-style:dashed;border-color:var(--boruvka)}
.tl.typ{margin-top:.2rem}.tl.typ button{border-color:var(--mech)}
.tl button.vybrano{background:var(--boruvka);color:#fff;border-color:var(--boruvka)}
#velky{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;z-index:3}
#velky img{width:100%;height:100%;object-fit:contain}
</style></head><body>
<header><b>Třídič obrázků</b>
<label>Zobrazit <select id="filtr"><option value="">vše</option><option value="netrideno">netříděné</option>
<option value="nakres">nákres</option><option value="foto">foto</option><option value="protokol">protokol</option>
<option value="mapa">mapa</option><option value="jine">jiné</option><option value="bez">nákres věže bez typu</option></select></label>
<span id="stav"></span><span style="opacity:.7">přerušovaný rámeček = odhad, plný = ručně · klik na obrázek = zvětšit</span></header>
<main id="seznam"></main><div id="velky" onclick="this.style.display='none'"><img></div>
<script>
const D=['nakres','foto','protokol','mapa','jine'],J={nakres:'nákres',foto:'foto',protokol:'protokol',mapa:'mapa',jine:'jiné'},
 T={pudorys:'půdorys',pohled:'pohled'};
const typ=o=>o.druh==='nakres'?`<div class="tl typ">${Object.keys(T).map(t=>`<button data-t="${t}" class="${o.pohled===t?'vybrano':''}">${T[t]}</button>`).join('')}</div>`:'';
let O=[];
fetch('/api').then(r=>r.json()).then(o=>{O=o;kresli();});
function kresli(){const f=filtr.value;let h='',last;
 const R=O.filter(o=>!f||(f==='netrideno'?!o.druh:f==='bez'?o.druh==='nakres'&&o.vez&&!o.pohled:(o.druh||o.odhad)===f));
 for(const o of R){if(o.objekt!==last){if(last)h+='</div>';h+=`<h2>${o.objekt} <small style="font-weight:400;color:#666">${o.sektor}</small></h2><div class="mrizka">`;last=o.objekt;}
  h+=`<div class="obr${o.druh?' rucne':''}" data-id="${o.id}"><img loading="lazy" src="/soubor/${o.id}"><p>${o.popis||''}${o.cesta?' · '+o.cesta:''}</p>
  <div class="tl">${D.map(d=>`<button data-d="${d}" class="${(o.druh||o.odhad)===d?(o.druh?'vybrano':'odhad'):''}">${J[d]}</button>`).join('')}</div>${typ(o)}</div>`;}
 seznam.innerHTML=h+(last?'</div>':'');
 stav.textContent=`${O.filter(o=>o.druh).length} / ${O.length} roztříděno`;}
filtr.onchange=kresli;
seznam.onclick=e=>{const b=e.target.closest('button'),k=e.target.closest('.obr');if(!k)return;
 if(e.target.tagName==='IMG'){velky.querySelector('img').src=e.target.src;velky.style.display='block';return;}
 if(!b)return;const o=O.find(o=>o.id==k.dataset.id);
 if(b.dataset.t){const t=o.pohled===b.dataset.t?null:b.dataset.t;  // půdorys/pohled, druhý klik = zrušit
  return fetch('/api',{method:'POST',body:JSON.stringify({id:o.id,pohled:t})}).then(r=>{if(!r.ok)throw r;o.pohled=t;
   k.querySelectorAll('[data-t]').forEach(x=>x.className=o.pohled===x.dataset.t?'vybrano':'');}).catch(()=>alert('Uložení selhalo'));}
 const d=o.druh===b.dataset.d?null:b.dataset.d;  // druhý klik = zrušit
 fetch('/api',{method:'POST',body:JSON.stringify({id:o.id,druh:d})}).then(r=>{if(!r.ok)throw r;o.druh=d;
  k.classList.toggle('rucne',!!d);k.querySelector('.typ')?.remove();k.insertAdjacentHTML('beforeend',typ(o));k.querySelectorAll('button').forEach(x=>x.className=(o.druh||o.odhad)===x.dataset.d?(o.druh?'vybrano':'odhad'):'');
  stav.textContent=`${O.filter(o=>o.druh).length} / ${O.length} roztříděno`;}).catch(()=>alert('Uložení selhalo'));};
</script></body></html>"""

def db():
    return sqlite3.connect('data/jizerky.db')

class H(BaseHTTPRequestHandler):
    def poslat(self, kod, data, typ):
        self.send_response(kod); self.send_header('Content-Type', typ); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if self.path == '/':
            return self.poslat(200, STRANKA.encode(), 'text/html; charset=utf-8')
        if self.path == '/api':
            rows = db().execute("""SELECT b.id, o.nazev, s.nazev, c.nazev, b.popis, b.odhad, b.druh, b.pohled, o.druh='věž' FROM obrazek b
                JOIN objekt o ON o.id = b.objekt_id JOIN sektor s ON s.id = o.sektor_id LEFT JOIN cesta c ON c.id = b.cesta_id
                ORDER BY s.nazev, o.nazev COLLATE NOCASE, b.id""").fetchall()
            k = ['id', 'objekt', 'sektor', 'cesta', 'popis', 'odhad', 'druh', 'pohled', 'vez']
            return self.poslat(200, json.dumps([dict(zip(k, r)) for r in rows]).encode(), 'application/json')
        if self.path.startswith('/soubor/'):
            r = db().execute('SELECT soubor FROM obrazek WHERE id=?', (int(self.path[8:]),)).fetchone()
            if r and r[0] and os.path.exists(r[0]):
                return self.poslat(200, open(r[0], 'rb').read(), 'image/png' if r[0].endswith('.png') else 'image/jpeg')
        self.poslat(404, b'', 'text/plain')

    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        c = db()
        if 'pohled' in d:
            if d['pohled'] not in ('pudorys', 'pohled', None): return self.poslat(400, b'', 'text/plain')
            c.execute('UPDATE obrazek SET pohled=? WHERE id=?', (d['pohled'], int(d['id'])))
        else:
            if d['druh'] not in DRUHY + [None]: return self.poslat(400, b'', 'text/plain')
            c.execute('UPDATE obrazek SET druh=? WHERE id=?', (d['druh'], int(d['id'])))
        c.commit()
        self.poslat(204, b'', 'text/plain')

    def log_message(self, *a): pass

try: db().execute("ALTER TABLE obrazek ADD COLUMN pohled TEXT CHECK (pohled IN ('pudorys','pohled'))")
except sqlite3.OperationalError: pass  # sloupec už existuje
print('Třídič: http://localhost:8766')
ThreadingHTTPServer(('127.0.0.1', 8766), H).serve_forever()
