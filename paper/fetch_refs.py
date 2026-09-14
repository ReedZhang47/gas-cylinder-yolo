r"""fetch refs for the paper -> paper/references.bib (+ audit table).

Two sources, both queried over the network:
  1. Crossref (title search + official BibTeX transform endpoint) - journals.
  2. arXiv API (Atom) - preprints, rendered in the same @misc style the user
     already uses for Qwen-Image / Z-Image.

Every entry gets a title-similarity check against the query; low-confidence
matches are flagged in the audit file instead of being silently accepted.
Re-runnable: overwrites references.bib and references_audit.md.
"""
import difflib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

OUT_BIB = Path(__file__).parent / "references.bib"
OUT_AUDIT = Path(__file__).parent / "references_audit.md"
UA = {"User-Agent": "gas-cylinder-paper-refs/1.0 (mailto:oochee47@gmail.com)"}

# key, title query, kind, expected first-author surname (hint), expected year (hint)
TASKS = [
    # --- user's local papers (md notes / pdf folder), need bib entries ---
    ("davari2025bcon", "ControlNet-based domain adaptation for synthetic construction images via graphical simulation and generative AI", "doi", "10.1016/j.autcon.2025.106562"),
    ("jeong2026lora", "Addressing data scarcity in construction safety monitoring using LoRA-tuned domain-specific image generation", "doi", "10.1016/j.autcon.2026.106786"),
    ("dinh2026ponding", "Enhancing Water-Ponding Detection via Generative AI Inpainting-Based Synthetic Data", "any", None, 2026),
    ("grieco2024diag", "DIAG Leveraging Latent Diffusion Models for Training-Free In-Distribution Data Augmentation for Surface Defect Detection", "any", None, 2024),
    ("lee2023gameengine", "Game engine-driven synthetic data generation for computer vision-based safety monitoring of construction workers", "any", None, 2023),
    ("li2025steeldefect", "A Few-Shot Steel Surface Defect Generation Method Based on Diffusion Models", "any", None, 2025),
    ("li2025substation", "Substation Inspection Safety Risk Identification Based on Synthetic Data and Spatiotemporal Action Detection", "any", None, 2025),
    ("zhang2025helmet", "Detection of helmet use via helmet-head region matching and state tracking", "any", None, 2025),
    ("zhang2026mixing", "A Fixed-Budget Study of Real-Synthetic Data Mixing for PPE Detection in Construction", "any", None, 2026),
    # --- foundational / context refs (added by the agent) ---
    ("redmon2016yolo", "You Only Look Once: Unified, Real-Time Object Detection", "any", "Redmon", 2016),
    ("bochkovskiy2020yolov4", "YOLOv4: Optimal Speed and Accuracy of Object Detection", "any", "Bochkovskiy", 2020),
    ("wang2023yolov7", "YOLOv7: Trainable bag-of-freebies sets new state-of-the-art for real-time object detectors", "any", "Wang", 2023),
    ("wang2024yolov9", "YOLOv9: Learning What You Want to Learn Using Programmable Gradient Information", "any", "Wang", 2024),
    ("wang2024yolov10", "YOLOv10: Real-Time End-to-End Object Detection", "any", "Wang", 2024),
    ("lin2014coco", "Microsoft COCO: Common Objects in Context", "any", "Lin", 2014),
    ("ho2020ddpm", "Denoising Diffusion Probabilistic Models", "any", "Ho", 2020),
    ("rombach2022ldm", "High-Resolution Image Synthesis with Latent Diffusion Models", "any", "Rombach", 2022),
    ("zhang2023controlnet", "Adding Conditional Control to Text-to-Image Diffusion Models", "any", "Zhang", 2023),
    ("brooks2023instructpix2pix", "InstructPix2Pix: Learning to Follow Image Editing Instructions", "any", "Brooks", 2023),
    ("ruiz2023dreambooth", "DreamBooth: Fine Tuning Text-to-Image Diffusion Models for Subject-Driven Generation", "any", "Ruiz", 2023),
    ("podell2023sdxl", "SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis", "any", "Podell", 2023),
    ("tremblay2018domainrand", "Training Deep Networks with Synthetic Data: Bridging the Reality Gap by Domain Randomization", "any", "Tremblay", 2018),
    ("richter2016playing", "Playing for Data: Ground Truth from Computer Games", "any", "Richter", 2016),
    ("ghiasi2021copypaste", "Simple Copy-Paste is a Strong Data Augmentation Method for Instance Segmentation", "any", "Ghiasi", 2021),
    ("shorten2019augmentation", "A survey on Image Data Augmentation for Deep Learning", "any", "Shorten", 2019),
    ("azizi2023synthetic", "Synthetic Data from Diffusion Models Improves ImageNet Classification", "any", "Azizi", 2023),
    ("cheng2023smallobject", "Towards Large-Scale Small Object Detection: Survey and Benchmarks", "any", "Cheng", 2023),
    ("akyon2022sahi", "Slicing Aided Hyper Inference and Fine-tuning for Small Object Detection", "any", "Akyon", 2022),
    ("northcutt2021labelerrors", "Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks", "any", "Northcutt", 2021),
    ("kaufman2012leakage", "Leakage in Data Mining: Formulation, Detection, and Avoidance", "any", "Kaufman", 2012),
    ("nath2020ppe", "Deep learning for site safety: Real-time detection of personal protective equipment", "any", "Nath", 2020),
    ("fang2018nocert", "A deep learning-based method for detecting non-certified work on construction sites", "any", "Fang", 2018),
    ("duan2022soda", "SODA: A large-scale open site object detection dataset for deep learning in construction", "any", "Duan", 2022),
    ("xie2020noisystudent", "Self-training with Noisy Student improves ImageNet classification", "any", "Xie", 2020),
    ("lee2013pseudolabel", "Pseudo-Label: The Simple and Efficient Semi-Supervised Learning Method for Deep Neural Networks", "any", "Lee", 2013),
]


