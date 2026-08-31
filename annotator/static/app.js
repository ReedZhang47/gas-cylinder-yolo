"use strict";
/* YOLO detection annotator frontend (flat label format: class cx cy w h) */

const $ = (id) => document.getElementById(id);
const cv = $("cv"), ctx = cv.getContext("2d");
const PALETTE = ["#7aa2f7", "#f7768e", "#9ece6a", "#e0af68", "#bb9af7", "#2ac3de", "#ff9e64", "#73daca"];

const S = {
  root: null, info: null,
  images: [], idx: -1,
  boxes: [], sel: -1,
  dirty: false,
  img: null, imgW: 0, imgH: 0,
  s: 1, ox: 0, oy: 0, base: 1,
  names: {0: "Upside-down"},
  drag: null,
  space: false,
  zoom: 1,
  // per-image state
  boxCache: {},   // idx -> boxes array (same reference as S.boxes when loaded)
  dirtyAt: {},    // idx -> bool
};

const api = async (url, opts) => {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || `HTTP ${r.status}`);
  return r;
};

/* ---------------- toast / status ---------------- */
let toastTimer = null;
function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2200);
}
function setStatus() {
  $("stImage").textContent = S.root ? `${S.idx + 1} / ${S.images.length}   ${S.images[S.idx] || ""}` : "未打开数据集";
  $("stCount").textContent = S.boxes.length ? `框: ${S.boxes.length}` : "";
  $("stZoom").textContent = `缩放 ${Math.round(S.zoom * 100)}%`;
  $("stModel").textContent = `模型: ${(S.info && S.info.names && S.info.names[0]) || "Upside-down"}`;
}

/* ---------------- dataset loading ---------------- */
async function openRoot(root) {
  try {
    const r = await api(`/api/dataset?root=${encodeURIComponent(root)}`);
    const { info } = await r.json();
    S.root = info.root; S.info = info; S.images = info.images;
    S.names = info.names || {0: "Upside-down"};
    S.boxCache = {}; S.dirtyAt = {};
    S.idx = -1;
    renderList(); buildClassOptions();
    $("rootHint").hidden = true;
    if (S.images.length) goto(0, false);
    toast(`已打开 ${info.image_count} 张图 · 标注目录 ${info.labels_dir}`);
  } catch (e) {
    toast("打开失败: " + e.message);
  }
}

function markDirty() {
  S.dirty = true;
  S.dirtyAt[S.idx] = true;
  const d = $("imgItem" + S.idx);
  if (d) d.classList.add("isdirty");
}

function itemDot(i) {
  if (S.dirtyAt[i]) return "●";
  if (S.boxCache[i] !== undefined) return `\u00B7${S.boxCache[i].length}`;
  return "";
}

function renderList() {
  const el = $("imageList");
  el.innerHTML = "";
  S.images.forEach((name, i) => {
    const d = document.createElement("div");
    d.id = "imgItem" + i;
    d.className = "item" + (i === S.idx ? " active" : "");
    const n = document.createElement("span");
    n.textContent = name;
    const cnt = document.createElement("span");
    cnt.className = "n";
    cnt.textContent = itemDot(i);
    if (S.dirtyAt[i]) cnt.style.color = "#e0af68";
    d.append(n, cnt);
    d.onclick = () => goto(i);
    el.append(d);
  });
}

async function goto(i, savePrev = true) {
  if (i < 0 || i >= S.images.length || i === S.idx) return;
  if (savePrev && S.idx >= 0 && S.dirty) await saveNow();
  S.idx = i;
  await loadImage();
  renderList();
}

async function loadImage() {
  const name = S.images[S.idx];
  const r = await api(`/api/label?root=${encodeURIComponent(S.root)}&img=${encodeURIComponent(name)}`);
  S.boxes = (await r.json()).boxes || [];
  if (S.boxCache[S.idx] !== undefined && !S.dirtyAt[S.idx]) {
    S.boxes = S.boxCache[S.idx]; // reuse in-memory edits
  }
  S.boxCache[S.idx] = S.boxes;
  S.sel = -1; S.dirty = S.dirtyAt[S.idx] || false;
  renderBoxList(); syncEditor();
  const img = new Image();
  img.onload = () => { S.img = img; S.imgW = img.naturalWidth; S.imgH = img.naturalHeight; fitCanvas(); };
  img.src = `/api/image?root=${encodeURIComponent(S.root)}&img=${encodeURIComponent(name)}`;
  draw();
}

