r"""local YOLO detection annotation GUI server (stdlib only).

Serves a browser GUI at http://127.0.0.1:<port> for viewing/editing flatted YOLO
detection labels (class cx cy w h, normalized), with import (folder/zip) and
export (CVAT-importable zip). Optional per-image re-detection with a trained
weight.

Run:
  & D:\yolo\.venv\Scripts\python.exe D:\yolo\annotator\annotator.py [--port 8085] [--model <best.pt>]
"""
import argparse
import io
import json
import mimetypes
import os
import re
import tempfile
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
IMAGES_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
LABEL_RE = re.compile(r"^(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$")
DEFAULT_NAMES = {0: "Upside-down"}
MODEL_ARG = None
_MODEL = None
_MODEL_LOCK = threading.Lock()
SRV = None

MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".bmp": "image/bmp", ".tif": "image/tiff", ".tiff": "image/tiff",
}


def get_model():
    global _MODEL
    if _MODEL is None:
        with _MODEL_LOCK:
            if _MODEL is None:
                from ultralytics import YOLO
                _MODEL = YOLO(MODEL_ARG)
    return _MODEL


def names_for(root: str) -> dict:
    """Parse names from root/data.yaml (naive; falls back to defaults)."""
    p = Path(root) / "data.yaml"
    if not p.exists():
        return dict(DEFAULT_NAMES)
    names = {}
    try:
        import yaml
        data = yaml.safe_load(p.read_text(encoding="utf-8-sig")) or {}
        nm = data.get("names") or {}
        for k, v in nm.items():
            names[int(k)] = str(v)
    except Exception:
        in_names = False
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            if re.match(r"^\s*names\s*:", line):
                in_names = True
                continue
            if in_names and re.match(r"^\s+\S", line):
                m = re.match(r"^\s*(\d+)\s*:\s*(.+?)\s*$", line)
                if m:
                    names[int(m.group(1))] = m.group(2)
            elif in_names and re.match(r"^\S", line):
                break
    return names if names else dict(DEFAULT_NAMES)


def find_dirs(root: Path) -> tuple[Path, Path]:
    """Return (images_dir, labels_dir). Supports images/+labels/ flat layout and
    CVAT/ultralytics layout (images/<subset> + labels/<subset>, or <subset>/images)."""
    root = Path(root)
    img_dir, subset = None, None
    if (root / "images").is_dir():
        img_dir = root / "images"
        for s in ("train", "val", "test"):
            if (root / "images" / s).is_dir():
                img_dir, subset = root / "images" / s, s
                break
    else:
        for s in ("train", "val", "test"):
            if (root / s / "images").is_dir():
                img_dir, subset = root / s / "images", s
                break
    if img_dir is None:
        img_dir = root if any(f.is_file() for f in root.iterdir()) else root
    lab = None
    if subset and (root / "labels" / subset).is_dir():
        lab = root / "labels" / subset
    elif (root / "labels").is_dir():
        lab = root / "labels"
    if lab is None and (img_dir.parent / "labels").is_dir():
        lab = img_dir.parent / "labels"
    if lab is None:
        lab = img_dir
    return img_dir, lab


def scan_dataset(root: str) -> dict:
    img_dir, lab_dir = find_dirs(Path(root))
    images = []
    for f in sorted(img_dir.iterdir()):
        if f.suffix.lower() in IMAGES_EXTS:
            images.append(f.name)
    labels = {}
    if lab_dir.is_dir():
        for f in lab_dir.iterdir():
            if f.suffix.lower() == ".txt":
                labels[f.stem] = f
    return {"root": root, "images_dir": str(img_dir), "labels_dir": str(lab_dir),
            "image_count": len(images), "images": images, "names": names_for(root)}


def label_path_for(lab_dir: Path, img_name: str) -> Path:
    return lab_dir / (Path(img_name).stem + ".txt")


def read_label(lab_dir: Path, img_name: str) -> list[dict]:
    p = label_path_for(lab_dir, img_name)
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = LABEL_RE.match(line.strip())
            if not m:
                continue
            cid, cx, cy, w, h = (int(m.group(1)), float(m.group(2)), float(m.group(3)),
                                 float(m.group(4)), float(m.group(5)))
            out.append({"class": cid, "cx": cx, "cy": cy, "w": w, "h": h})
    return out


