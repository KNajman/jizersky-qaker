"""Místní třídič obrázků (tabulka obrazek): náhledy po objektech, kliknutím se uloží ruční druh.
Editor půdorysů (/editor): u věže s půdorysem sever, střed a nástupy cest -> objekt.sever/stred_x/stred_y,
cesta.nastup_x/nastup_y/strana (světová strana nástupu od středu věže vůči severu).
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
<span id="stav"></span><a href="/editor" style="color:#fff">editor půdorysů</a><span style="opacity:.7">přerušovaný rámeček = odhad, plný = ručně · klik na obrázek = zvětšit</span></header>
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

EDITOR = """<!doctype html><html lang="cs"><head><meta charset="utf-8"><title>Editor půdorysů</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--les:#23392c;--mech:#6f8a4a;--zula:#ece9e1;--boruvka:#4d3d6e}
body{margin:0;font:15px system-ui,sans-serif;background:var(--zula);color:#222}
header{background:var(--les);color:#fff;padding:.5rem 1rem;display:flex;gap:1rem;flex-wrap:wrap;align-items:center}
header select,header button,header label{font:inherit}
main{display:grid;grid-template-columns:minmax(0,3fr) minmax(280px,2fr);gap:1rem;padding:1rem}
#plocha{position:relative;background:#fff;border-radius:.4rem}
#plocha svg{display:block;width:100%;height:auto;max-height:80vh}
#znacky{position:absolute;inset:0;width:100%;height:100%;cursor:crosshair}
.panel{background:#fff;border-radius:.4rem;padding:.6rem}
.nastroje button{margin:.1rem;padding:.3rem .6rem;border:1px solid #bbb;background:#fff;border-radius:.3rem;cursor:pointer}
.nastroje button.akt{background:var(--boruvka);color:#fff;border-color:var(--boruvka)}
ol{padding-left:1.6rem;margin:.4rem 0}li{padding:.25rem;border-radius:.3rem;cursor:pointer}
li.akt{background:#e4dff0}li small{color:#666;display:block}
.strana{font-weight:600;color:var(--boruvka)}.pozn{color:#666;font-size:.85rem}
</style></head><body>
<header><b>Editor půdorysů</b><select id="vyber"></select>
<label><input type="checkbox" id="orig" checked> originál</label><span id="stav"></span>
<a href="/" style="color:#fff;margin-left:auto">třídič</a></header>
<main><div id="plocha"><div id="svg"></div><svg id="znacky"></svg></div>
<div><div class="panel nastroje"><button data-n="sever">Sever</button><button data-n="stred">Střed věže</button><button data-n="cesta" class="akt">Nástup cesty</button>
<p class="pozn" id="napoveda"></p><p>Sever: <b id="sever">–</b></p></div>
<div class="panel" style="margin-top:.6rem"><b>Cesty</b> <span class="pozn">vyber cestu a klikni na její nástup; pravé tlačítko = smazat</span><ol id="cesty"></ol></div></div></main>
<script>
const STRANY=['S','SV','V','JV','J','JZ','Z','SZ'],NAP={sever:'Klikni na patu a pak na hrot severky.',stred:'Klikni na střed věže.',cesta:'Vyber cestu vpravo a klikni na její nástup.'};
let V=[],v,nastroj='cesta',cesta,pata;
const $=id=>document.getElementById(id);
fetch('/api/veze').then(r=>r.json()).then(d=>{V=d;vyber.innerHTML=V.map((x,i)=>`<option value="${i}">${x.sektor} · ${x.nazev}${x.hotovo?' ✓':''}</option>`).join('');nacti(0);});
vyber.onchange=()=>nacti(+vyber.value);
async function nacti(i){v=V[i];cesta=v.cesty.find(c=>c.x==null)||v.cesty[0];pata=null;
 $('svg').innerHTML=await (await fetch('/nakres/'+v.id)).text();
 znacky.setAttribute('viewBox',$('svg').querySelector('svg').getAttribute('viewBox'));
 orig.onchange();kresli();}
orig.onchange=()=>{const g=[...$('svg').querySelectorAll('g')].find(g=>g.getAttribute('inkscape:label')==='originál');
 if(g){g.style.display=orig.checked?'inline':'none';g.style.opacity=.45;}};
const vb=()=>znacky.getAttribute('viewBox').split(' ').map(Number);
function strana(c){if(v.sever==null||c.x==null)return null;
 const sx=v.stred_x??vb()[2]/2,sy=v.stred_y??vb()[3]/2,a=Math.atan2(c.x-sx,-(c.y-sy))*180/Math.PI-v.sever;
 return STRANY[Math.round(((a%360)+360)%360/45)%8];}
function bod(e){const p=znacky.createSVGPoint();p.x=e.clientX;p.y=e.clientY;return p.matrixTransform(znacky.getScreenCTM().inverse());}
function kresli(){const [,,w,h]=vb(),r=Math.max(w,h)/60,sx=v.stred_x??w/2,sy=v.stred_y??h/2;let g='';
 if(v.sever!=null){const a=v.sever*Math.PI/180,L=Math.max(w,h)/6;g+=`<line x1="${sx}" y1="${sy}" x2="${sx+L*Math.sin(a)}" y2="${sy-L*Math.cos(a)}" stroke="#4d3d6e" stroke-width="${r/3}" stroke-dasharray="${r/2}"/><text x="${sx+L*1.15*Math.sin(a)}" y="${sy-L*1.15*Math.cos(a)}" font-size="${r*2}" fill="#4d3d6e" text-anchor="middle" dominant-baseline="middle">S</text>`;}
 g+=`<circle cx="${sx}" cy="${sy}" r="${r/2}" fill="${v.stred_x==null?'#bbb':'#4d3d6e'}"/>`;
 if(pata)g+=`<circle cx="${pata.x}" cy="${pata.y}" r="${r/2}" fill="#c0392b"/>`;
 v.cesty.forEach((c,i)=>{if(c.x!=null)g+=`<circle cx="${c.x}" cy="${c.y}" r="${r}" fill="${c===cesta?'#c0392b':'#fff'}" stroke="#c0392b" stroke-width="${r/4}"/><text x="${c.x}" y="${c.y}" font-size="${r*1.1}" text-anchor="middle" dominant-baseline="central" fill="${c===cesta?'#fff':'#c0392b'}">${i+1}</text>`;});
 znacky.innerHTML=g;
 $('sever').textContent=v.sever==null?'nezadán':Math.round(v.sever)+'°';
 $('cesty').innerHTML=v.cesty.map((c,i)=>`<li data-i="${i}" class="${c===cesta?'akt':''}">${c.nazev} <b>${c.zapis||''}</b> <span class="strana">${c.strana||''}</span>${c.popis?`<small>${c.popis}</small>`:''}</li>`).join('');
 $('napoveda').textContent=NAP[nastroj];
 $('stav').textContent=`${v.cesty.filter(c=>c.x!=null).length} / ${v.cesty.length} nástupů`;
 document.querySelectorAll('.nastroje button').forEach(b=>b.classList.toggle('akt',b.dataset.n===nastroj));}
document.querySelector('.nastroje').onclick=e=>{if(e.target.dataset.n){nastroj=e.target.dataset.n;pata=null;kresli();}};
cesty.onclick=e=>{const li=e.target.closest('li');if(li){cesta=v.cesty[li.dataset.i];nastroj='cesta';kresli();}};
cesty.oncontextmenu=e=>{const li=e.target.closest('li');if(!li)return;e.preventDefault();const c=v.cesty[li.dataset.i];c.x=c.y=c.strana=null;ulozC(c);kresli();};
const post=(u,d)=>fetch(u,{method:'POST',body:JSON.stringify(d)}).then(r=>{if(!r.ok)throw r;}).catch(()=>alert('Uložení selhalo'));
const ulozC=c=>post('/api/cesta',{id:c.id,x:c.x,y:c.y,strana:c.strana});
const ulozV=()=>{post('/api/vez',{id:v.id,sever:v.sever,stred_x:v.stred_x,stred_y:v.stred_y});
 v.cesty.forEach(c=>{const s=strana(c);if(s!==c.strana){c.strana=s;ulozC(c);}});};
znacky.onclick=e=>{const p=bod(e);
 if(nastroj==='sever'){if(!pata)pata=p;else{v.sever=(Math.atan2(p.x-pata.x,-(p.y-pata.y))*180/Math.PI+360)%360;pata=null;ulozV();nastroj='cesta';}}
 else if(nastroj==='stred'){v.stred_x=p.x;v.stred_y=p.y;ulozV();nastroj='cesta';}
 else if(cesta){cesta.x=p.x;cesta.y=p.y;cesta.strana=strana(cesta);ulozC(cesta);
  const i=v.cesty.indexOf(cesta);cesta=v.cesty.slice(i+1).find(c=>c.x==null)||cesta;}
 kresli();};
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
        if self.path == '/editor':
            return self.poslat(200, EDITOR.encode(), 'text/html; charset=utf-8')
        if self.path == '/api/veze':  # věže s nákresem z půdorysu, jejich cesty a nástupy
            c = db(); out = []
            for oid, n, sek, sv, sx, sy in c.execute("""SELECT o.id, o.nazev, s.nazev, o.sever, o.stred_x, o.stred_y FROM objekt o
                    JOIN sektor s ON s.id = o.sektor_id WHERE o.nakres IS NOT NULL AND o.druh = 'věž' AND EXISTS
                    (SELECT 1 FROM obrazek WHERE objekt_id = o.id AND druh = 'nakres' AND pohled = 'pudorys')
                    ORDER BY s.nazev, o.nazev COLLATE NOCASE"""):
                k = ['id', 'nazev', 'zapis', 'popis', 'x', 'y', 'strana']
                cesty = [dict(zip(k, r)) for r in c.execute('SELECT id, nazev, zapis, popis, nastup_x, nastup_y, strana '
                                                            'FROM cesta WHERE objekt_id=? ORDER BY id', (oid,))]
                out.append({'id': oid, 'nazev': n, 'sektor': sek, 'sever': sv, 'stred_x': sx, 'stred_y': sy, 'cesty': cesty,
                            'hotovo': sv is not None and all(x['x'] is not None for x in cesty)})
            return self.poslat(200, json.dumps(out).encode(), 'application/json')
        if self.path.startswith('/nakres/'):  # lokální SVG i s originálem
            f = f'obrazky/nakresy/{int(self.path[8:])}.svg'
            if os.path.exists(f): return self.poslat(200, open(f, 'rb').read(), 'image/svg+xml')
        if self.path.startswith('/soubor/'):
            r = db().execute('SELECT soubor FROM obrazek WHERE id=?', (int(self.path[8:]),)).fetchone()
            if r and r[0] and os.path.exists(r[0]):
                return self.poslat(200, open(r[0], 'rb').read(), 'image/png' if r[0].endswith('.png') else 'image/jpeg')
        self.poslat(404, b'', 'text/plain')

    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        c = db()
        if self.path == '/api/vez':
            c.execute('UPDATE objekt SET sever=?, stred_x=?, stred_y=? WHERE id=?', (d['sever'], d['stred_x'], d['stred_y'], int(d['id'])))
        elif self.path == '/api/cesta':
            if d['strana'] not in ('S', 'SV', 'V', 'JV', 'J', 'JZ', 'Z', 'SZ', None): return self.poslat(400, b'', 'text/plain')
            c.execute('UPDATE cesta SET nastup_x=?, nastup_y=?, strana=? WHERE id=?', (d['x'], d['y'], d['strana'], int(d['id'])))
        elif 'pohled' in d:
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
for t, col in (('objekt', 'sever REAL'), ('objekt', 'stred_x REAL'), ('objekt', 'stred_y REAL'),
               ('cesta', 'nastup_x REAL'), ('cesta', 'nastup_y REAL'), ('cesta', 'strana TEXT')):
    try: db().execute(f'ALTER TABLE {t} ADD COLUMN {col}')
    except sqlite3.OperationalError: pass  # sloupec už existuje
print('Třídič: http://localhost:8766, editor půdorysů: http://localhost:8766/editor')
ThreadingHTTPServer(('127.0.0.1', 8766), H).serve_forever()
