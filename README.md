# youssefashraf.github.io

Personal site — Youssef Ashraf, security &amp; networks. Theme is *Senbonzakura*,
inspired by Kuchiki Byakuya from Bleach (black shihakusho, silver scarf, sakura petals).

## Layout

```
index.html          home / portfolio
writeups.html       all write-ups (rendered from posts.json)
posts.json          write-up manifest
css/style.css       shared styles + theme + animations
js/main.js          theme, scroll reveal, sakura petals, post list
build.py            convert an Obsidian note into a write-up page
writeups/<Name>/    one folder per box
```

## Add a write-up

Drop your Obsidian note anywhere and run:

```bash
pip install markdown        # one-time
python build.py "D:/path/to/Box writeup.md"
```

The script:

1. finds every image in the note — `![[...]]` embeds, `![](...)` links,
   `file:///...` absolute paths, and relative paths — and copies them into
   `writeups/<Name>/images/<name>/imgNN.png` in the order they appear;
2. converts the markdown to HTML and wraps it in the site template;
3. adds the entry to `posts.json`.

Optional flags:

```bash
python build.py "note.md" \
  --title "Box Name" \
  --date "Oct 2026" \
  --tag "HackTheBox" \
  --summary "Short card summary" \
  --machine-url "https://app.hackthebox.com/machines/Box"
```

If a relative/`file://` image can't be found, the script falls back to searching
the folders listed in `ATTACHMENT_ROOTS` at the top of `build.py` — point those
at your Obsidian vault attachment folders and your ShareX screenshots folder.

Then commit and push; GitHub Pages serves `index.html` at the root.
