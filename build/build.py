#!/usr/bin/env python3
"""
Génère les pages statiques du site à partir des sources Markdown de content/.

    python3 build/build.py

Le contenu éditorial vit dans content/*.md. Le gabarit (en-tête, pied de page,
métadonnées) est décrit ici. La page d'accueil est un cas à part : son corps est
conservé tel quel dans build/index.body.html, parce qu'il s'agit de mise en page
et non de texte rédactionnel.

Aucune dépendance externe : le convertisseur Markdown ci-dessous couvre le
sous-ensemble effectivement utilisé par les sources.
"""

import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Tout ce qui est servi vit dans public/ ; les sources restent hors de portée du web.
OUT = os.path.join(ROOT, "public")

# --------------------------------------------------------------------------
# Configuration — un seul endroit à modifier
# --------------------------------------------------------------------------

SITE_URL = "https://naturalisation.hasakistudio.fr"
CONTACT_EMAIL = "contact@hasakistudio.fr"
STUDIO = "Hasaki Studio"
ANNEE = "2026"

# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

PAGES = [
    {
        "slug": "index",
        "url": "/",
        "body_file": "build/index.body.html",
        "title": "Entretien naturalisation : révision avec des fiches claires | Hasaki Studio",
        "description": (
            "Révision de l'entretien de naturalisation française : fiches claires "
            "basées sur le Livret du citoyen 2026, sans quiz ni score. "
            "Application Android bientôt disponible."
        ),
        "og_title": "Réussir mon entretien de naturalisation",
        "og_description": (
            "Préparez votre entretien de naturalisation sereinement grâce à des "
            "fiches de révision claires, basées sur le Livret du citoyen 2026."
        ),
        "priority": "1.0",
    },
    {
        "slug": "conseils-de-revision",
        "url": "/conseils-de-revision",
        "source": "content/conseils-de-revision.md",
        "eyebrow": "Préparation",
        "h1": "Conseils de révision",
        "title": "Conseils de révision pour l'entretien de naturalisation | Hasaki Studio",
        "description": (
            "Comment préparer l'entretien de naturalisation : liens officiels, "
            "étapes après la convocation, et méthode de révision efficace."
        ),
        "priority": "0.8",
    },
    {
        "slug": "contact",
        "url": "/contact",
        "source": "content/contact.md",
        "eyebrow": "Nous écrire",
        "h1": "Contact",
        "title": "Contact — Réussir mon entretien de naturalisation | Hasaki Studio",
        "description": (
            "Signaler une erreur dans une fiche, un problème technique ou une "
            "question sur vos données personnelles."
        ),
        "priority": "0.5",
    },
    {
        "slug": "confidentialite",
        "url": "/confidentialite",
        "source": "content/confidentialite.md",
        "eyebrow": "Vos données",
        "h1": "Politique de confidentialité",
        "title": "Politique de confidentialité — Réussir mon entretien | Hasaki Studio",
        "description": (
            "Politique de confidentialité de l'application « Réussir mon entretien » : "
            "données traitées, bases légales, consentements et vos droits."
        ),
        "priority": "0.5",
    },
    {
        "slug": "404",
        "url": "/404",
        "source": "content/404.md",
        "eyebrow": "Erreur 404",
        "h1": "Cette page n'existe pas",
        "title": "Page introuvable — Hasaki Studio",
        "description": "La page demandée n'existe pas ou a été déplacée.",
        "priority": "0.0",
        "sitemap": False,
    },
    {
        "slug": "mentions-legales",
        "url": "/mentions-legales",
        "source": "content/mentions-legales.md",
        "eyebrow": "Informations légales",
        "h1": "Mentions légales",
        "title": "Mentions légales — Réussir mon entretien | Hasaki Studio",
        "description": (
            "Mentions légales de l'application « Réussir mon entretien » éditée par "
            "Hasaki Studio : éditeur, hébergeur, responsabilité et propriété intellectuelle."
        ),
        "priority": "0.5",
    },
]

# --------------------------------------------------------------------------
# Convertisseur Markdown (sous-ensemble)
# --------------------------------------------------------------------------


