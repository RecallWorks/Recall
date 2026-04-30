# @wbx-modified copilot-a3f7 | 2026-04-30 00:08 MTN | v1.0 | render Recall logo PNGs from PIL (no SVG dep) | prev: NEW
"""Render the Recall logo at 128/256/512 PNG sizes for stores and READMEs.

Brand cues from website (`/website/_dist/index.html`):
  bg     #0b0d10
  accent #7cc4ff (sky)
  text   #e8eaed
  mark   = circle with sky radial gradient (top-left highlight)

Output:
  assets/logo-128.png  -> VS Code / Anthropic MCP gallery card
  assets/logo-256.png  -> README header
  assets/logo-512.png  -> social / OG image base
  assets/logo.svg      -> vector source for downstream re-export

Run:
  python assets/make-logo.py
"""
from __future__ import annotations
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

BG       = (11, 13, 16, 255)       # #0b0d10
ACCENT   = (124, 196, 255, 255)    # #7cc4ff
ACCENT_DIM = (124, 196, 255, 70)
TEXT     = (232, 234, 237, 255)    # #e8eaed
RING     = (58, 64, 73, 255)       # #3a4049

def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Outer rounded background (squircle-ish via rounded rectangle)
    radius = int(size * 0.22)
    d.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=BG,
    )

    # Concentric "memory rings" — three faint circles suggesting recall waves
    cx, cy = size // 2, size // 2
    for i, r_frac in enumerate([0.46, 0.36, 0.27]):
        r = int(size * r_frac)
        thickness = max(1, size // 96)
        # fade outermost rings
        alpha = [180, 120, 80][i]
        col = (RING[0], RING[1], RING[2], alpha)
        d.ellipse(
            [(cx - r, cy - r), (cx + r, cy + r)],
            outline=col,
            width=thickness,
        )

    # Central glyph — solid disc with offset highlight (the radial gradient feel)
    inner_r = int(size * 0.18)
    d.ellipse(
        [(cx - inner_r, cy - inner_r), (cx + inner_r, cy + inner_r)],
        fill=ACCENT,
    )
    # Highlight: smaller white-ish disc top-left of the accent disc, blurred
    hl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hl_r = int(size * 0.09)
    hl_cx = cx - int(size * 0.05)
    hl_cy = cy - int(size * 0.05)
    hd.ellipse(
        [(hl_cx - hl_r, hl_cy - hl_r), (hl_cx + hl_r, hl_cy + hl_r)],
        fill=(255, 255, 255, 110),
    )
    hl = hl.filter(ImageFilter.GaussianBlur(radius=size / 64))
    img.alpha_composite(hl)

    # "R" wordmark inside the accent disc (white)
    try:
        # Prefer a heavier weight if available on the system
        font_path = None
        for cand in [
            "C:/Windows/Fonts/segoeuib.ttf",   # Segoe UI Bold
            "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
            "C:/Windows/Fonts/arial.ttf",
        ]:
            if os.path.exists(cand):
                font_path = cand
                break
        font_size = int(size * 0.22)
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    text = "R"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = cx - tw // 2 - bbox[0]
    ty = cy - th // 2 - bbox[1]
    d.text((tx, ty), text, fill=TEXT, font=font)

    return img


def write_svg() -> None:
    """Minimal vector source, brand-matched. Hand-authored — no PIL conversion."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="Recall">
  <defs>
    <radialGradient id="g" cx="42%" cy="42%" r="60%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.55"/>
      <stop offset="55%" stop-color="#7cc4ff" stop-opacity="1"/>
      <stop offset="100%" stop-color="#7cc4ff" stop-opacity="1"/>
    </radialGradient>
  </defs>
  <rect width="128" height="128" rx="28" ry="28" fill="#0b0d10"/>
  <circle cx="64" cy="64" r="59" fill="none" stroke="#3a4049" stroke-opacity="0.70" stroke-width="1.4"/>
  <circle cx="64" cy="64" r="46" fill="none" stroke="#3a4049" stroke-opacity="0.50" stroke-width="1.4"/>
  <circle cx="64" cy="64" r="35" fill="none" stroke="#3a4049" stroke-opacity="0.32" stroke-width="1.4"/>
  <circle cx="64" cy="64" r="23" fill="url(#g)"/>
  <text x="64" y="64" font-family="Segoe UI, Arial, sans-serif" font-weight="700"
        font-size="28" fill="#e8eaed" text-anchor="middle"
        dominant-baseline="central">R</text>
</svg>
"""
    with open(os.path.join(OUT_DIR, "logo.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


def main() -> None:
    write_svg()
    for sz in (128, 256, 512):
        img = render(sz)
        img.save(os.path.join(OUT_DIR, f"logo-{sz}.png"), "PNG", optimize=True)
        print(f"wrote logo-{sz}.png")
    print("wrote logo.svg")


if __name__ == "__main__":
    main()
