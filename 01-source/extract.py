"""Թվայնացնել նշումներով PDF-ի ուրվագծերը։ Գործարկում՝ python extract.py ԱՂԲՅՈՒՐ.pdf։"""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import pdfplumber
from pypdf import PdfReader


DEST = Path(__file__).resolve().parent
SOURCE = Path(sys.argv[1])
if SOURCE.name != "Հավելյալ նշումներ արված բնակարանի հատակագիծ.pdf":
    raise ValueError("Ընտրեք առաջադրանքով սահմանված ծանոթագրություններով PDF-ը։")

ROOMS = [
    ("bath", "№5 բաղնիք", 2.91),
    ("living", "№4 հյուրասենյակ", 25.44),
    ("bed_w", "№3 ննջասենյակ", 13.55),
    ("bed_e", "№2 ննջասենյակ", 15.54),
    ("balcony", "Բ/Պ բաց պատշգամբ", 31.24),
    ("kitchen", "№1 միջանցք-խոհանոց", 8.71),
    ("wc", "№2 փոքր զուգարան", 0.80),
    ("vestibule", "№1 ընդհանուր նախամուտք", 8.84),
]

with pdfplumber.open(SOURCE) as document:
    page = document.pages[0]
    curves = [[tuple(point) for point in c["pts"]] for c in page.curves]
    lines = [line["pts"] for line in page.lines]

reader = PdfReader(SOURCE)
original = reader.pages[0]
annotations = [ref.get_object() for ref in original["/Annots"]]
scale = (curves[1][0][0] - curves[1][5][0]) / 5.92
origin = curves[1][5]


def world(point):
    return [round((point[0] - origin[0]) / scale, 9),
            round((origin[1] - point[1]) / scale, 9)]


def area(points):
    edges = zip(points, points[1:] + points[:1])
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in edges)) / 2


def arrow(index):
    vector = annotations[index]["/L"]
    return [(float(vector[2]), float(original.mediabox.height) - float(vector[3]))]


def poly(pts):
    return [world(p) for p in pts]


circle = annotations[9]["/Rect"]
circle_center = ((float(circle[0]) + float(circle[2])) / 2,
                 float(original.mediabox.height) - (float(circle[1]) + float(circle[3])) / 2)
features = {
    "outer_boundary": curves[8][:-1],
    "column": [(198.68, 286.12), (207.8, 286.12), (207.68, 277.72), (198.56, 277.84)],
    "bearing_edge": [origin, curves[1][0]],
    "stack_marker": [circle_center],
    "entry1": [(407.84, 500.44)], "entry2": [(377.3, 645)], "entry3": [(378, 532)],
    "arrow1": arrow(4), "arrow2": arrow(2), "arrow3": arrow(8),
}
rooms = {}
for i, (key, name, stated) in enumerate(ROOMS):
    points = poly(curves[i][:-1])
    rooms[key] = {"name": name, "stated_area": stated, "points": points, "area": area(points)}

result = {
    "version": "R0", "units": "m", "source": SOURCE.name,
    "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "origin": {"description": "Հյուրասենյակի 5.92 մ եզրի ձախ ծայր, x աջ, y վեր ըստ թերթի։ ±0.000՝ ընդունված պատրաստի հատակ։",
               "pdf_pt_top_left": origin, "pdf_pt_per_m": scale,
               "pdf_metadata_m_per_pt": float(original["/VP"][0]["/Measure"]["/X"][0]["/C"])},
    "status": "PDF-ի վեկտորային թվայնացում, տեղում չչափագրված",
    "rooms": rooms,
    "features": {k: poly(pts) for k, pts in features.items()},
    "lines": [{"id": i, "points": poly(lines[i])}
              for i in [*range(0, 19), *range(33, 51), 59]],
    "notes": {
        "doors": "entry1..3՝ պատին պրոյեկտած մոտավոր կենտրոններ։ Կարմիր սլաքների իրական ծայրերը՝ arrow1..3։ Բացման ուղղությունները չեն հաստատվել։",
        "stack": "Դեղին նշանի կենտրոնը՝ էջի կոորդինատ։ Կանգնակի խողովակի առանցքն ու միացման կետը չափագրել։",
        "scale": "Համասեռ մասշտաբ՝ 258.12 PDF կետ / 5.92 մ։ Ուրվագծերը պահպանում են սկզբնական շեղումները։",
    },
}
(DEST / "base.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

with (DEST / "edges.csv").open("w", newline="", encoding="utf-8-sig") as out:
    w = csv.writer(out)
    w.writerow(["Տարածք", "Նշված մակերես, մ²", "Գագաթ A", "Գագաթ B", "X_A, մ", "Y_A, մ",
                "X_B, մ", "Y_B, մ", "Կող, մ", "Կող, մմ", "Աղբյուր"])
    for room in rooms.values():
        pts = room["points"]
        for i, a in enumerate(pts):
            j = (i + 1) % len(pts)
            b = pts[j]
            w.writerow([room["name"], room["stated_area"], i + 1, j + 1,
                        *a, *b, f"{math.dist(a,b):.6f}", round(math.dist(a,b) * 1000),
                        "PDF-ի վեկտոր, տեղում ճշտել"])
