#!/usr/bin/env python3
"""
build.py — convert an Obsidian markdown note into a write-up page for
youssefashraf.github.io.

It:
  1. Resolves the images referenced in the note (Obsidian ![[...]] embeds,
     markdown ![](...) links, file:/// absolute paths, and relative paths).
  2. Copies them into writeups/<Name>/images/<name>/imgNN.ext in document order.
  3. Converts the markdown to HTML and wraps it in the site template.
  4. Updates posts.json so the write-up shows up on writeups.html.

Usage:
    python build.py "path/to/My Box writeup.md"

Options:
    --title "Checkpoint"        Write-up title (default: first # heading or filename)
    --date "Oct 2026"           Publication date (default: file mtime -> "Mon YYYY")
    --tag "HackTheBox"          Tag badge (default: "HackTheBox")
    --status "Retired"          Status label (default: "Retired")
    --summary "..."             Card summary (default: first paragraph, trimmed)
    --machine-url "https://..." HTB machine link (optional, not required)

Dependencies: markdown  ->  pip install markdown
"""

import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    import markdown as md
except ImportError:
    sys.exit("Missing dependency. Run:  pip install markdown")

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent

# Roots where the script searches for images it cannot resolve directly.
# Add your Obsidian vault attachment folders here.
ATTACHMENT_ROOTS = [
    r"D:/obisidian/Java shit/gitbook/assets",
    r"C:/Users/Asus/Documents/ShareX/Screenshots",
]

# --------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------
PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} | Youssef Ashraf</title>
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Zen+Old+Mincho&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../css/style.css">
</head>
<body>
<div class="bg-orb o1" aria-hidden="true"></div>
<div class="bg-orb o2" aria-hidden="true"></div>

<div class="wrap">
  <a class="back" href="../../writeups.html">&larr; All write-ups</a>
  <header class="post-head">
    <p class="eyebrow">{tag} &bull; {status}</p>
    <h1>{title}</h1>
    <p class="meta"><span>{date}</span><span class="pill">{tag}</span></p>
  </header>
  <article>
{body}
  </article>
  <div class="article-footer">Written by Youssef Ashraf. Published for a retired HTB machine, in line with HTB's write-up policy.</div>
</div>

