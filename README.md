# Youssef Ashraf — Portfolio

A static portfolio for offensive/defensive security, built for GitHub Pages. It lists certifications, focus areas, and write-ups.

## Structure

```
index.html          # main portfolio page
posts.json          # write-up manifest (the site reads this to list write-ups)
writeups/
  Devhub/
    devhub.html
    images/devhub/img01.png ...
  Voleur/
    voleur.html
    images/voleur/img01.png ...
```

## How write-ups work

The site has **no server and no upload form**. That is deliberate: a static site has no upload surface, so there is nothing to exploit. Anyone can read write-ups; only you (through a git commit) can add one.

`index.html` fetches `posts.json` at load time and renders a card for every entry. Each entry points at a static HTML page.

```json
[
  {
    "title": "HTB: Voleur",
    "date": "Sep 2026",
    "tag": "HackTheBox",
    "summary": "One-line summary shown on the card.",
    "url": "writeups/Voleur/voleur.html"
  }
]
```

## Adding a write-up

1. Create a folder `writeups/<MachineName>/`.
2. Put the write-up page there as `writeups/<MachineName>/<machine>.html`.
3. Put its images under `writeups/<MachineName>/images/<machine>/img01.png`, `img02.png`, and so on, and reference them in the HTML as `images/<machine>/img01.png`.
4. Add one entry to `posts.json` with the title, date, tag, summary, and URL.
5. Commit and push. The list updates automatically — no rebuild needed.

Keep the write-up page consistent with the existing ones: copy the `<style>` block and the `<a class="back" href="../index.html">` header from `writeups/Devhub/devhub.html`, then swap in your own `<article>` content.

## Previewing locally

`posts.json` is loaded with `fetch`, which browsers block on the `file://` protocol. Serve the folder over HTTP instead:

```bash
# from the site root
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Security notes

- The site is fully static: no backend, no database, no server-side code, no upload endpoint.
- There are no credentials stored in the repository, and nothing client-side that grants write access.
- Write-ups render as hand-authored HTML. Only content you (or a collaborator with commit access) put in the repo is ever served, so there is no path for arbitrary uploads, path traversal, or remote code execution through the site.
