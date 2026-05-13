"""Regenerate mockups 2 and 3 with stronger cover-fidelity instructions."""
import json
import os
import sys
import time
import urllib.request

API_KEY = "087ade3410b23ca9b66ff1f62b4b8169"
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
QUERY_URL  = "https://api.kie.ai/api/v1/jobs/recordInfo"
COVER_URL  = "https://raw.githubusercontent.com/TCS-Andres/sowhatbook/main/images/book-cover.jpeg"
OUT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mockups")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

# Front-loaded fidelity contract. Same wording for both variations so the model
# locks the cover before composing the scene.
COVER_LOCK = (
    "STRICT REFERENCE-MATCHING TASK. The reference image is a real book cover that "
    "must be reproduced PIXEL-FAITHFULLY on the front of a hardcover book in the "
    "scene below. DO NOT recolor, restyle, redesign, or 'improve' anything on the "
    "cover. The cover layout and colors are: "
    "(1) Background = vibrant deep MAGENTA/PINK (hex roughly #B5208E), full bleed. "
    "(2) The word 'So' = large YELLOW italic serif character in the upper-left area. "
    "(3) The word 'What' = large PURE WHITE (not yellow, not cream — WHITE) italic "
    "serif in the lower-center, sitting below 'So'. "
    "(4) A white hand-drawn scribble ball of tangled loops sits to the right of 'So', "
    "with a single white arrow shooting out the upper-right. "
    "(5) The subtitle 'How to Stop Overthinking Your Wins & Losses and Build "
    "Unstoppable Momentum' appears INSIDE the scribble in small WHITE serif text, "
    "right-aligned, 5 short stacked lines. "
    "(6) The author line 'Dr. Meghna Dassani' is in PURE WHITE serif text, "
    "centered along the bottom of the cover. "
    "Every text element on the cover except 'So' is WHITE. Do not turn 'What', the "
    "subtitle, or the author name yellow. Now compose the following scene: "
)

SCENE_2 = (
    "Lifestyle photograph from a slight over-the-shoulder angle: a woman's hands "
    "(natural skin tone, neutral nude nail polish, anatomically correct — five "
    "fingers per hand, realistic proportions, no extra digits) holding the "
    "hardcover book upright in front of her so the full front cover faces the "
    "camera directly. The book is held by its lower edge, both thumbs visible on "
    "the front and fingers wrapping around behind. Background softly out of focus: "
    "an oatmeal-colored knit sweater sleeve, blurred morning window light from the "
    "left, a hint of a wooden table and a ceramic coffee mug in the deep "
    "background. Sharp focus on the book; shallow DOF elsewhere. Warm natural "
    "daylight, no harsh shadows. Editorial Instagram aesthetic — feels like a "
    "real reader's first-look photo, not a stock shot."
)

SCENE_3 = (
    "Top-down flat-lay photograph of the hardcover book lying flat on a creamy "
    "off-white linen surface. The book is tilted diagonally about 15 degrees "
    "off-vertical, occupying the center of the frame. Around it, elegantly "
    "arranged minimal props: a small terracotta-pot succulent with a single "
    "green leaf in the upper-right, a folded tan linen napkin tucked under one "
    "corner of the book, a ceramic mug of black coffee in the upper-left (faint "
    "steam), a pair of tortoiseshell reading glasses near the lower-left, and a "
    "brass pen lying diagonally near the lower-right. Soft natural morning light "
    "casting gentle shadows. Aesthetic editorial flat-lay — book is the hero."
)

VARIATIONS = [
    {"name": "mockup_2_lifestyle_hands", "aspect_ratio": "4:5", "prompt": COVER_LOCK + SCENE_2},
    {"name": "mockup_3_flatlay_desk",   "aspect_ratio": "1:1", "prompt": COVER_LOCK + SCENE_3},
]


def http_post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                  headers={"Authorization": f"Bearer {API_KEY}",
                                           "Content-Type": "application/json"},
                                  method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def http_get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/png,image/*,*/*"})
    with urllib.request.urlopen(req, timeout=180) as r:
        with open(path, "wb") as f:
            f.write(r.read())


def run(el):
    body = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": el["prompt"],
            "image_input": [COVER_URL],
            "aspect_ratio": el["aspect_ratio"],
            "resolution": "2K",
            "output_format": "png",
        },
    }
    r = http_post(CREATE_URL, body)
    if r.get("code") != 200:
        raise RuntimeError(f"submit failed: {r}")
    tid = r["data"]["taskId"]
    print(f"  submitted {el['name']}  taskId={tid}", flush=True)

    deadline = time.time() + 600
    while time.time() < deadline:
        info = http_get(f"{QUERY_URL}?taskId={tid}")
        state = info.get("data", {}).get("state")
        if state == "success":
            result = json.loads(info["data"]["resultJson"])
            out_path = os.path.join(OUT_DIR, f"{el['name']}.png")
            download(result["resultUrls"][0], out_path)
            print(f"  saved {el['name']}.png  ({os.path.getsize(out_path)//1024} KB)", flush=True)
            return
        if state == "fail":
            raise RuntimeError(f"task failed: {info.get('data', {}).get('failMsg')}")
        time.sleep(8)
    raise TimeoutError("timed out")


from concurrent.futures import ThreadPoolExecutor, as_completed
with ThreadPoolExecutor(max_workers=2) as ex:
    futs = [ex.submit(run, el) for el in VARIATIONS]
    for f in as_completed(futs):
        try: f.result()
        except Exception as e: print(f"  FAILED: {e}", flush=True); sys.exit(1)
print("done.")