<script src="../../js/main.js"></script>
</body>
</html>
"""

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
# Single alternation so image order is preserved across wikilink + markdown
# embeds in document order.
IMG_RE = re.compile(r"!\[\[([^\]]+)\]\]|!\[([^\]]*)\]\(([^)]+)\)")


def slugify(text: str) -> str:
    """'DevHub' -> 'devhub'"""
    return re.sub(r"[^a-z0-9]+", "", text.lower()) or "writeup"


def safe_name(text: str) -> str:
    """Sanitise a title into a folder-safe name (keeps case)."""
    return re.sub(r'[<>:"/\\|?*]', "", text).strip() or "Writeup"


def month_name(m: int) -> str:
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1]


def find_by_basename(roots, basename):
    """Search candidate roots recursively for a file matching basename."""
    for root in roots:
        r = Path(root)
        if not r.is_dir():
            continue
        try:
            for hit in r.rglob(basename):
                if hit.is_file():
                    return hit
        except OSError:
            continue
    return None


def resolve_source(src: str, note_dir: Path):
    """Turn an image reference into a Path on disk, or None."""
    src = src.strip()
    if src.startswith(("http://", "https://")):
        return None  # external, leave as-is

    decoded = unquote(src)

    # file:///C:/...  ->  C:/...
    if decoded.startswith("file://"):
        decoded = decoded[len("file://"):].lstrip("/")
        # on windows a leading drive letter is expected
        p = Path(decoded)
        return p if p.is_file() else None

    # absolute windows path  C:\... or C:/...  or UNC
    if re.match(r"^[A-Za-z]:[\\/]", decoded) or decoded.startswith(("/", "\\")):
        p = Path(decoded)
        return p if p.is_file() else None

    # relative to the note
    p = (note_dir / decoded).resolve()
    if p.is_file():
        return p

    # fall back: search attachment roots by basename
    return find_by_basename([note_dir, *ATTACHMENT_ROOTS], Path(decoded).name)


def extract_images(text: str, note_dir: Path):
    """
    Return (new_text, images) where images is a list of resolved Paths in
    document order, and new_text has every local image reference rewritten
    to a placeholder marker.
    """
    images = []  # list of (resolved_path, alt)

    def repl(m):
        alt = ""
        target = None
        if m.group(0).startswith("![["):  # wikilink embed
            raw = m.group(1)
            parts = raw.split("|")
            filename = parts[0].strip()
            alt = parts[1].strip() if len(parts) > 1 else filename
            target = filename
        else:  # markdown image
            alt = m.group(2)
            target = m.group(3)

        resolved = resolve_source(target, note_dir)
        if resolved is None:
            return m.group(0)  # leave external / unresolvable untouched
        images.append((resolved, alt))
        return f"![](@@IMG{len(images) - 1}@@)"

    return IMG_RE.sub(repl, text), images


def first_paragraph_summary(text: str, limit: int = 190) -> str:
    for para in text.split("\n\n"):
        p = para.strip()
        if not p or p.startswith(("#", "```", "![", "-", ">", "|")):
            continue
        # strip inline markdown
        p = re.sub(r"`([^`]*)`", r"\1", p)
        p = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", p)
        p = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", p)
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            return p[:limit].rstrip() + ("..." if len(p) > limit else "")
    return ""


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Convert an Obsidian note into a write-up page.")
    ap.add_argument("note", help="Path to the .md note")
    ap.add_argument("--title", help="Write-up title")
    ap.add_argument("--date", help='Date, e.g. "Oct 2026"')
    ap.add_argument("--tag", default="HackTheBox", help="Tag badge")
    ap.add_argument("--status", default="Retired", help="Status label")
    ap.add_argument("--summary", help="Card summary")
    ap.add_argument("--machine-url", help="HTB machine link")
    args = ap.parse_args()

    note = Path(args.note).expanduser()
    if not note.is_file():
        sys.exit(f"Not found: {note}")

    text = note.read_text(encoding="utf-8", errors="replace")

    # --- title ---
    title = args.title
    if not title:
        m = re.search(r"^#\s+(.+)$", text, flags=re.M)
        if m:
            title = m.group(1).strip()
        else:
            title = re.sub(r"\s*(writeup|write up|walkthrough)\s*$", "", note.stem,
                           flags=re.I).strip()
    title = title or "Writeup"

    # --- date ---
    if args.date:
        date = args.date
    else:
        ts = datetime.datetime.fromtimestamp(note.stat().st_mtime)
        date = f"{month_name(ts.month)} {ts.year}"

    # --- summary ---
    summary = args.summary or first_paragraph_summary(text)

    # --- machine link (decorative intro is left to the note itself) ---
    machine_url = args.machine_url

    # --- images ---
    new_text, images = extract_images(text, note.parent)

    # --- output paths ---
    folder = safe_name(title)
    slug = slugify(title)
    out_dir = REPO_ROOT / "writeups" / folder
    img_dir = out_dir / "images" / slug
    img_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for i, (src, alt) in enumerate(images, start=1):
        ext = src.suffix or ".png"
        dest = img_dir / f"img{i:02d}{ext}"
        shutil.copy2(src, dest)
        copied.append((src, dest))
        rel = f"images/{slug}/{dest.name}"
        new_text = new_text.replace(f"![](@@IMG{i - 1}@@)", f"![]({rel})")

    # --- markdown -> html ---
    body = md.markdown(
        new_text,
        extensions=["fenced_code", "tables", "sane_lists"],
    )

    description = summary or ""
    page = PAGE_TEMPLATE.format(
        title=title,
        date=date,
        tag=args.tag,
        status=args.status,
        description=description.replace('"', "&quot;"),
        body=body,
    )

    html_path = out_dir / f"{slug}.html"
    html_path.write_text(page, encoding="utf-8")

    # --- posts.json ---
    posts_path = REPO_ROOT / "posts.json"
    posts = []
    if posts_path.is_file():
        try:
            posts = json.loads(posts_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            posts = []

    url = f"writeups/{folder}/{slug}.html"
    entry = {
        "title": f"HTB: {title}" if not title.lower().startswith("htb") else title,
        "date": date,
        "tag": args.tag,
        "summary": summary,
        "url": url,
    }
    posts = [p for p in posts if p.get("url") != url]
    posts.append(entry)
    posts_path.write_text(
        json.dumps(posts, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- report ---
    print(f"title   : {entry['title']}")
    print(f"date    : {date}")
    print(f"html    : {html_path.relative_to(REPO_ROOT)}")
    print(f"images  : {len(copied)}")
    for src, dest in copied:
        print(f"  {src.name} -> {dest.relative_to(REPO_ROOT)}")
    print(f"posts   : updated {posts_path.name} ({len(posts)} entries)")


if __name__ == "__main__":
    main()