def write_label(lab_dir: Path, img_name: str, boxes: list[dict]) -> None:
    lab_dir.mkdir(parents=True, exist_ok=True)
    p = label_path_for(lab_dir, img_name)
    lines = [f"{b['class']} {b['cx']:.6f} {b['cy']:.6f} {b['w']:.6f} {b['h']:.6f}" for b in boxes]
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def validate_box(b: dict) -> dict | None:
    try:
        cid = int(b.get("class", 0))
        cx, cy, w, h = (float(b["cx"]), float(b["cy"]), float(b["w"]), float(b["h"]))
    except Exception:
        return None
    if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1 and 0 < h <= 1):
        return None
    return {"class": cid, "cx": cx, "cy": cy, "w": w, "h": h}


def export_cvat_zip(root: str) -> bytes:
    """Assemble the CVAT ultralytics-yolo structure: data.yaml, train.txt,
    images/train/*, labels/train/* (empty txt for label-less images)."""
    info = scan_dataset(root)
    img_dir = Path(info["images_dir"])
    lab_dir = Path(info["labels_dir"])
    names = info["names"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        yaml_text = "path: .\ntrain: train.txt\nnc: {}\nnames:\n".format(len(names))
        for cid, cname in sorted(names.items()):
            yaml_text += f"  {cid}: {cname}\n"
        z.writestr("data.yaml", yaml_text)
        list_lines = []
        for name in info["images"]:
            img = img_dir / name
            z.write(img, f"images/train/{name}")
            lab = label_path_for(lab_dir, name)
            lab_text = lab.read_text(encoding="utf-8") if lab.exists() else ""
            z.writestr(f"labels/train/{Path(name).stem}.txt", lab_text)
            list_lines.append(f"images/train/{name}")
        z.writestr("train.txt", "\n".join(list_lines) + "\n")
    return buf.getvalue()


def extract_import_zip(data: bytes) -> str:
    """Unzip an uploaded dataset archive into a temp dir; return the dataset root."""
    tmp = Path(tempfile.mkdtemp(prefix="annotator_import_", dir=str(HERE)))
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(tmp)
    # locate dataset root: dir containing data.yaml / images / image files, ≤2 levels deep
    def has_images(d: Path) -> bool:
        return any(f.suffix.lower() in IMAGES_EXTS for f in d.iterdir())
    root = tmp
    for cand in tmp.iterdir():
        if cand.is_dir() and (has_images(cand) or (cand / "images").is_dir()):
            root = cand
            break
    return str(root)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    # -- helpers ---------------------------------------------------------
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _bytes(self, body, ctype, filename=None, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _contained(self, root: str, path: str) -> Path | None:
        try:
            rp = os.path.realpath(path)
            rr = os.path.realpath(root)
            if os.path.commonpath([rp, rr]) == rr:
                return Path(rp)
        except Exception:
            pass
        return None

    def _img_path(self, q) -> tuple[Path | None, Path | None]:
        root = q.get("root", "")
        name = q.get("img", "")
        if not root or not name or "/" in name or "\\" in name or ".." in name:
            return None, None
        info = scan_dataset(root)
        img = self._contained(root, str(Path(info["images_dir"]) / name))
        return img, Path(info["labels_dir"])

    # -- routes ----------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        q = {}
        if "?" in self.path:
            q = dict(pair.split("=", 1) for pair in self.path.split("?", 1)[1].split("&") if "=" in pair)
        from urllib.parse import unquote
        q = {k: unquote(v) for k, v in q.items()}

        if path in ("/", "/index.html"):
            self._bytes((STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/app.js":
            self._bytes((STATIC / "app.js").read_bytes(), "text/javascript; charset=utf-8")
            return
        if path == "/style.css":
            self._bytes((STATIC / "style.css").read_bytes(), "text/css; charset=utf-8")
            return
        if path == "/api/dataset":
            try:
                info = scan_dataset(q["root"])
            except Exception as e:
                self._json({"error": str(e)}, 400)
                return
            self._json({"info": info})
            return
        if path == "/api/roots":
            base = q.get("base", "D:/")
            base = Path(base)
            found = []
            if base.is_dir():
                for d in base.iterdir():
                    if d.is_dir() and any(f.suffix.lower() in IMAGES_EXTS for f in d.iterdir()):
                        found.append(str(d))
                    elif d.is_dir() and (d / "images").is_dir():
                        found.append(str(d))
            self._json({"base": str(base), "roots": sorted(found)[:200]})
            return
        if path == "/api/image":
            img, lab_dir = self._img_path(q)
            if img is None or not img.is_file():
                self._json({"error": "image not found"}, 404)
                return
            ctype = MIME.get(img.suffix.lower(), "application/octet-stream")
            self._bytes(img.read_bytes(), ctype)
            return
        if path == "/api/label":
            img, lab_dir = self._img_path(q)
            if img is None:
                self._json({"error": "bad params"}, 400)
                return
            self._json({"boxes": read_label(lab_dir, img.name)})
            return
        if path == "/api/export_cvat":
            try:
                buf = export_cvat_zip(q["root"])
            except Exception as e:
                self._json({"error": str(e)}, 400)
                return
            self._bytes(buf, "application/zip", filename="cvat_import.zip")
            return
        self._json({"error": f"no such route {path}"}, 404)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        body = self._read_body()
        if path == "/api/shutdown":
            self._json({"ok": True, "msg": "server is shutting down"})
            if SRV is not None:
                threading.Timer(0.3, SRV.shutdown).start()
            return
        if path == "/api/label":
            data = json.loads(body)
            root, name = data.get("root", ""), data.get("img", "")
            if "/" in name or "\\" in name or ".." in name:
                self._json({"error": "bad name"}, 400)
                return
            info = scan_dataset(root)
            lab_dir = Path(info["labels_dir"])
            if not self._contained(root, str(lab_dir)):
                self._json({"error": "outside root"}, 403)
                return
            boxes = []
            for raw in data.get("boxes", []):
                b = validate_box(raw)
                if b is None:
                    self._json({"error": f"invalid box {raw}"}, 400)
                    return
                boxes.append(b)
            try:
                write_label(lab_dir, name, boxes)
            except Exception as e:
                self._json({"error": str(e)}, 400)
                return
            self._json({"ok": True, "saved": len(boxes), "path": str(label_path_for(lab_dir, name))})
            return
        if path == "/api/detect":
            data = json.loads(body)
            img, _ = self._img_path(data)
            if img is None or not img.is_file():
                self._json({"error": "image not found"}, 404)
                return
            try:
                res = get_model().predict(str(img), conf=data.get("conf", 0.25),
                                          verbose=False)[0]
                boxes = []
                if res.boxes is not None and len(res.boxes):
                    cls = res.boxes.cls.cpu().numpy().astype(int)
                    xywhn = res.boxes.xywhn.cpu().numpy()
                    for c, (cx, cy, w, h) in zip(cls, xywhn):
                        boxes.append({"class": int(c), "cx": float(cx), "cy": float(cy),
                                      "w": float(w), "h": float(h)})
                self._json({"boxes": boxes})
            except Exception as e:
                self._json({"error": f"detect failed: {e}"}, 500)
            return
        if path == "/api/import_zip":
            try:
                root = extract_import_zip(body)
                info = scan_dataset(root)
                self._json({"root": root, "info": info})
            except Exception as e:
                self._json({"error": f"import failed: {e}"}, 400)
            return
        self._json({"error": f"no such route {path}"}, 404)


def main():
    global MODEL_ARG, SRV
    ap = argparse.ArgumentParser(description="local YOLO detection annotator GUI")
    ap.add_argument("--port", type=int, default=8085)
    ap.add_argument("--model", default=r"D:\yolo\runs\detect\first500\yolo11m\weights\best.pt")
    args = ap.parse_args()
    MODEL_ARG = args.model
    SRV = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"annotator GUI: http://127.0.0.1:{args.port}  (model: {MODEL_ARG})", flush=True)
    SRV.serve_forever()
    print("server stopped", flush=True)


if __name__ == "__main__":
    main()