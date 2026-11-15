#!/usr/bin/env python3
"""Bundle GLB models + circuit SVGs into one self-contained viewer/index.html.
    python hardware/cad/build_viewer.py   (run build_models.py and schematics.py first)
Needs internet in the browser for three.js (cdn.jsdelivr.net)."""
import base64, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
DEV = [
  ("cubesat", "CubeSat", "1U stack, 100 mm. Six boards on four corner rods.",
   [("Frame", "100 x 100 x 100 mm"), ("Boards", "6 layers, 90 x 90 mm"), ("Antenna", "433 MHz dipole, 2 x 173 mm"), ("Computer", "Raspberry Pi Zero W"), ("Mass in photo", "424 g on the scale")]),
  ("rescue_tower", "Rescue tower", "Solar powered SOS tower with beacon and helical antenna. Illustrative scale.",
   [("Mast", "1.1 m lattice, 130 mm square"), ("Computer", "ESP32 + LoRa RA-02"), ("Interface", "OLED, SOS button, GPS"), ("Top", "beacon + helical antenna on dish"), ("Power", "solar panel + PMU + 18650")]),
  ("ground_station", "Ground station", "Arduino Nano + ESP32 + RA-02 in an enclosure, helical antenna on a mast. Illustrative scale.",
   [("Enclosure", "170 x 110 x 55 mm (printable)"), ("Boards", "Arduino Nano + ESP32 DevKit"), ("Radio", "LoRa RA-02, SMA to antenna"), ("Mast", "650 mm pole, helical on dish")]),
]
TRANSPARENT = {"beacon_lamp": 0.75, "enc_enclosure": 0.22, "enc_lid": 0.45}
data = {}
for key, name, blurb, facts in DEV:
    glb = base64.b64encode((ROOT / key / f"{key}.glb").read_bytes()).decode()
    parts = json.load((ROOT / key / "parts.json").open())
    circuits = [("Circuit", (ROOT / key / "circuit.svg").read_text())]
    if key == "cubesat": circuits.append(("Burn-wire driver", (ROOT / key / "burnwire.svg").read_text()))
    data[key] = dict(name=name, blurb=blurb, facts=facts, glb=glb, parts=parts, circuits=circuits)

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CubeSat Rescue System</title>
<style>
:root{--bg:#f1f4f7;--surface:#fff;--ink:#0d1621;--ink2:#465465;--ink3:#66737f;--line:#d3dbe3;--accent:#2a78d6;--accent-ink:#fff;--stage:#e4e9ee}
@media (prefers-color-scheme:dark){:root{--bg:#0e1319;--surface:#161d25;--ink:#e8edf2;--ink2:#b4bfca;--ink3:#8f9ba7;--line:#2b3641;--accent:#3987e5;--accent-ink:#06101c;--stage:#0b1015}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;padding:0 max(16px,env(safe-area-inset-left)) 48px}
.wrap{max-width:1180px;margin:0 auto}h1{font-size:clamp(24px,4vw,34px);margin:26px 0 4px}h2{font-size:20px;margin:0 0 6px}
.lede{color:var(--ink2);max-width:70ch;margin:0 0 14px}
nav{display:flex;gap:6px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:8px;position:sticky;top:0;background:var(--bg);z-index:5;padding-top:8px}
button{font:600 14px system-ui,sans-serif;cursor:pointer;color:var(--ink2);background:none;border:1px solid transparent;border-radius:6px;padding:7px 13px}
button[aria-pressed=true],button[aria-selected=true]{background:var(--surface);border-color:var(--line);color:var(--ink);box-shadow:0 -2px 0 var(--accent) inset}
.sub{display:flex;gap:6px;margin:14px 0}
.grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:20px}@media(max-width:860px){.grid{grid-template-columns:minmax(0,1fr)}}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:16px;min-width:0}
.stage{position:relative;border:1px solid var(--line);border-radius:8px;background:var(--stage);aspect-ratio:16/10;min-height:320px;overflow:hidden}
.stage canvas{position:absolute;inset:0;width:100%!important;height:100%!important}
.ctl{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;margin-top:12px;font-size:13.5px;color:var(--ink2)}
.ctl label{display:inline-flex;gap:6px;align-items:center;cursor:pointer}input[type=range]{width:min(220px,60vw);accent-color:var(--accent)}
dl{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin:8px 0 0;font-size:13.5px}dt{color:var(--ink3)}dd{margin:0}
.plist{max-height:260px;overflow:auto;margin-top:8px;font:12px/1.7 ui-monospace,Menlo,monospace}
.plist div{padding:0 6px;border-radius:4px;cursor:pointer}.plist div:hover,.plist div.on{background:var(--accent);color:var(--accent-ink)}
.svgbox{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:8px;overflow:auto}.svgbox svg{min-width:1000px;width:100%;height:auto;display:block}
.msg{padding:40px 20px;color:var(--ink2)}.note{font-size:13px;color:var(--ink3)}
</style></head><body><div class="wrap">
<h1>CubeSat Rescue System</h1>
<p class="lede">3D models and circuit diagrams for the rescue tower, CubeSat relay and ground station. The CubeSat pins come from the project README. Tower and ground-station pins are proposed and should be checked against the build.</p>
<nav id="dev"></nav><div class="sub" id="view"></div>
<section id="v3d"><div class="grid"><div><div class="stage" id="stage"></div>
<div class="ctl"><label>Exploded <input type="range" id="ex" min="0" max="100" value="0"></label><label><input type="checkbox" id="see"> See-through enclosure</label><span id="groups"></span></div>
<div class="ctl"><span class="note">Drag to orbit, scroll or pinch to zoom, click a part name to highlight it.</span></div></div>
<div class="panel"><h2 id="dname"></h2><p class="note" id="dblurb"></p><dl id="facts"></dl><h2 style="margin-top:14px;font-size:15px">Parts</h2><div class="plist" id="plist"></div></div></div></section>
<section id="vckt" hidden><div id="ckt"></div></section>
</div>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
const D = __DATA__, TR = __TR__;
const $ = s => document.querySelector(s);
let cur = "cubesat", view = "3d", renderer, scene, camera, controls, holder, objs = [], gl = false, hl = null;
const cache = {};

function buildNav(){
  $("#dev").innerHTML = Object.keys(D).map(k => `<button data-k="${k}" aria-selected="${k===cur}">${D[k].name}</button>`).join("");
  $("#view").innerHTML = ["3d","circuit"].map(v => `<button data-v="${v}" aria-pressed="${v===view}">${v==="3d"?"3D model":"Circuit diagram"}</button>`).join("");
  document.querySelectorAll("#dev button").forEach(b => b.onclick = () => { cur = b.dataset.k; buildNav(); show(); });
  document.querySelectorAll("#view button").forEach(b => b.onclick = () => { view = b.dataset.v; buildNav(); show(); });
}
function b64(s){ const bin = atob(s), u = new Uint8Array(bin.length); for(let i=0;i<bin.length;i++) u[i]=bin.charCodeAt(i); return u.buffer; }

function init3d(){
  const host = $("#stage");
  if(!window.THREE || !THREE.GLTFLoader || !THREE.OrbitControls){ host.innerHTML = '<div class="msg">The 3D library could not load. Check your connection and reload.</div>'; return; }
  try{ renderer = new THREE.WebGLRenderer({antialias:true}); }catch(e){ host.innerHTML = '<div class="msg">WebGL is not available in this browser.</div>'; return; }
  gl = true; renderer.setPixelRatio(Math.min(devicePixelRatio,2)); host.appendChild(renderer.domElement);
  scene = new THREE.Scene(); camera = new THREE.PerspectiveCamera(36, 1.6, 1, 20000);
  controls = new THREE.OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x556270, 0.95));
  const dl = new THREE.DirectionalLight(0xffffff, 0.9); dl.position.set(1,2,1.5); scene.add(dl);
  const dl2 = new THREE.DirectionalLight(0xbcd2ff, 0.4); dl2.position.set(-1.5,0.5,-1); scene.add(dl2);
  new ResizeObserver(resize).observe(host); resize(); themeBg();
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", themeBg);
  (function loop(){ requestAnimationFrame(loop); if(view!=="3d"||document.hidden) return; controls.update(); renderer.render(scene,camera); })();
}
function themeBg(){ if(renderer) renderer.setClearColor(new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue("--stage").trim()||"#e4e9ee")); }
function resize(){ const h = $("#stage"), w = h.clientWidth, ht = h.clientHeight; if(!w||!ht||!renderer) return; renderer.setSize(w,ht,false); camera.aspect = w/ht; camera.updateProjectionMatrix(); }

