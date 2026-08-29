#!/usr/bin/env python3
"""Builds support.html and privacy.html from i18n/<lang>.json.

Both pages carry all nine languages in one file. Language selection is pure CSS
(:target + :has), so there is no JavaScript and the chosen language lives in the
URL fragment -- which means privacy.html#ja is a real, linkable Japanese page.
"""
import base64, json, pathlib

HERE = pathlib.Path(__file__).parent
ORDER = ['en', 'de', 'ja', 'es', 'fr', 'pt', 'it', 'zh', 'ko']

L = {c: json.loads((HERE / 'i18n' / f'{c}.json').read_text(encoding='utf-8')) for c in ORDER}

ICON = base64.b64encode((HERE / 'icon-96.png').read_bytes()).decode()


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
    other = 'privacy' if page == 'support' else 'support'
    hl = d['htmlLang']
    s = [f'<div class="i18n" id="{code}" lang="{hl}">']

    # header
    s.append('<header class="site-header"><div class="wrap">')
    s.append(f'<a class="brand" href="#{code}" aria-label="ProGains">'
             f'<span class="brand-mark" aria-hidden="true"></span>'
             f'<span><span class="pro">Pro</span><span class="gains">Gains</span></span></a>')
    s.append('<nav class="site-nav" aria-label="'+d['nav']['label']+'">')
    for pg, fn in (('support', 'support.html'), ('privacy', 'privacy.html')):
        cur = ' aria-current="page"' if pg == page else ''
        s.append(f'<a href="{fn}#{code}"{cur}>{d["nav"][pg]}</a>')
    s.append('</nav>')
    s.append(switcher(code, page))
    s.append('</div></header>')

    # hero
    s.append('<div class="hero"><div class="wrap">')
    s.append(f'<p class="eyebrow">{p["eyebrow"]}</p>')
    s.append(f'<h1>{p["h1"]}</h1>')
    s.append(f'<p class="lede">{p["lede"]}</p>')
    if page == 'support':
        s.append('<div class="btn-row">'
                 f'<a class="btn btn-primary" href="mailto:progains.support@gmail.com">{p["btnEmail"]}</a>'
                 f'<a class="btn btn-secondary" href="privacy.html#{code}">{p["btnOther"]}</a>'
                 '</div>')
    else:
        s.append(f'<p class="updated">{p["updatedLabel"]} <strong>{p["updatedDate"]}</strong></p>')
    s.append('</div></div>')

    # main
    s.append(f'<main id="main-{code}"><div class="wrap">')
    s.append(f'<nav class="toc" aria-label="{p["tocLabel"]}"><h2>{p["tocLabel"]}</h2><ol>')
    for sec in p['sections']:
        s.append(f'<li><a href="#{sec["id"]}-{code}">{sec["h2"]}</a></li>')
    s.append('</ol></nav>')
    # Non-English legal pages state which version governs.
    if page == 'privacy' and code != 'en' and d.get('langNote'):
        s.append(f'<div class="note lang-note"><p>{d["langNote"]}</p></div>')
    for sec in p['sections']:
        s.append(f'<section id="{sec["id"]}-{code}"><h2>{sec["h2"]}</h2>{sec["html"]}</section>')
    s.append('</div></main>')

    # footer
    s.append('<footer class="site-footer"><div class="wrap">')
    s.append(f'<p>&copy; 2026 ProGains. {d["footer"]["rights"]}</p>')
    s.append(f'<nav class="footer-nav" aria-label="{d["footer"]["label"]}">'
             f'<a href="support.html#{code}">{d["nav"]["support"]}</a>'
             f'<a href="privacy.html#{code}">{d["nav"]["privacy"]}</a>'
             f'<a href="mailto:progains.support@gmail.com">progains.support@gmail.com</a></nav>')
    s.append('</div></footer>')
    s.append('</div>')
    return '\n'.join(s)


def page(name):
    en = L['en'][name]
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
<meta property="og:image" content="icon-512.png">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{en["title"]}">
<meta name="twitter:description" content="{en["desc"]}">
<meta name="twitter:image" content="icon-512.png">
<link rel="icon" type="image/png" sizes="32x32" href="icon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-512.png">
<link rel="apple-touch-icon" sizes="180x180" href="icon-180.png">
<link rel="stylesheet" href="styles.css">
</head>
<body>
'''
    body = '\n'.join(block(c, name) for c in ORDER)
    return head + body + '\n</body>\n</html>\n'


for n in ('support', 'privacy'):
    out = HERE / f'{n}.html'
    out.write_text(page(n), encoding='utf-8')
    print(f'{n}.html  {out.stat().st_size:>7,} bytes')

# The brand mark rides in the stylesheet as one data URI rather than being
# repeated in nine header blocks per page.
css = (HERE / 'styles.css').read_text(encoding='utf-8')
marker = '/* __BRAND_MARK__ */'
rule = (marker + '\n.brand-mark { background-image: url("data:image/png;base64,'
        + ICON + '"); }')
if marker in css:
    start = css.index(marker)
    end = css.index('\n', css.index('background-image', start)) + 1
    css = css[:start] + rule + '\n' + css[end:]
else:
    css += '\n\n' + rule + '\n'
(HERE / 'styles.css').write_text(css, encoding='utf-8')
print(f'styles.css {(HERE / "styles.css").stat().st_size:>6,} bytes (brand mark embedded)')
