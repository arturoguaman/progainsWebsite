#!/usr/bin/env python3
"""Builds the ProGains support + privacy site for GitHub Pages.

Output layout — the contents of `site/` become the published root, which for this
repository is https://progainssupport.github.io/progains/ :

    site/
      index.html          the Support page          -> /progains/
      privacy/index.html  the Privacy Policy        -> /progains/privacy
      css/styles.css
      assets/icon-*.png
      .nojekyll

`privacy/index.html` rather than `privacy.html` is what lets GitHub Pages serve a
clean `/progains/privacy` URL with no extension and no server-side routing, and it
is why refreshing that URL cannot 404.

Every path emitted is relative, so the site works unchanged whether it is published
at a repository subpath, at a user-site root, or opened from the local filesystem.

Both pages carry all nine translations in one file and select between them with the
URL fragment (`#ja`), which keeps one canonical URL per page for App Store Connect
while still giving every language a linkable address.
"""
import base64, json, pathlib, re, shutil

HERE = pathlib.Path(__file__).parent
SRC  = HERE / 'i18n'
OUT  = HERE / 'site'
ORDER = ['en', 'de', 'ja', 'es', 'fr', 'pt', 'it', 'zh', 'ko']

L = {c: json.loads((SRC / f'{c}.json').read_text(encoding='utf-8')) for c in ORDER}

# Where each page is written, and how it reaches shared assets and the other page.
# `self_href` is a bare fragment because a link to the page you are already on
# should not re-request it.
PAGES = {
    'support': {
        'out':        OUT / 'index.html',
        'asset':      '',            # index.html sits at the published root
        'self_href':  '#',
        'other_href': 'privacy/#',
    },
    'privacy': {
        'out':        OUT / 'privacy' / 'index.html',
        'asset':      '../',         # privacy/index.html is one level down
        'self_href':  '#',
        'other_href': '../#',
    },
}


def rewrite_links(html, page):
    """Point the cross-page links in translated section bodies at the built layout.

    The language files were authored against a flat `support.html` / `privacy.html`
    pair. Rewriting here keeps that source readable and means a future layout change
    is one edit in this function rather than 9 files x 20 sections.
    """
    support_href = PAGES[page]['self_href'] if page == 'support' else PAGES[page]['other_href']
    privacy_href = PAGES[page]['self_href'] if page == 'privacy' else PAGES[page]['other_href']
    html = html.replace('href="support.html#', f'href="{support_href}')
    html = html.replace('href="privacy.html#', f'href="{privacy_href}')
    return html


def switcher(active, page):
    out = ['<nav class="lang-switch" aria-label="Language">']
    for c in ORDER:
        d = L[c]
        cur = ' aria-current="true"' if c == active else ''
        out.append(f'<a href="#{c}" lang="{d["htmlLang"]}" hreflang="{d["htmlLang"]}"'
                   f' title="{d["name"]}"{cur}>{d["label"]}</a>')
    out.append('</nav>')
    return ''.join(out)


def block(code, page):
    d = L[code]
    p = d[page]
    cfg = PAGES[page]
    hl = d['htmlLang']
    support_href = cfg['self_href'] if page == 'support' else cfg['other_href']
    privacy_href = cfg['self_href'] if page == 'privacy' else cfg['other_href']

    s = [f'<div class="i18n" id="{code}" lang="{hl}">']

    s.append('<header class="site-header"><div class="wrap">')
    s.append(f'<a class="brand" href="{support_href}{code}" aria-label="ProGains">'
             f'<span class="brand-mark" aria-hidden="true"></span>'
             f'<span><span class="pro">Pro</span><span class="gains">Gains</span></span></a>')
    s.append(f'<nav class="site-nav" aria-label="{d["nav"]["label"]}">')
    for pg, href in (('support', support_href), ('privacy', privacy_href)):
        cur = ' aria-current="page"' if pg == page else ''
        s.append(f'<a href="{href}{code}"{cur}>{d["nav"][pg]}</a>')
    s.append('</nav>')
    s.append(switcher(code, page))
    s.append('</div></header>')

    s.append('<div class="hero"><div class="wrap">')
    s.append(f'<p class="eyebrow">{p["eyebrow"]}</p>')
    s.append(f'<h1>{p["h1"]}</h1>')
    s.append(f'<p class="lede">{p["lede"]}</p>')
    if page == 'support':
        s.append('<div class="btn-row">'
                 f'<a class="btn btn-primary" href="mailto:progains.support@gmail.com">{p["btnEmail"]}</a>'
                 f'<a class="btn btn-secondary" href="{privacy_href}{code}">{p["btnOther"]}</a>'
                 '</div>')
    else:
        s.append(f'<p class="updated">{p["updatedLabel"]} <strong>{p["updatedDate"]}</strong></p>')
    s.append('</div></div>')

    s.append(f'<main id="main-{code}"><div class="wrap">')
    s.append(f'<nav class="toc" aria-label="{p["tocLabel"]}"><h2>{p["tocLabel"]}</h2><ol>')
    for sec in p['sections']:
        s.append(f'<li><a href="#{sec["id"]}-{code}">{sec["h2"]}</a></li>')
    s.append('</ol></nav>')
    if page == 'privacy' and code != 'en' and d.get('langNote'):
        s.append(f'<div class="note lang-note"><p>{d["langNote"]}</p></div>')
    for sec in p['sections']:
        body = rewrite_links(sec['html'], page).replace('-en"', f'-{code}"')
        s.append(f'<section id="{sec["id"]}-{code}"><h2>{sec["h2"]}</h2>{body}</section>')
    s.append('</div></main>')

    s.append('<footer class="site-footer"><div class="wrap">')
    s.append(f'<p>&copy; 2026 ProGains. {d["footer"]["rights"]}</p>')
    s.append(f'<nav class="footer-nav" aria-label="{d["footer"]["label"]}">'
             f'<a href="{support_href}{code}">{d["nav"]["support"]}</a>'
             f'<a href="{privacy_href}{code}">{d["nav"]["privacy"]}</a>'
             f'<a href="mailto:progains.support@gmail.com">progains.support@gmail.com</a></nav>')
    s.append('</div></footer>')
    s.append('</div>')
    return '\n'.join(s)