function fitCanvas() {
  const wrap = $("canvasWrap");
  cv.width = wrap.clientWidth; cv.height = wrap.clientHeight;
  if (!S.imgW) { draw(); return; }
  const s0 = Math.min(cv.width / S.imgW, cv.height / S.imgH) * 0.96;
  S.base = s0; S.zoom = 1; S.s = s0;
  S.ox = (cv.width - S.imgW * s0) / 2;
  S.oy = (cv.height - S.imgH * s0) / 2;
  setStatus(); draw();
}

/* ---------------- coordinate helpers ---------------- */
const toScreen = (x, y) => [S.ox + x * S.s, S.oy + y * S.s];
const toImg = (sx, sy) => [(sx - S.ox) / S.s, (sy - S.oy) / S.s];
const boxRect = (b) => [(b.cx - b.w / 2) * S.imgW, (b.cy - b.h / 2) * S.imgH,   // normalized -> image px
                        (b.cx + b.w / 2) * S.imgW, (b.cy + b.h / 2) * S.imgH];

/* ---------------- drawing ---------------- */
function draw() {
  ctx.clearRect(0, 0, cv.width, cv.height);
  if (!S.img) return;
  ctx.drawImage(S.img, S.ox, S.oy, S.imgW * S.s, S.imgH * S.s);
  S.boxes.forEach((b, i) => drawBox(b, i === S.sel));
  if (S.drag && S.drag.mode === "create" && S.drag.cur && S.drag.start) {
    const x1 = Math.min(S.drag.start[0], S.drag.cur[0]), y1 = Math.min(S.drag.start[1], S.drag.cur[1]);
    const x2 = Math.max(S.drag.start[0], S.drag.cur[0]), y2 = Math.max(S.drag.start[1], S.drag.cur[1]);
    const [sx1, sy1] = toScreen(x1, y1), [sx2, sy2] = toScreen(x2, y2);
    ctx.strokeStyle = "#e0af68";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 4]);
    ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);
    ctx.setLineDash([]);
  }
}

function drawBox(b, selected) {
  const [x1, y1, x2, y2] = boxRect(b);
  const [sx1, sy1] = toScreen(x1, y1), [sx2, sy2] = toScreen(x2, y2);
  const w = sx2 - sx1, h = sy2 - sy1;
  if (w <= 0 || h <= 0) return;
  const col = PALETTE[b.class % PALETTE.length] || "#fff";
  ctx.strokeStyle = col;
  ctx.lineWidth = selected ? 3 : 1.5;
  ctx.strokeRect(sx1, sy1, w, h);
  if (selected) {
    ctx.fillStyle = col;
    for (const [hx, hy] of [[sx1, sy1], [sx2, sy1], [sx1, sy2], [sx2, sy2]]) {
      ctx.fillRect(hx - 4, hy - 4, 8, 8);
    }
  }
  const txt = `${b.class} ${b.cx.toFixed(2)} ${b.cy.toFixed(2)} ${b.w.toFixed(2)} ${b.h.toFixed(2)}`;
  ctx.font = "11px monospace";
  const tw = ctx.measureText(txt).width;
  ctx.fillStyle = "rgba(20,20,25,0.75)";
  ctx.fillRect(sx1, sy1 - 16, tw + 8, 15);
  ctx.fillStyle = col;
  ctx.fillText(txt, sx1 + 4, sy1 - 4);
}

/* ---------------- hit testing / drag ---------------- */
function hitTest(sx, sy) {
  for (let i = S.boxes.length - 1; i >= 0; i--) {
    const b = S.boxes[i];
    const [x1, y1, x2, y2] = boxRect(b);
    const [sx1, sy1] = toScreen(x1, y1), [sx2, sy2] = toScreen(x2, y2);
    const hs = 6;
    if (sx >= sx1 - hs && sx <= sx1 + hs && sy >= sy1 - hs && sy <= sy1 + hs) return { i, mode: "resize", corner: 0 };
    if (sx >= sx2 - hs && sx <= sx2 + hs && sy >= sy1 - hs && sy <= sy1 + hs) return { i, mode: "resize", corner: 1 };
    if (sx >= sx1 - hs && sx <= sx1 + hs && sy >= sy2 - hs && sy <= sy2 + hs) return { i, mode: "resize", corner: 2 };
    if (sx >= sx2 - hs && sx <= sx2 + hs && sy >= sy2 - hs && sy <= sy2 + hs) return { i, mode: "resize", corner: 3 };
    if (sx >= sx1 && sx <= sx2 && sy >= sy1 && sy <= sy2) return { i, mode: "move" };
  }
  return null;
}

