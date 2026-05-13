"""
Generate a hero-optimized book mockup (upright 3/4 angle, editorial light)
on a solid black background, then convert to a true transparent PNG that
floats on the magenta hero section.
"""
import json
import os
import sys
import time
import urllib.request

import numpy as np
from PIL import Image

API_KEY = "087ade3410b23ca9b66ff1f62b4b8169"
CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
QUERY_URL  = "https://api.kie.ai/api/v1/jobs/recordInfo"
COVER_URL  = "https://raw.githubusercontent.com/TCS-Andres/sowhatbook/main/images/book-cover.jpeg"

PROJECT = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(PROJECT, "mockups", "_raw")
IMG_DIR = os.path.join(PROJECT, "images")
os.makedirs(RAW_DIR, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Cover fidelity contract (carried from the mockup regen pass).
COVER_LOCK = (
    "STRICT REFERENCE-MATCHING TASK. The reference image is the real book cover "
    "and must be reproduced PIXEL-FAITHFULLY on the front of the book. DO NOT "
    "recolor, restyle, or redesign the cover. Cover layout: "
    "(1) Background = vibrant deep magenta/pink (~#B5208E), full bleed. "
    "(2) The word 'So' = large YELLOW italic serif character, upper-left. "
    "(3) The word 'What' = large WHITE italic serif character, lower-center. "
    "(4) A white hand-drawn scribble ball with a single white arrow shooting "
    "out the upper-right sits to the right of 'So'. "
    "(5) The subtitle 'How to Stop Overthinking Your Wins & Losses and Build "
    "Unstoppable Momentum' = 5 short stacked lines of small WHITE serif text, "
    "right-aligned, INSIDE the scribble. "
    "(6) The author line 'Dr. Meghna Dassani' = WHITE serif text, centered "
    "along the bottom of the cover. "
)

HERO_SCENE = (
    "Photorealistic 3D product render of a premium hardcover book standing "
    "upright at a 20-degree three-quarter angle, slightly rotated to the "
    "left so the spine is visible. Visible book thickness ~1 inch with "
    "subtle warm cream page edges peeking out on the right side. The book "
    "is rendered as if held up for the viewer — confident, presented. "
    "Editorial warm natural light from the upper-left like soft morning "
    "window light, casting a soft natural drop shadow grounding the book. "
    "BACKGROUND: a uniform solid pure BLACK (#000000) studio backdrop "
    "filling the entire canvas behind the book — flat, opaque, photographic "
    "black like a black-sweep studio shoot. DO NOT add a gradient, texture, "
    "or any color in the background. DO NOT draw a checkered pattern. The "
    "background is uniform flat black. The book is centered in the frame "
    "with generous empty black space around it (especially top and bottom) "
    "so it floats nicely when later composited onto another color. No "
    "props, no surface details — just the book on solid black. High-end "
    "publisher-supplied hero image quality."
)

PROMPT = COVER_LOCK + HERO_SCENE
ASPECT = "4:5"  # portrait-ish; works well in the hero's right column


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


# Same proven alpha-extraction pipeline used on the brand elements.
LOW, HIGH = 35, 70
def black_to_alpha(in_path, out_path):
    img = Image.open(in_path).convert("RGB")
    arr = np.array(img).astype(np.float32)
    brightness = np.max(arr, axis=2)

    alpha = np.where(
        brightness <= LOW, 0.0,
        np.where(
            brightness >= HIGH,
            brightness,
            brightness * (brightness - LOW) / (HIGH - LOW),
        ),
    )
    alpha = np.clip(alpha, 0, 255)
    safe = np.where(alpha > 0, alpha, 1.0)
    straight = np.minimum(arr * 255.0 / safe[..., None], 255.0)
    rgba = np.dstack([straight, alpha]).astype(np.uint8)
    Image.fromarray(rgba).save(out_path, "PNG", optimize=True)


def main():
    body = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": PROMPT,
            "image_input": [COVER_URL],
            "aspect_ratio": ASPECT,
            "resolution": "2K",
            "output_format": "png",
        },
    }
    r = http_post(CREATE_URL, body)
    if r.get("code") != 200:
        print(f"submit failed: {r}", flush=True)
        return 1
    tid = r["data"]["taskId"]
    print(f"submitted  taskId={tid}", flush=True)

    deadline = time.time() + 600
    while time.time() < deadline:
        info = http_get(f"{QUERY_URL}?taskId={tid}")
        state = info.get("data", {}).get("state")
        if state == "success":
            result = json.loads(info["data"]["resultJson"])
            raw = os.path.join(RAW_DIR, "hero_book.png")
            download(result["resultUrls"][0], raw)
            print(f"downloaded raw → {raw}", flush=True)
            out = os.path.join(IMG_DIR, "book-mockup-hero.png")
            black_to_alpha(raw, out)
            print(f"saved transparent hero mockup → {out} ({os.path.getsize(out)//1024} KB)", flush=True)
            return 0
        if state == "fail":
            print(f"task failed: {info.get('data', {}).get('failMsg')}", flush=True)
            return 1
        time.sleep(8)
    print("timed out", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