def _inline(text):
    """Applique le formatage en ligne, en protégeant d'abord le code."""
    placeholders = []

    def stash(markup):
        placeholders.append(markup)
        return "\x00%d\x00" % (len(placeholders) - 1)

    # `code`
    text = re.sub(
        r"`([^`]+)`",
        lambda m: stash("<code>%s</code>" % html.escape(m.group(1))),
        text,
    )

    text = html.escape(text, quote=False)

    # [libellé](url)
    def link(m):
        label, href = m.group(1), m.group(2)
        external = href.startswith("http")
        attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return stash('<a href="%s"%s>%s</a>' % (html.escape(href, quote=True), attrs, label))

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)

    # **gras**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    # *italique* — un emplacement à compléter reçoit un traitement visuel dédié
    def italic(m):
        inner = m.group(1)
        if inner.lstrip().startswith("[") or "À COMPLÉTER" in inner or "à vérifier" in inner:
            return '<span class="todo">%s</span>' % inner
        return "<em>%s</em>" % inner

    text = re.sub(r"\*([^*]+)\*", italic, text)

    for i, markup in enumerate(placeholders):
        text = text.replace("\x00%d\x00" % i, markup)
    return text


def _table(rows):
    head, body = rows[0], rows[2:]
    out = ['<div class="table-wrap"><table><thead><tr>']
    out += ["<th>%s</th>" % _inline(c) for c in head]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>" + "".join("<td>%s</td>" % _inline(c) for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def _split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_to_html(md):
    lines = md.split("\n")
    out, i = [], 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Titre de niveau 1 : consommé par le gabarit, pas rendu ici
        if stripped.startswith("# "):
            i += 1
            continue

        if stripped.startswith("### "):
            out.append("<h3>%s</h3>" % _inline(stripped[4:]))
            i += 1
            continue

        if stripped.startswith("## "):
            out.append("<h2>%s</h2>" % _inline(stripped[3:]))
            i += 1
            continue

        if re.fullmatch(r"-{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        # Tableau
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1
            out.append(_table(rows))
            continue

        # Citation
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % _inline(" ".join(buf)))
            continue

        # Listes
        bullet = re.match(r"^[-*]\s+(.*)", stripped)
        number = re.match(r"^\d+\.\s+(.*)", stripped)
        if bullet or number:
            tag = "ul" if bullet else "ol"
            pattern = r"^[-*]\s+(.*)" if bullet else r"^\d+\.\s+(.*)"
            items = []
            while i < n:
                cur = lines[i].strip()
                m = re.match(pattern, cur)
                if m:
                    items.append(m.group(1))
                    i += 1
                elif cur and not re.match(r"^([-*]|\d+\.)\s", cur) and not cur.startswith(("#", ">", "|")):
                    # continuation d'un item sur la ligne suivante
                    if items:
                        items[-1] += " " + cur
                        i += 1
                    else:
                        break
                else:
                    break
            out.append(
                "<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % _inline(x) for x in items), tag)
            )
            continue

        # Paragraphe
        buf = []
        while i < n and lines[i].strip() and not re.match(
            r"^\s*(#{1,3}\s|[-*]\s|\d+\.\s|>|\||-{3,}$)", lines[i]
        ):
            buf.append(lines[i].strip())
            i += 1
        para = " ".join(buf)
        cls = ' class="updated"' if para.startswith("*Dernière mise à jour") else ""
        out.append("<p%s>%s</p>" % (cls, _inline(para)))

    return "\n".join(out)


# --------------------------------------------------------------------------
# Gabarit
# --------------------------------------------------------------------------

HEADER = """<header class="border-b border-ligne bg-blanc-casse">
<div aria-hidden="true" class="flex h-1 w-full"><div class="flex-1 bg-bleu-nuit"></div><div class="flex-1 bg-papier"></div><div class="flex-1 bg-rouge"></div></div>
<nav aria-label="Navigation principale" class="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-5 py-4">
<a href="/" style="font-family:var(--font-display)" class="flex items-center gap-2.5 font-display text-lg text-bleu-nuit"><span aria-hidden="true" class="inline-flex overflow-hidden rounded-[2px] border border-ligne align-middle" style="height:14px;width:21px"><span class="h-full flex-1" style="background-color:#1C2B49"></span><span class="h-full flex-1" style="background-color:#FCFAF5"></span><span class="h-full flex-1" style="background-color:#A62B2B"></span></span>Hasaki Studio</a>
<ul class="flex items-center gap-5 text-sm text-ardoise">
<li><a class="hover:text-bleu-nuit" href="/#application">L'application</a></li>
<li><a class="hover:text-bleu-nuit" href="/#themes">Thèmes</a></li>
<li><a class="hover:text-bleu-nuit" href="/contact">Contact</a></li>
</ul></nav></header>"""