cv.addEventListener("mousedown", (e) => {
  if (e.button === 1 || S.space) {
    S.drag = { mode: "pan", x: e.clientX, y: e.clientY, ox: S.ox, oy: S.oy };
    cv.classList.add("panning");
    e.preventDefault();
    return;
  }
  if (e.button !== 0) return;
  const rect = cv.getBoundingClientRect();
  const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
  const hit = hitTest(sx, sy);
  if (hit) {
    S.sel = hit.i;
    const [ix, iy] = toImg(sx, sy);
    S.drag = { mode: hit.mode, i: hit.i, corner: hit.corner, start: [ix, iy],
               orig: { ...S.boxes[hit.i] } };
  } else {
    S.sel = -1;
    const [ix0, iy0] = toImg(sx, sy);
    S.drag = { mode: "create", start: [ix0, iy0], cur: [ix0, iy0] };
  }
  renderBoxList(); syncEditor(); draw();
});

cv.addEventListener("mousemove", (e) => {
  if (!S.drag) return;
  const rect = cv.getBoundingClientRect();
  const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
  const [ix, iy] = toImg(sx, sy);
  if (S.drag.mode === "pan") {
    S.ox = S.drag.ox + (sx - S.drag.x);
    S.oy = S.drag.oy + (sy - S.drag.y);
    draw(); return;
  }
  if (S.drag.mode === "create") {
    S.drag.cur = [Math.min(Math.max(ix, 0), S.imgW), Math.min(Math.max(iy, 0), S.imgH)];
    draw(); return;
  }
  const b = S.boxes[S.drag.i];
  if (!b) return;
  if (S.drag.mode === "move") {
    const dx = ix - S.drag.start[0], dy = iy - S.drag.start[1];
    const ncx = S.drag.orig.cx + dx / S.imgW, ncy = S.drag.orig.cy + dy / S.imgH;
    b.cx = Math.min(Math.max(ncx, b.w / 2), 1 - b.w / 2);
    b.cy = Math.min(Math.max(ncy, b.h / 2), 1 - b.h / 2);
  } else { // resize corner
    const o = S.drag.orig;
    let x1 = o.cx - o.w / 2, y1 = o.cy - o.h / 2, x2 = o.cx + o.w / 2, y2 = o.cy + o.h / 2;
    const px = ix / S.imgW, py = iy / S.imgH;
    if (S.drag.corner === 1 || S.drag.corner === 3) x2 = px; else x1 = px;   // right corners move x2, left move x1
    if (S.drag.corner >= 2) y2 = py; else y1 = py;                            // bottom corners move y2, top move y1
    const min = 0.01;
    const nx1 = Math.min(Math.max(x1, 0), 1), nx2 = Math.min(Math.max(Math.max(x2, nx1 + min), 0), 1);
    const ny1 = Math.min(Math.max(y1, 0), 1), ny2 = Math.min(Math.max(Math.max(y2, ny1 + min), 0), 1);
    b.cx = (nx1 + nx2) / 2; b.cy = (ny1 + ny2) / 2;
    b.w = nx2 - nx1; b.h = ny2 - ny1;
  }
  markDirty();
  syncEditor(); draw();
});

cv.addEventListener("mouseup", (e) => {
  if (!S.drag) return;
  if (S.drag.mode === "create") {
    const rect = cv.getBoundingClientRect();
    const [ix, iy] = toImg(e.clientX - rect.left, e.clientY - rect.top);
    const x1 = Math.min(Math.max(S.drag.start[0], 0), S.imgW), y1 = Math.min(Math.max(S.drag.start[1], 0), S.imgH);
    const x2 = Math.min(Math.max(ix, 0), S.imgW), y2 = Math.min(Math.max(iy, 0), S.imgH);
    if (Math.abs(x2 - x1) > 4 / S.s && Math.abs(y2 - y1) > 4 / S.s) {
      S.boxes.push({ class: 0, cx: (x1 + x2) / 2 / S.imgW, cy: (y1 + y2) / 2 / S.imgH,
                     w: Math.abs(x2 - x1) / S.imgW, h: Math.abs(y2 - y1) / S.imgH });
      S.sel = S.boxes.length - 1;
      markDirty();
    }
  }
  S.drag = null;
  cv.classList.remove("panning");
  renderBoxList(); syncEditor(); draw();
});

