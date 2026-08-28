#!/usr/bin/env python3
"""
build_icons.py: generate every brand asset from one geometry definition.

Why a script: the mark exists at eight sizes plus the social card, and a
hand-edited copy always drifts from the others. Edit TREE/COLORS here and
re-run; never touch the generated files.

    python3 build_icons.py

Writes favicon.svg, favicon.ico, favicon-96x96.png, apple-touch-icon.png,
icon-192.png, icon-512.png, icon-512-maskable.png and og.png.

Requires Pillow. Everything else is stdlib.

The mark is three pine trees on the same silhouette, offset horizontally and
shaded from far (desaturated) to near (accent): the parallax layer stack the
renderer builds, drawn as an object. Only the front tree carries a trunk;
trunks on the back layers read as noise below 32 px.
"""

import struct
from PIL import Image, ImageDraw, ImageFont

OUT = {
    "favicon.svg": None,
    "favicon.ico": (16, 32, 48, 64),
    "favicon-96x96.png": 96,
    "apple-touch-icon.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
    "icon-512-maskable.png": 512,
    "og.png": (1200, 630),
}

# ---------------------------------------------------------------- palette
BG = "#0B0B0C"          # --page
# Far to near runs violet, accent blue, cyan: rising luminance so the layers
# still recede, and three hues so the mark reads as split colour channels
# rather than one blue tree drawn three times.
FAR = "#6A2BD9"
MID = "#0A84FF"         # --accent
NEAR = "#2BE7F0"
INK = "#FFFFFF"
LABEL = "#9A9AA0"

RADIUS = 0.176          # corner radius as a fraction of the icon side

# ---------------------------------------------------------------- geometry
# Unit space: 0..1 across the icon square. The front tree's apex sits right of
# centre so the three layers stay balanced inside the rounded square.
CX = 0.5885
TREE = dict(
    apex=0.2026,
    t1_bot=0.4067, h1=0.1475,
    t2_top=0.4171, h2t=0.0965,
    t2_bot=0.5662, h2=0.2058,
    t3_top=0.5766, h3t=0.1467,
    t3_bot=0.7256, h3=0.2512,
    trunk_bot=0.8150, trunk_half=0.0574,
)
# Back-to-front: horizontal offset from the front tree, and fill.
LAYERS = ((-0.1667, FAR), (-0.0797, MID), (0.0, NEAR))


def foliage(cx):
    """Closed pine outline: three tiers, each stepping in at the notch."""
    t = TREE
    right = [
        (cx, t["apex"]),
        (cx + t["h1"], t["t1_bot"]),
        (cx + t["h2t"], t["t2_top"]),
        (cx + t["h2"], t["t2_bot"]),
        (cx + t["h3t"], t["t3_top"]),
        (cx + t["h3"], t["t3_bot"]),
    ]
    left = [(2 * cx - x, y) for x, y in reversed(right[1:])]
    return right + left


def trunk(cx):
    t = TREE
    return [
        (cx - t["trunk_half"], t["t3_bot"]),
        (cx + t["trunk_half"], t["t3_bot"]),
        (cx + t["trunk_half"], t["trunk_bot"]),
        (cx - t["trunk_half"], t["trunk_bot"]),
    ]


# The mark is centred on (.5,.5) already; this only trades padding for legible
# notches at 16 px. Anything past ~1.15 crowds the rounded corners.
ART_SCALE = 1.10


def shapes():
    """Every filled polygon, back to front, in unit space."""
    out = []
    for dx, fill in LAYERS:
        out.append((foliage(CX + dx), fill))
    out.append((trunk(CX), NEAR))
    s = ART_SCALE
    return [([(0.5 + (x - 0.5) * s, 0.5 + (y - 0.5) * s) for x, y in poly], fill)
            for poly, fill in out]


# ---------------------------------------------------------------- svg
def write_svg(path, side=64):
    def pts(poly):
        return " ".join(
            ("M" if i == 0 else "L") + f"{x * side:.2f} {y * side:.2f}"
            for i, (x, y) in enumerate(poly)
        ) + "Z"

    body = "\n".join(
        f'  <path d="{pts(poly)}" fill="{fill}"/>' for poly, fill in shapes()
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
        f'role="img" aria-label="Depthgram">\n'
        f'  <rect width="{side}" height="{side}" rx="{RADIUS * side:.2f}" fill="{BG}"/>\n'
        f"{body}\n</svg>\n"
    )
    with open(path, "w") as f:
        f.write(svg)


# ---------------------------------------------------------------- raster
SS = 8  # supersample factor; the notches are the part that aliases


def rounded_mask(side, radius):
    m = Image.new("L", (side * SS, side * SS), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        (0, 0, side * SS - 1, side * SS - 1), radius=radius * SS, fill=255
    )
    return m.resize((side, side), Image.LANCZOS)