FOOTER = """<footer class="bg-bleu-nuit text-papier">
<div class="mx-auto max-w-5xl px-5 py-12">
<p class="text-lg" style="font-family:var(--font-display);font-weight:600">{studio}</p>
<ul class="mt-5 flex flex-wrap gap-x-8 gap-y-3 text-sm">
<li><a href="/mentions-legales" class="underline-offset-4 hover:underline">Mentions légales</a></li>
<li><a href="/confidentialite" class="underline-offset-4 hover:underline">Politique de confidentialité</a></li>
<li><a href="/conseils-de-revision" class="underline-offset-4 hover:underline">Conseils de révision</a></li>
<li><a href="/contact" class="underline-offset-4 hover:underline">Contact</a></li>
</ul>
<p class="mt-8 text-xs text-papier/70">© {annee} {studio}. Application indépendante, non affiliée au ministère de l'Intérieur.</p>
</div></footer>""".format(studio=STUDIO, annee=ANNEE)

TOGGLE_SCRIPT = '<script src="/assets/site.js" defer></script>'

# Données structurées. L'organisation figure sur toutes les pages ; la fiche
# application seulement sur l'accueil. Volontairement limité aux faits
# vérifiables : ni prix, ni note, ni nombre d'avis.
ORGANISATION = {
    "@type": "Organization",
    "name": STUDIO,
    "url": SITE_URL + "/",
    "email": CONTACT_EMAIL,
}

APPLICATION = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Réussir mon entretien",
    "applicationCategory": "EducationalApplication",
    "operatingSystem": "Android",
    "inLanguage": "fr-FR",
    "description": (
        "Fiches de révision pour préparer l'entretien de naturalisation française, "
        "basées sur le Livret du citoyen 2026."
    ),
    "publisher": ORGANISATION,
}

SHELL = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="{studio}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_description}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_description}">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/site.css">
{jsonld}</head>
<body>
<div class="min-h-screen bg-blanc-casse">
{header}
{main}
{footer}
</div>
{script}
</body>
</html>
"""

ARTICLE = """<main>
<article class="mx-auto max-w-3xl px-5 py-14 sm:py-20">
<p class="eyebrow">{eyebrow}</p>
<h1 class="mt-3 text-[32px] text-bleu-nuit" style="font-family:var(--font-display);font-weight:600">{h1}</h1>
<div class="prose mt-8">
{content}
</div>
</article>
</main>"""


def normalise_links(markup):
    """./page.html -> /page, et ./index.html -> / .

    Cloudflare Pages sert confidentialite.html sur /confidentialite et redirige
    l'URL en .html en 301. Pointer directement sur l'URL propre évite ce saut.
    """
    markup = re.sub(r'href="\.?/?index\.html"', 'href="/"', markup)
    return re.sub(r'href="\.?/?([a-z0-9-]+)\.html"', r'href="/\1"', markup)


def build():
    written = []
    for page in PAGES:
        if "body_file" in page:
            main = normalise_links(
                open(os.path.join(ROOT, page["body_file"]), encoding="utf-8").read()
            )
        else:
            md = open(os.path.join(ROOT, page["source"]), encoding="utf-8").read()
            main = ARTICLE.format(
                eyebrow=html.escape(page["eyebrow"]),
                h1=html.escape(page["h1"]),
                content=md_to_html(md),
            )

        canonical = SITE_URL + page["url"]
        data = APPLICATION if page["slug"] == "index" else dict(
            ORGANISATION, **{"@context": "https://schema.org"}
        )
        jsonld = '<script type="application/ld+json">%s</script>\n' % json.dumps(
            data, ensure_ascii=False, separators=(",", ":")
        )
        doc = SHELL.format(
            jsonld=jsonld,
            title=html.escape(page["title"], quote=True),
            description=html.escape(page["description"], quote=True),
            canonical=canonical,
            studio=STUDIO,
            og_title=html.escape(page.get("og_title", page["title"]), quote=True),
            og_description=html.escape(
                page.get("og_description", page["description"]), quote=True
            ),
            header=HEADER,
            main=main,
            footer=FOOTER,
            script=TOGGLE_SCRIPT,
        )

        path = os.path.join(OUT, page["slug"] + ".html")
        open(path, "w", encoding="utf-8").write(doc)
        written.append((page["slug"] + ".html", len(doc)))

    # sitemap.xml
    urls = "\n".join(
        '  <url><loc>%s%s</loc><priority>%s</priority></url>'
        % (SITE_URL, p["url"], p["priority"])
        for p in PAGES
        if p.get("sitemap", True)
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls
        + "\n</urlset>\n"
    )
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(sitemap)

    # robots.txt
    robots = "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL
    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(robots)

    for name, size in written:
        print("%-28s %6d octets" % (name, size))
    print("%-28s" % "sitemap.xml")
    print("%-28s" % "robots.txt")


if __name__ == "__main__":
    build()