cv.addEventListener("wheel", (e) => {
  e.preventDefault();
  const rect = cv.getBoundingClientRect();
  const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
  const f = Math.exp(-e.deltaY * 0.0015);
  const nz = Math.min(Math.max(S.zoom * f, 0.1), 16);
  const ns = S.base * nz;
  const ix = (sx - S.ox) / S.s, iy = (sy - S.oy) / S.s;
  S.ox = sx - ix * ns; S.oy = sy - iy * ns;
  S.s = ns; S.zoom = nz;
  setStatus(); draw();
}, { passive: false });

/* ---------------- keyboard ---------------- */
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  if (e.key === "ArrowRight" || e.key === "d") { if (S.idx >= 0) goto(Math.min(S.idx + 1, S.images.length - 1)); }
  else if (e.key === "ArrowLeft" || e.key === "a") { if (S.idx >= 0) goto(Math.max(S.idx - 1, 0)); }
  else if (e.key === "Delete" || e.key === "Backspace") { if (S.sel >= 0) { S.boxes.splice(S.sel, 1); S.sel = -1; markDirty(); renderBoxList(); syncEditor(); draw(); } }
  else if (e.key === "Escape") { S.sel = -1; renderBoxList(); syncEditor(); draw(); }
  else if (e.key === " ") { e.preventDefault(); S.space = true; }
  else if (e.key === "+" || e.key === "=") zoomBy(1.2);
  else if (e.key === "-") zoomBy(1 / 1.2);
  else if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); saveNow(); }
  else if (e.key === "q") { if (S.idx >= 0) goto(S.idx); } // reload current image
});
document.addEventListener("keyup", (e) => { if (e.key === " ") S.space = false; });

function zoomBy(f) {
  const rect = cv.getBoundingClientRect();
  const sx = rect.width / 2, sy = rect.height / 2;
  const nz = Math.min(Math.max(S.zoom * f, 0.1), 16);
  const ns = S.base * nz;
  const ix = (sx - S.ox) / S.s, iy = (sy - S.oy) / S.s;
  S.ox = sx - ix * ns; S.oy = sy - iy * ns;
  S.s = ns; S.zoom = nz;
  setStatus(); draw();
}

/* ---------------- save / detect / export ---------------- */
async function saveNow() {
  if (!S.root || S.idx < 0) return;
  const name = S.images[S.idx];
  try {
    await api(`/api/label`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ root: S.root, img: name, boxes: S.boxes }),
    });
    S.dirty = false; S.dirtyAt[S.idx] = false;
    toast(`已保存 ${name}（${S.boxes.length} 框）`);
    renderList();
  } catch (e) { toast("保存失败: " + e.message); }
}

async function saveAll() {
  if (!S.root) return;
  let n = 0;
  for (const i of Object.keys(S.dirtyAt)) {
    if (!S.dirtyAt[i]) continue;
    const boxes = S.boxCache[i] || [];
    await api(`/api/label`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ root: S.root, img: S.images[i], boxes }),
    });
    S.dirtyAt[i] = false; n++;
  }
  if (S.idx >= 0 && S.dirty) { S.dirty = false; }
  toast(`已保存 ${n} 张图的修改`);
  renderList();
}

async function detectCurrent() {
  if (!S.root || S.idx < 0) return;
  toast("模型推理中…");
  try {
    const r = await api(`/api/detect`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ root: S.root, img: S.images[S.idx], conf: 0.25 }),
    });
    S.boxes = (await r.json()).boxes || [];
    S.boxCache[S.idx] = S.boxes;
    S.sel = -1; markDirty();
    renderBoxList(); syncEditor(); draw();
    toast(`模型给出 ${S.boxes.length} 框（未保存，可直接修改）`);
  } catch (e) { toast("检测失败: " + e.message); }
}

async function exportCvat() {
  if (!S.root) return;
  if (S.dirty) await saveNow();
  if (S.dirty) { toast("保存失败，未导出"); return; }
  const r = await fetch(`/api/export_cvat?root=${encodeURIComponent(S.root)}`);
  if (!r.ok) { toast("导出失败: " + ((await r.json().catch(() => ({}))).error || r.status)); return; }
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "cvat_import.zip";
  a.click();
  toast("已导出 cvat_import.zip（Ultralytics YOLO 结构，可导入 CVAT）");
}