def render(side, *, rounded=True, scale=1.0):
    """Icon at `side` px. `scale` shrinks the mark inside the square."""
    big = side * SS
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, big, big), fill=BG)
    off = (1 - scale) / 2
    for poly, fill in shapes():
        d.polygon([((off + x * scale) * big, (off + y * scale) * big) for x, y in poly],
                  fill=fill)
    im = im.resize((side, side), Image.LANCZOS)
    if rounded:
        im.putalpha(rounded_mask(side, int(round(RADIUS * side))))
    return im


def write_ico(path, sizes):
    """Multi-size ICO. Pillow's own writer resamples one image; these are
    rendered per size so the 16 px notches survive."""
    frames = [render(s).convert("RGBA") for s in sizes]
    import io

    blobs = []
    for f in frames:
        buf = io.BytesIO()
        f.save(buf, format="PNG")
        blobs.append(buf.getvalue())
    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = 6 + 16 * len(frames)
    entries, data = b"", b""
    for f, blob in zip(frames, blobs):
        w = 0 if f.width >= 256 else f.width
        h = 0 if f.height >= 256 else f.height
        entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
        data += blob
    with open(path, "wb") as fh:
        fh.write(header + entries + data)


# ---------------------------------------------------------------- og card
FONTS = (
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
)


FACE = {"regular": 0, "bold": 1, "medium": 10}


def font(size, weight="regular"):
    for path in FONTS:
        try:
            if path.endswith(".ttc"):
                return ImageFont.truetype(path, size, index=FACE[weight])
            if weight != "regular":
                try:
                    return ImageFont.truetype(path.replace("Arial.ttf", "Arial Bold.ttf"), size)
                except OSError:
                    pass
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def glow(im, cx, cy, r, alpha):
    """The site paints blurred white circles behind the glass; the card keeps
    the same background so the two read as one surface."""
    layer = Image.new("L", (im.width // 4, im.height // 4), 0)
    d = ImageDraw.Draw(layer)
    steps = 42
    for i in range(steps):
        t = 1 - i / steps
        rr = r * t / 4
        d.ellipse((cx / 4 - rr, cy / 4 - rr, cx / 4 + rr, cy / 4 + rr),
                  fill=int(alpha * 255 / steps) * (i + 1) // steps + 1)
    layer = layer.resize(im.size, Image.BICUBIC)
    white = Image.new("RGB", im.size, "#FFFFFF")
    return Image.composite(white, im, layer.point(lambda v: min(v, int(alpha * 255))))


PILLS = ("Parallax scenes", "Depth maps", "Anaglyphs", "Stereo pairs", "Looping clips")


def pill(im, d, x, y, text, f):
    """The card reuses the app's segmented-control look: faint fill, hairline
    stroke, no shadow. Returns the advance."""
    pad, hh = 22, 52
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((x, y, x + tw + pad * 2, y + hh), radius=hh // 2,
                        fill=(23, 23, 25), outline=(56, 56, 60), width=1)
    d.text((x + pad, y + hh / 2), text, font=f, fill=INK, anchor="lm")
    return tw + pad * 2 + 14


def write_og(path, size):
    w, h = size
    im = Image.new("RGB", size, BG)
    im = glow(im, -40, -80, 820, 0.075)
    im = glow(im, w + 60, h * 0.1, 700, 0.05)
    im = glow(im, w * 0.5, h + 260, 900, 0.04)
    d = ImageDraw.Draw(im)

    mark, mx, my = 148, 88, 84
    im.paste(render(mark), (mx, my), render(mark))

    d.text((mx + mark + 34, my + mark / 2 - 4), "Depthgram",
           font=font(88, "bold"), fill=INK, anchor="lm")

    d.text((mx, my + mark + 52), "Any photo becomes an animated 3D scene,",
           font=font(42, "medium"), fill=INK)
    d.text((mx, my + mark + 108), "computed in your browser and never uploaded.",
           font=font(42, "medium"), fill=LABEL)

    x, f = mx, font(28)
    for p in PILLS:
        x += pill(im, d, x, h - 176, p, f)

    site, foot = "depthgram.com", font(28)
    d.text((mx, h - 82), site, font=font(28, "bold"), fill=NEAR)
    d.text((mx + d.textlength(site, font=font(28, "bold")) + 28, h - 82),
           "Free and open source  ·  No account", font=foot, fill=LABEL)
    im.save(path, optimize=True)


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    write_svg("favicon.svg")
    write_ico("favicon.ico", OUT["favicon.ico"])
    render(96).save("favicon-96x96.png", optimize=True)
    # iOS applies its own mask, so the touch icon is full bleed and opaque.
    render(180, rounded=False).convert("RGB").save("apple-touch-icon.png", optimize=True)
    render(192).save("icon-192.png", optimize=True)
    render(512).save("icon-512.png", optimize=True)
    # Maskable art must survive a 40% safe-zone circle crop.
    render(512, rounded=False, scale=0.72).save("icon-512-maskable.png", optimize=True)
    write_og("og.png", OUT["og.png"])
    print("wrote:", ", ".join(OUT))
