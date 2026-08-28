# Depthgram

Depthgram turns any photo into an animated 3D scene, entirely in your browser.

Drop a photo. A depth estimation model computes per-pixel depth, a WebGL 2 renderer
re-projects the image through it, and the camera starts moving. Nothing is uploaded and
there is no server: the model runs on your GPU, through WebGPU when the browser has it
and WASM otherwise. No account, no watermark, no tracking.

Live at <https://depthgram.com>.

## Exports

- **Rendered frame** (PNG): the current camera view.
- **Depth map** (PNG): the shaped field the renderer marches, with layers and
  exaggeration applied.
- **Anaglyph** (PNG): half-colour red/cyan, with luminance in the red channel to reduce
  retinal rivalry.
- **Stereo pair** (PNG): parallel side-by-side, the layout VR viewers expect.
- **Looping clip** (MP4 or WebM): a whole number of camera sweeps, so the file loops
  without a seam.

## How it works

1. **Depth estimation.** [Depth Anything V2 (small)][dav2] runs through
   [transformers.js][tjs]. About 50 MB downloaded once, then cached by the browser.
2. **Analysis.** The depth histogram picks the focus plane: a high centre-weighted
   percentile, so the subject stays pinned instead of the sky. The steepest depth
   gradients bound the motion range so edges never visibly tear.
3. **Rendering.** A single-pass WebGL 2 fragment shader does steep parallax marching
   with bisection refinement for correct occlusion, optional depth of field with a
   golden-angle gather, and ordered dithering so sub-pixel motion survives 8-bit output.
4. **Motion.** Camera sweeps are phase-locked to the display. Each cycle closes exactly
   on a frame boundary at the measured refresh rate, so playback never beats against
   the display.

The whole application is one dependency-free `index.html`. The only network traffic is
the CDN module, the model weights, and the optional Unsplash demo photos.

## Run it locally

```bash
git clone https://github.com/Depthgram/Depthgram.git
cd Depthgram
python3 -m http.server
open http://localhost:8000
```

Any static server works. `file://` does not: the model needs a real origin.

## Repository layout

| Path | What it is |
| --- | --- |
| `index.html` | The entire application: markup, CSS, GLSL and JS. |
| `build_icons.py` | Generates every brand asset from one geometry definition. |
| `favicon.*`, `icon-*.png`, `apple-touch-icon.png`, `og.png` | Generated. Do not hand-edit. |
| `_headers`, `robots.txt`, `sitemap.xml`, `site.webmanifest` | Static hosting and SEO. |
| `CLAUDE.md` | The invariants that keep the render path correct. |

Regenerate the brand assets after editing `build_icons.py`:

```bash
python3 -m pip install pillow
python3 build_icons.py
```

## Deploy

Depthgram is a static site with no build step; the repository is the site. On
Cloudflare Pages: connect the repo, leave the build command empty, set the output
directory to `/`, and attach your domain. `_headers` ships the security and caching
headers, and `robots.txt`, `sitemap.xml`, the web manifest and the Open Graph card are
already wired. Deploying under a different domain means updating the canonical URL in
`index.html`, `robots.txt` and `sitemap.xml`.

## Privacy

Photos never leave the device. There are no analytics, no cookies, no accounts and no
database. Settings persist in `localStorage` only.

## Browser support

WebGL 2 is required, which every evergreen browser has. WebGPU is used when present and
falls back cleanly. Clip export needs `MediaRecorder`: MP4 on Safari and Chrome 126+,
WebM elsewhere.

## Contributing

The whole app is one file by design. Read [CLAUDE.md](CLAUDE.md) for the invariants that
keep it correct (frame-locked motion, the relief curve mirror, texture lifetime) before
touching the render path. Commits follow [Conventional Commits][cc].

## License

[GPL-3.0-or-later](LICENSE). Demo photos courtesy of [Unsplash](https://unsplash.com).
Depth model by the [Depth Anything V2][dav2] authors (Apache-2.0), served through the
ONNX community builds.

[dav2]: https://depth-anything-v2.github.io
[tjs]: https://github.com/huggingface/transformers.js
[cc]: https://www.conventionalcommits.org/