async function importZip(file) {
  toast("解压导入中…");
  const r = await fetch("/api/import_zip", { method: "POST", body: file });
  if (!r.ok) { toast("导入失败: " + ((await r.json().catch(() => ({}))).error || r.status)); return; }
  const { root } = await r.json();
  await openRoot(root);
}

/* ---------------- panels ---------------- */
function buildClassOptions() {
  const sel = $("edClass");
  sel.innerHTML = "";
  for (const [cid, cname] of Object.entries(S.names)) {
    const o = document.createElement("option");
    o.value = cid; o.textContent = `${cid}: ${cname}`;
    sel.append(o);
  }
}

function renderBoxList() {
  const el = $("boxList");
  el.innerHTML = "";
  S.boxes.forEach((b, i) => {
    const d = document.createElement("div");
    d.className = "boxitem" + (i === S.sel ? " sel" : "");
    const col = PALETTE[b.class % PALETTE.length] || "#fff";
    d.innerHTML = `<span style="color:${col}">■</span>${b.class} · (${b.cx.toFixed(3)}, ${b.cy.toFixed(3)}, ${b.w.toFixed(3)}, ${b.h.toFixed(3)})`;
    d.onclick = () => { S.sel = i; renderBoxList(); syncEditor(); draw(); };
    el.append(d);
  });
  $("selTitle").textContent = S.sel >= 0 ? `选中框 #${S.sel + 1}` : "选中框（无）";
}

function syncEditor() {
  const b = S.boxes[S.sel];
  const ids = ["edClass", "edCx", "edCy", "edW", "edH", "btnDel"];
  ids.forEach((id) => { $(id).disabled = !b; });
  if (!b) {
    ["edCx", "edCy", "edW", "edH"].forEach((id) => { $(id).value = ""; });
    $("edClass").value = "";
    return;
  }
  $("edClass").value = b.class;
  $("edCx").value = b.cx.toFixed(6);
  $("edCy").value = b.cy.toFixed(6);
  $("edW").value = b.w.toFixed(6);
  $("edH").value = b.h.toFixed(6);
}

function onUserEdit(input, apply) {
  if (S.sel < 0) return;
  const val = parseFloat(input.value);
  if (isNaN(val)) return;
  const box = S.boxes[S.sel];
  const clamped = Math.min(Math.max(val, +input.min), +input.max);
  apply(box, clamped);
  markDirty();
  renderBoxList(); draw();
}
$("edClass").onchange = (e) => { if (S.sel >= 0 && e.target.value !== "") { S.boxes[S.sel].class = +e.target.value; markDirty(); renderBoxList(); draw(); } };
$("edCx").oninput = (e) => onUserEdit(e.target, (b, v) => { b.cx = v; });
$("edCy").oninput = (e) => onUserEdit(e.target, (b, v) => { b.cy = v; });
$("edW").oninput = (e) => onUserEdit(e.target, (b, v) => { b.w = Math.max(v, 0.001); });
$("edH").oninput = (e) => onUserEdit(e.target, (b, v) => { b.h = Math.max(v, 0.001); });
$("btnDel").onclick = () => { if (S.sel >= 0) { S.boxes.splice(S.sel, 1); S.sel = -1; markDirty(); renderBoxList(); syncEditor(); draw(); } };

/* ---------------- topbar ---------------- */
$("btnOpen").onclick = () => { if ($("rootInput").value.trim()) openRoot($("rootInput").value.trim()); };
$("rootInput").addEventListener("keydown", (e) => { if (e.key === "Enter" && $("rootInput").value.trim()) openRoot($("rootInput").value.trim()); });
$("btnSave").onclick = saveNow;
$("btnSaveAll").onclick = saveAll;
$("btnDetect").onclick = detectCurrent;
$("btnExport").onclick = exportCvat;
$("btnImport").onclick = () => $("zipInput").click();
$("zipInput").onchange = (e) => { if (e.target.files[0]) importZip(e.target.files[0]); e.target.value = ""; };
$("btnStop").onclick = async () => {
  if (!confirm("停止服务？将退出标注服务进程（未保存的修改会先自动保存）。")) return;
  if (S.dirty) await saveNow();
  try { await fetch("/api/shutdown", { method: "POST" }); } catch (e) { /* server may close first */ }
  toast("服务已停止，可关闭此页面");
};