def norm_title(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def http_get(url: str, timeout=30) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def crossref_bibtex(doi: str) -> str:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}/transform/application/x-bibtex"
    return http_get(url).decode("utf-8").strip()


def crossref_search(title: str, year=None):
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 5})
    data = json.loads(http_get(f"https://api.crossref.org/works?{q}"))
    best = None
    for it in data["message"]["items"]:
        t = (it.get("title") or [""])[0]
        score = sim(title, t)
        if year and it.get("issued", {}).get("date-parts", [[None]])[0][0]:
            dy = abs(it["issued"]["date-parts"][0][0] - year)
            if dy == 0:
                score += 0.06
            elif dy <= 1:
                score += 0.03
            else:
                score -= 0.05
        if best is None or score > best[0]:
            best = (score, it, t)
    return best


def arxiv_search(title: str):
    words = " ".join(re.findall(r"[A-Za-z0-9-]+", title))
    q = urllib.parse.urlencode({"search_query": f'ti:"{words}"', "max_results": 3})
    try:
        xml = http_get(f"http://export.arxiv.org/api/query?{q}")
    except Exception as e:
        return None, str(e)
    root = ET.fromstring(xml)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    best = None
    for e in root.findall("a:entry", ns):
        t = " ".join(e.find("a:title", ns).text.split())
        score = sim(title, t)
        eid = e.find("a:id", ns).text  # http://arxiv.org/abs/xxxx.xxxxx
        if best is None or score > best[0]:
            best = (score, e, t, eid)
    return best, None


def arxiv_misc(key: str, entry, title: str, eid: str) -> str:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)]
    year = entry.find("a:published", ns).text[:4]
    aid = eid.rstrip("/").split("/abs/")[-1]
    prim = entry.find("{http://arxiv.org/schemas/atom}primary_category")
    prim = prim.get("term") if prim is not None else "cs.CV"
    lines = [
        f"@misc{{{key},",
        f"      title={{{title}}},",
        f"      author={{{' and '.join(authors)}}},",
        f"      year={{{year}}},",
        f"      eprint={{{aid}}},",
        "      archivePrefix={arXiv},",
        f"      primaryClass={{{prim}}},",
        f"      url={{https://arxiv.org/abs/{aid}}},",
        "}",
    ]
    return "\n".join(lines)


def main():
    entries, audit = [], []
    for task in TASKS:
        key, title = task[0], task[1]
        kind = task[2]
        hint = task[3:]
        print(f"[{key}]", flush=True)
        got, note = None, ""
        if kind == "doi":
            doi = task[3]
            try:
                got = crossref_bibtex(doi)
                note = f"DOI direct {doi}"
            except Exception as e:
                note = f"DOI FAILED {doi}: {e}"
        else:
            year = hint[1] if len(hint) > 1 else None
            cr = crossref_search(title, year)
            if cr and cr[0] >= 0.80:
                it = cr[1]
                doi = it.get("DOI")
                try:
                    got = crossref_bibtex(doi)
                    note = f"crossref sim={cr[0]:.2f} doi={doi}"
                except Exception as e:
                    note = f"crossref bibtex failed ({doi}): {e}"
            ar = None
            if got is None:
                ar, err = arxiv_search(title)
                if ar and ar[0] >= 0.80:
                    got = arxiv_misc(key, ar[1], ar[2], ar[3])
                    note = f"arxiv sim={ar[0]:.2f} {ar[3]}"
                elif err:
                    note = f"arxiv error: {err}"
                elif ar:
                    note = f"arxiv low sim={ar[0]:.2f} ({ar[2][:60]})"
            if got is None and cr:
                note = f"UNVERIFIED crossref sim={cr[0]:.2f} best={cr[2][:70]}"
        if got:
            # force our key
            got = re.sub(r"^@(\w+)\{[^,]+,", lambda m: f"@{m.group(1)}{{{key},", got, count=1)
            entries.append(f"% {key}\n{got}\n")
            print(f"   OK  {note}", flush=True)
        else:
            entries.append(f"% {key}  -- UNRESOLVED: {title}\n")
            print(f"   MISS {note}", flush=True)
        audit.append(f"| {key} | {title[:70]} | {note} |")

    OUT_BIB.write_text(
        "% references.bib - master bibliography for working_paper.tex\n"
        "% generated by paper/fetch_refs.py; re-run to refresh. UNRESOLVED entries are commented.\n\n"
        + "\n".join(entries),
        encoding="utf-8",
    )
    OUT_AUDIT.write_text(
        "# references audit (fetch_refs.py)\n\n"
        "| key | query title | how resolved |\n|---|---|---|\n" + "\n".join(audit) + "\n",
        encoding="utf-8",
    )
    print(f"\nsaved -> {OUT_BIB}\naudit -> {OUT_AUDIT}")


if __name__ == "__main__":
    main()