function load(key){
  if(cache[key]) return Promise.resolve(cache[key]);
  return new Promise(res => new THREE.GLTFLoader().parse(b64(D[key].glb), "", g => { cache[key] = g.scene; res(g.scene); }, e => res(null)));
}
async function show3d(){
  const key = cur, d = D[cur];
  $("#dname").textContent = d.name; $("#dblurb").textContent = d.blurb;
  $("#facts").innerHTML = d.facts.map(f => `<dt>${f[0]}</dt><dd>${f[1]}</dd>`).join("");
  if(!gl) return;
  if(holder) scene.remove(holder);
  const model = await load(cur); if(!model || key !== cur) return;
  holder = new THREE.Group(); holder.rotation.x = -Math.PI/2; holder.add(model); scene.add(holder);
  objs = [];
  d.parts.forEach(p => { let o = model.getObjectByName(p.name); if(!o) return;
    o.traverse(m => { if(m.isMesh){ m.material = m.material.clone(); m.material.vertexColors = true; m.material.roughness = 0.6; m.material.metalness = 0.05;
      const t = TR[p.name]; if(t !== undefined){ m.material.transparent = true; m.material.opacity = t; m.material.depthWrite = false; m.userData.op = t; } } });
    objs.push({o, meta:p, base:o.position.clone(), vis:true}); });
  const gs = [...new Set(d.parts.map(p => p.group))];
  $("#groups").innerHTML = gs.map(g => `<label><input type="checkbox" data-g="${g}" checked> ${g}</label>`).join(" ");
  document.querySelectorAll("#groups input").forEach(c => c.onchange = () => { objs.forEach(x => { if(x.meta.group===c.dataset.g) x.o.visible = c.checked; }); });
  $("#plist").innerHTML = d.parts.map((p,i) => `<div data-i="${i}">${p.name}</div>`).join("");
  document.querySelectorAll("#plist div").forEach(el => el.onclick = () => highlight(d.parts[+el.dataset.i].name, el));
  $("#ex").value = 0; explode(); see();
  const box = new THREE.Box3().setFromObject(holder), c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3()), r = Math.max(s.x,s.y,s.z);
  controls.target.copy(c); camera.position.set(c.x + r*0.9, c.y + r*0.55, c.z + r*1.1); camera.near = r/100; camera.far = r*20; camera.updateProjectionMatrix(); controls.update();
}
function explode(){ const t = $("#ex").value/100; objs.forEach(x => { const d = x.meta.dir, k = x.meta.dist*t; x.o.position.set(x.base.x + d[0]*k, x.base.y + d[1]*k, x.base.z + d[2]*k); }); }
function see(){ const on = $("#see").checked; objs.forEach(x => x.o.traverse(m => { if(m.isMesh && x.meta.name.startsWith("enc_")){ m.material.opacity = on ? 0.12 : (TR[x.meta.name] ?? 1); } })); }
function highlight(name, el){
  document.querySelectorAll("#plist div").forEach(e => e.classList.toggle("on", e===el && hl!==name));
  objs.forEach(x => x.o.traverse(m => { if(m.isMesh){ if(!m.material.emissive) return; m.material.emissive.setHex(x.meta.name===name && hl!==name ? 0xffb020 : 0x000000); } }));
  hl = (hl===name) ? null : name;
}
function showCkt(){
  const d = D[cur]; let h = "";
  if(d.circuits.length > 1) h += `<div class="sub" id="cs">${d.circuits.map((c,i) => `<button data-c="${i}" aria-pressed="${i===0}">${c[0]}</button>`).join("")}</div>`;
  h += `<div class="svgbox" id="svgbox">${d.circuits[0][1]}</div>`;
  $("#ckt").innerHTML = h;
  document.querySelectorAll("#cs button").forEach(b => b.onclick = () => { document.querySelectorAll("#cs button").forEach(x => x.setAttribute("aria-pressed", x===b)); $("#svgbox").innerHTML = d.circuits[+b.dataset.c][1]; });
}
function show(){
  $("#v3d").hidden = view !== "3d"; $("#vckt").hidden = view !== "circuit";
  if(view === "3d"){ resize(); show3d(); } else showCkt();
}
$("#ex").addEventListener("input", explode); $("#see").addEventListener("change", see);
buildNav(); init3d(); show();
</script></body></html>"""
out = ROOT.parent / "viewer" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(HTML.replace("__DATA__", json.dumps(data)).replace("__TR__", json.dumps(TRANSPARENT)))
print("wrote", out, f"{out.stat().st_size/1e3:.0f} kB")
