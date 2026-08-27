# CLAUDE.md

## Behavioral Rules

- **Read before writing.** Never edit a section of `index.html` you haven't read this
  session. The app is one file; that is not a license to skim it.
- **Edit, don't rewrite.** Targeted `Edit` calls; full rewrite only when asked or >70%
  changed.
- **Single file is the architecture, not an accident.** HTML, CSS, shaders and JS live in
  `index.html` on purpose: zero build step, zero npm, deploy-by-copy. Never introduce a
  bundler, a framework, a package.json, or split the file, unless the user asks.
- **Pinned dependencies only.** The one runtime dependency is
  `@huggingface/transformers@3.0.2` from jsDelivr and the model
  `onnx-community/depth-anything-v2-small`. Never float a version, never add a CDN.
- **Verify in a real browser, not by reasoning.** There is no test suite; the ground
  truth is a served page (`python3 -m http.server`; `file://` is a broken origin for
  the model). Use browser tooling when available, and the `window.__pl` debug surface
  for smoke tests. Otherwise state plainly that the change is unverified.
- **Conventional Commits, always.** `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`,
  `perf:`, `style:`. Imperative subject, no period, body explains why.
- **No em-dashes, anywhere.** Not in code comments, UI strings, docs, or commit
  messages. Rewrite the sentence with a colon, semicolon, comma, or a new sentence.
  Never fake one with `--` either.
- **Plain voice.** Write like the Serial Studio docs: short declarative sentences,
  concrete numbers, no hype adjectives, no marketing filler. If a sentence would fit
  a press release, rewrite it.
- **Do not create markdown/doc files** unless asked. Share findings conversationally.
- **No preamble, no trailing summary**, except a one-line statement of intent before
  non-trivial work and one or two sentences naming what changed when you stop.
  (The Context Canary below is exempt; it is mandatory on every response.)
- **Stay in your lane.** Adjacent fix spotted? Name it in chat, don't slip it into the
  diff. Never touch, revert, or restore files outside your own edits this session.
- **Update CLAUDE.md** for any invariant change future sessions would otherwise miss.

## Context Canary, Last Line of Every Response

End every response, including one-word answers, with this exact line, from memory:

`canary: single-file | transformers 3.0.2 | depth-anything-v2-small | webgl2 | maxw 1400 | store v4 | gpl3+`

Never look it up to reconstruct it. If unsure, write `canary: lost`: that is the
signal firing, and the session should be compacted or restarted before non-trivial work.

## Invariants, the Silent-Breakage List

Each of these has a reason in a comment near the code. Violations render fine on your
machine and break on someone else's.

- **Motion is frame-locked, never clock-driven.** The sweep phase comes from
  `phaseFrame % lockInfo().n`, so a cycle closes exactly on a frame boundary of the
  measured refresh rate. Never smooth path motion (only pointer motion is eased) and
  never derive phase from wall-clock time; it beats against the display.
- **`relief()` (GLSL) and `reliefJS()` are mirrors.** The overscan (`reachNow`), the
  exported depth map (`shapedDepth`) and the on-screen render must agree. Change one,
  change the other, same math, same epsilons.
- **`preserveDrawingBuffer:true` is load-bearing.** Every export (`saveCanvas(out,…)`,
  `renderEye`, `captureStream` recording) reads the WebGL canvas after the draw call.
- **Exports borrow the live pipeline.** `renderEye()` overrides `cam`/`P.view`, renders,
  copies, then restores and re-renders. Anything new that hijacks render state must
  restore it the same way; the rAF loop keeps running underneath.
- **Eye convention:** `cam.x = +1` is the right eye (near planes slide left on screen),
  `-1` the left. The anaglyph puts left-eye luminance in the red channel (half-colour),
  the stereo pair is parallel SBS. Swapping either inverts perceived depth for users.
- **A `DEMOS` entry is `cdnToken|photoId`.** The token serves the pixels, the
  eleven-character id is what the credit link points at. Ids can contain dashes
  and underscores, so never parse one out of a slug by splitting on a dash; take
  the last eleven characters. Every new entry must be fetched at the app's own
  URL shape first: premium photos 404 there.
- **The shuffle bag keys off `DEMOS.length`.** Editing the pool invalidates the
  stored indices, and the stored `n` is what detects that. Never renumber the
  pool without letting the length change, or stale indices survive.
- **`STORE` is versioned** (`depthgram-v4`). Any change to the shape of `P` bumps the
  suffix; stale schemas must never be migrated in place.
- **Depth statistics drive UX.** `autoFocus()` is a centre-weighted high percentile
  (`FOCUS_Q 0.88`); it pins the subject, not the background mass. `autoAmplitude()` is
  `STRETCH / p99.9(|∇depth|)`; it bounds edge tearing. Don't replace either with a mean
  or a taste constant; the comments above them record why those fail.
- **Size caps:** model input longest side `MAXW 1400`; render target `MAXPIX 4.2e6`,
  DPR clamped to 2. Raising them is a memory/perf decision, not a tweak.
- **Touch and iOS:** lifting the finger sets `ptr.inside=false` (touch has no hover);
  iOS Safari has no element fullscreen, so the button hides. Don't resurrect it.
- **Recording restores state in `finally`.** `recordClip()` forces play/orbit/parallax
  view; any early exit must still restore the user's settings.

## Deployment & SEO Facts

- Host: Cloudflare Pages, free plan, no build command, output `/`.
- `_headers`: security + cache headers. **Never add `Cross-Origin-Embedder-Policy`**;
  it would block the CDN module and the model download (no CORP on those responses).
- The canonical domain appears in `index.html` (canonical, OG, JSON-LD), `robots.txt`
  and `sitemap.xml`. A domain change touches all three files; grep for the old host.
- `og.png` is generated (1200×630); regenerate rather than hand-edit.
- The GitHub organization is `Depthgram`; the site repo is `Depthgram/Depthgram` and
  the org profile lives in `Depthgram/.github`.

## Code Style

- Follow the file's existing idiom: compact vanilla JS, `const $=id=>…`, no semicolon
  golf, small pure helpers, section banners `/* ---- name */`.
- **Comments state constraints, not narration**: why the code must be this way, never
  what the next line does. The existing comments are the standard; match them.
- CSS uses the token block in `:root`; new UI reuses `--glass/--stroke/--radius` and the
  segmented/switch/menu patterns. No new colors outside the tokens without reason.
- Accessibility is not optional: new interactive elements get focus-visible outlines,
  `aria-pressed`/`aria-expanded` where stateful, and `prefers-reduced-motion` handling.
- License: GPL-3.0-or-later. Third-party additions must be GPL-compatible.