def page(name):
    en = L['en'][name]
    a = PAGES[name]['asset']
    head = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{en["title"]}</title>
<meta name="description" content="{en["desc"]}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#F6F6F7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E1013" media="(prefers-color-scheme: dark)">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ProGains">
<meta property="og:locale" content="en_US">'''
    for c in ORDER:
        if c != 'en':
            head += f'\n<meta property="og:locale:alternate" content="{L[c]["ogLocale"]}">'
    head += f'''
<meta property="og:title" content="{en["title"]}">
<meta property="og:description" content="{en["desc"]}">
<meta property="og:image" content="{a}assets/icon-512.png">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{en["title"]}">
<meta name="twitter:description" content="{en["desc"]}">
<meta name="twitter:image" content="{a}assets/icon-512.png">
<link rel="icon" type="image/png" sizes="32x32" href="{a}assets/icon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="{a}assets/icon-512.png">
<link rel="apple-touch-icon" sizes="180x180" href="{a}assets/icon-180.png">
<link rel="stylesheet" href="{a}css/styles.css">
</head>
<body>
'''
    body = '\n'.join(block(c, name) for c in ORDER)
    return head + body + '\n</body>\n</html>\n'


# ---------------------------------------------------------------- build
# Prefer a clean rebuild so a renamed page can't leave a stale file behind. Some
# sandboxed environments deny unlink; fall back to overwriting in place rather than
# failing the build, and say so, because stale output is then possible.
if OUT.exists():
    try:
        shutil.rmtree(OUT)
    except PermissionError:
        print('note: could not clear site/ (no delete permission) — overwriting in place')
for sub in ('privacy', 'css', 'assets'):
    (OUT / sub).mkdir(parents=True, exist_ok=True)

for name in ('support', 'privacy'):
    out = PAGES[name]['out']
    out.write_text(page(name), encoding='utf-8')
    print(f'{out.relative_to(HERE)}  {out.stat().st_size:>8,} bytes')

# The brand mark rides in the stylesheet as one data URI rather than being repeated
# in nine header blocks on each page.
css = (HERE / 'styles.css').read_text(encoding='utf-8')
icon = base64.b64encode((HERE / 'icon-96.png').read_bytes()).decode()
marker = '/* __BRAND_MARK__ */'
rule = f'{marker}\n.brand-mark {{ background-image: url("data:image/png;base64,{icon}"); }}'
if marker in css:
    start = css.index(marker)
    end = css.index('\n', css.index('background-image', start)) + 1
    css = css[:start] + rule + '\n' + css[end:]
else:
    css += '\n\n' + rule + '\n'
(OUT / 'css' / 'styles.css').write_text(css, encoding='utf-8')
print(f"css/styles.css       {(OUT / 'css' / 'styles.css').stat().st_size:>8,} bytes")

for n in ('icon-32.png', 'icon-180.png', 'icon-512.png'):
    shutil.copy(HERE / n, OUT / 'assets' / n)
print(f'assets/              {len(list((OUT / "assets").iterdir()))} icons')

# Tells GitHub Pages to publish the tree as-is instead of running it through Jekyll,
# which would otherwise ignore any file or folder beginning with an underscore.
(OUT / '.nojekyll').write_text('', encoding='utf-8')
print('.nojekyll            written')
