#!/usr/bin/env python3
"""IndexNow submitter for depthgram.com.

IndexNow (https://www.indexnow.org) pushes new or changed URLs to
participating search engines instead of waiting for a re-crawl. Bing,
Yandex, Seznam and Naver consume it; Google does not, so this complements
Google Search Console and the sitemap, it does not replace them.

How it works: a plain-text key file lives at the site root
(3ffe01a05a8c4cd2a0424bf15d5a572e.txt, contents = the key). A POST to the
IndexNow API with that key makes each engine fetch the key file to prove
domain ownership, then queue the URLs for crawling.

IMPORTANT: run this AFTER the deploy is live, never at build time. The
engine fetches every submitted URL within moments to verify it; pinging a
URL that still 404s wastes the submission. So this is a deploy step:
`git push`, Cloudflare Pages finishes, then run this.

Usage:
  python3 submit_indexnow.py --all           # every URL in sitemap.xml
  python3 submit_indexnow.py <url> [<url>]   # explicit URLs or site paths
  python3 submit_indexnow.py --all --dry-run # print the payload, send nothing

Only the standard library is used (urllib), matching build_icons.py.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://depthgram.com"
HOST = "depthgram.com"
KEY = "3ffe01a05a8c4cd2a0424bf15d5a572e"
KEY_FILE = f"{KEY}.txt"
KEY_LOCATION = f"{SITE}/{KEY_FILE}"
ENDPOINT = "https://api.indexnow.org/indexnow"


def urls_from_sitemap():
    """Every <loc> in sitemap.xml, already the canonical list of indexable
    URLs. The image <image:loc> entries are assets, not pages; the regex
    scoped to <loc> alone skips them because the image tag is namespaced."""
    with open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8") as f:
        xml = f.read()
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def normalize(items):
    """Accept full URLs or bare site paths; return absolute, de-duplicated,
    same-host URLs (IndexNow rejects a batch that mixes hosts)."""
    seen, out = set(), []
    for it in items:
        it = it.strip()
        if not it:
            continue
        if it.startswith("http://") or it.startswith("https://"):
            url = it
        else:
            url = f"{SITE}/{it.lstrip('/')}"
        if not url.startswith(SITE):
            print(f"skip (wrong host): {url}", file=sys.stderr)
            continue
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def submit(urls):
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow: HTTP {resp.status}, {len(urls)} URL(s) accepted.")
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace").strip()
        # 200 accepted / 202 accepted, key validation pending / 400 bad request
        # 403 key not valid / 422 URL or key mismatch / 429 rate limited
        print(f"IndexNow: HTTP {e.code}, {e.reason}. {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"IndexNow: network error, {e.reason}", file=sys.stderr)
        return 1


def main():
    ap = argparse.ArgumentParser(description="Submit URLs to IndexNow (Bing, Yandex, ...).")
    ap.add_argument("urls", nargs="*", help="explicit URLs or site paths to submit")
    ap.add_argument("--all", action="store_true", help="submit every URL in sitemap.xml")
    ap.add_argument("--dry-run", action="store_true", help="print the URL list, send nothing")
    args = ap.parse_args()

    # Guard: the key file must exist locally with matching contents, or the
    # engines' ownership check will fail once they fetch KEY_LOCATION.
    kf = os.path.join(ROOT, KEY_FILE)
    if not os.path.exists(kf):
        sys.exit(f"missing key file {KEY_FILE}; it must be deployed at {KEY_LOCATION}")
    with open(kf, encoding="utf-8") as f:
        if f.read().strip() != KEY:
            sys.exit(f"{KEY_FILE} contents do not match KEY")

    if args.all:
        urls = urls_from_sitemap()
    elif args.urls:
        urls = normalize(args.urls)
    else:
        ap.error("give URLs, or use --all")

    urls = normalize(urls)
    if not urls:
        print("Nothing to submit.")
        return

    if args.dry_run:
        print(f"[dry run] would submit {len(urls)} URL(s):")
        for u in urls:
            print(f"  {u}")
        return

    sys.exit(submit(urls))


if __name__ == "__main__":
    main()