window.addEventListener("resize", () => { if (S.img) fitCanvas(); });
fitCanvas();
setStatus();

/* ---------------- boot: ?root= auto-open ---------------- */
(async function boot() {
  const params = new URLSearchParams(location.search);
  const r = params.get("root");
  if (r) {
    $("rootInput").value = r;
    await openRoot(r);
  }
  if (params.get("selftest") === "1") runSelfTest();
})();

/* ---------------- synthetic-event self test (?selftest=1) ---------------- */
function waitFor(cond, ms) {
  return new Promise((res, rej) => {
    const t0 = Date.now();
    const iv = setInterval(() => {
      if (cond()) { clearInterval(iv); res(); }
      else if (Date.now() - t0 > ms) { clearInterval(iv); rej(new Error("timeout")); }
    }, 100);
  });
}

async function runSelfTest() {
  const rep = [];
  const ok = (name, cond, extra = "") => rep.push(`${cond ? "PASS" : "FAIL"} ${name} ${extra}`);
  try {
    await waitFor(() => S.img && S.imgW > 0, 8000);
    ok("load image", !!(S.img && S.imgW > 0), `${S.imgW}x${S.imgH} boxes=${S.boxes.length}`);
    const rect = cv.getBoundingClientRect();
    const fire = (type, x, y) => cv.dispatchEvent(new MouseEvent(type, {
      bubbles: true, cancelable: true, clientX: rect.left + x, clientY: rect.top + y,
      button: 0, buttons: 1,
    }));
    const n0 = S.boxes.length;
    const W = cv.width, H = cv.height;
    fire("mousedown", W * 0.30, H * 0.30);
    fire("mousemove", W * 0.50, H * 0.55);
    fire("mouseup", W * 0.50, H * 0.55);
    ok("create box", S.boxes.length === n0 + 1, `n ${n0} -> ${S.boxes.length}`);
    const b = S.boxes[S.boxes.length - 1];
    ok("coords normalized", b.cx > 0 && b.cx < 1 && b.w > 0, JSON.stringify([b.cx, b.cy, b.w, b.h].map(v => +v.toFixed(4))));
    const cxs = S.ox + b.cx * S.imgW * S.s, cys = S.oy + b.cy * S.imgH * S.s;
    const cx0 = b.cx;
    fire("mousedown", cxs, cys);
    fire("mousemove", cxs + 30, cys + 15);
    fire("mouseup", cxs + 30, cys + 15);
    ok("move box", Math.abs(b.cx - cx0) > 0.001, `dcx=${(b.cx - cx0).toFixed(4)}`);
    const w0 = b.w;
    const hxs = S.ox + (b.cx - b.w / 2) * S.imgW * S.s, hys = S.oy + (b.cy - b.h / 2) * S.imgH * S.s;
    fire("mousedown", hxs, hys);
    fire("mousemove", hxs - 30, hys - 20);
    fire("mouseup", hxs - 30, hys - 20);
    ok("resize box", b.w > w0, `w ${w0.toFixed(4)} -> ${b.w.toFixed(4)}`);
    S.sel = 0; syncEditor();
    const e = $("edCx");
    e.value = "0.5";
    e.dispatchEvent(new Event("input", { bubbles: true }));
    ok("panel edit", Math.abs(S.boxes[0].cx - 0.5) < 1e-6, `cx=${S.boxes[0].cx}`);
    S.sel = 0;
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Delete", bubbles: true }));
    ok("delete box", S.boxes.length === n0, `n=${S.boxes.length}`);
    S.boxes.push({ class: 0, cx: 0.5, cy: 0.5, w: 0.1, h: 0.1 });
    renderBoxList();
    const items = document.querySelectorAll(".boxitem");
    items[items.length - 1].dispatchEvent(new MouseEvent("click", { bubbles: true }));
    ok("select via panel", S.sel === S.boxes.length - 1, `sel=${S.sel}`);
    S.boxes.pop();
    if (S.dirty) await loadImage(); // discard selftest edits
  } catch (err) {
    rep.push("EXCEPTION " + (err && err.message));
  }
  const div = document.createElement("div");
  div.id = "selftest-report";
  div.textContent = rep.join("\n");
  document.body.append(div);
  document.title = "SELFTEST-DONE";
}