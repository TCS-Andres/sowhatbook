"""
Generates 3 photorealistic book mockup variations using the actual 'So What'
book cover (hosted in the GitHub repo) as a reference image.
"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "087ade3410b23ca9b66ff1f62b4b8169"
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
QUERY_URL  = "https://api.kie.ai/api/v1/jobs/recordInfo"
COVER_URL  = "https://raw.githubusercontent.com/TCS-Andres/sowhatbook/main/images/book-cover.jpeg"
OUT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mockups")
os.makedirs(OUT_DIR, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

COVER_FIDELITY = (
    "CRITICAL: The book cover artwork must be reproduced EXACTLY as shown in the "
    "reference image — same vibrant magenta/pink background color, same yellow "
    "italic serif 'So' character, same white serif 'What' below it, same hand-drawn "
    "white scribble-ball with arrow shooting out the upper right, same white "
    "subtitle text ('How to Stop Overthinking Your Wins & Losses and Build "
    "Unstoppable Momentum'), and same author line 'Dr. Meghna Dassani' at the bottom. "
    "Do NOT redesign, restyle, recolor, or reinterpret the cover. Wrap the existing "
    "artwork from the reference image onto a physical hardcover book."
)

VARIATIONS = [
    {
        "name": "mockup_1_studio_hero",
        "aspect_ratio": "4:3",
        "prompt": (
            "Photorealistic 3D product render of a premium hardcover book standing "
            "upright at a subtle 25-degree three-quarter angle on a clean surface. "
            "The book has a visible spine (roughly 1 inch thick) and slight page "
            "edges peeking out on the right side. Soft studio key light from the "
            "upper-left producing a gentle drop shadow on the floor. Background is "
            "a smooth gradient from a dusty rose pink in the upper-left to a warm "
            "cream in the lower-right — clean editorial product photography. "
            "Centered composition, generous negative space. Crisp focus on the "
            "entire book, no motion blur. High-end Amazon-style hero shot. "
            f"{COVER_FIDELITY}"
        ),
    },
    {
        "name": "mockup_2_lifestyle_hands",
        "aspect_ratio": "4:5",
        "prompt": (
            "Lifestyle photography from a slightly elevated angle: a woman's "
            "well-manicured hands (warm-toned skin, neutral nail polish) holding "
            "a hardcover book upright in front of her, the cover facing the "
            "camera. The hands grip the book from the lower edge so the full "
            "cover is visible. Background is a softly out-of-focus cozy "
            "interior — a hint of an oatmeal-colored knit sweater the woman is "
            "wearing, blurred natural light coming through a window on the left, "
            "a faint suggestion of a wooden surface and a ceramic mug in the "
            "deep background. Warm natural daylight, sharp focus on the book, "
            "shallow depth-of-field elsewhere. Editorial Instagram aesthetic, "
            "not stocky. "
            f"{COVER_FIDELITY}"
        ),
    },
    {
        "name": "mockup_3_flatlay_desk",
        "aspect_ratio": "1:1",
        "prompt": (
            "Top-down flat-lay photograph of a hardcover book lying flat on a "
            "creamy off-white linen surface. The book is angled diagonally about "
            "15 degrees from vertical, centered slightly off-center. Around it, "
            "elegantly arranged minimal props: a small terracotta-pot succulent "
            "with a single green leaf in the upper-right, a folded tan linen "
            "napkin under one corner of the book, a ceramic mug of black coffee "
            "in the upper-left (steam barely visible), a pair of tortoiseshell "
            "reading glasses resting near the book, and a brass pen lying "
            "diagonally near the bottom-right. Soft natural morning light "
            "casting gentle shadows. Aesthetic Pinterest/editorial flat-lay "
            "style. The book is the clear hero of the composition. "
            f"{COVER_FIDELITY}"
        ),
    },
]


def http_post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
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


def submit(el):
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
        raise RuntimeError(f"submit failed for {el['name']}: {r}")
    tid = r["data"]["taskId"]
    print(f"  submitted {el['name']}  taskId={tid}", flush=True)
    return el["name"], tid


def poll(name, tid, max_wait=600):
    deadline = time.time() + max_wait
    while time.time() < deadline:
        info = http_get(f"{QUERY_URL}?taskId={tid}")
        state = info.get("data", {}).get("state")
        if state == "success":
            result = json.loads(info["data"]["resultJson"])
            out_path = os.path.join(OUT_DIR, f"{name}.png")
            download(result["resultUrls"][0], out_path)
            size_kb = os.path.getsize(out_path) // 1024
            print(f"  saved {name}.png  ({size_kb} KB)", flush=True)
            return out_path
        if state == "fail":
            raise RuntimeError(f"task {tid} ({name}) failed: {info.get('data', {}).get('failMsg')}")
        time.sleep(8)
    raise TimeoutError(f"task {tid} ({name}) timed out")


def main():
    print(f"submitting {len(VARIATIONS)} mockup variations using reference cover:", flush=True)
    print(f"  {COVER_URL}\n", flush=True)

    submissions = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        for fut in as_completed([ex.submit(submit, el) for el in VARIATIONS]):
            submissions.append(fut.result())

    print("\npolling for completion...", flush=True)
    failures = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(poll, name, tid): name for name, tid in submissions}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                fut.result()
            except Exception as e:
                print(f"  FAILED {name}: {e}", flush=True)
                failures.append(name)

    if failures:
        print(f"\nfinished with {len(failures)} failure(s).", flush=True)
        return 1
    print(f"\nall {len(VARIATIONS)} mockups generated successfully in {OUT_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
