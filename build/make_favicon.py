#!/usr/bin/env python3
"""
Fabrique les icônes du site à partir de la marque Hasaki Studio : le bloc
tricolore repris de l'en-tête.

    python3 build/make_favicon.py

Produit public/favicon.svg (net à toute taille, utilisé par les navigateurs
récents), public/favicon.ico (repli, 16/32/48 px) et public/apple-touch-icon.png
(écran d'accueil iOS).

Aucune dépendance : le PNG est encodé à la main avec zlib, l'ICO encapsule
directement ces PNG.

Le contour sombre n'est pas décoratif : sans lui, la bande centrale claire se
confond avec le fond blanc d'un onglet et la marque paraît coupée en deux.
"""

import os
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public")

BLEU = (0x1C, 0x2B, 0x49)
PAPIER = (0xF6, 0xF3, 0xEC)  # blanc cassé : se détache d'un onglet blanc
ROUGE = (0xA6, 0x2B, 0x2B)

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" role="img" aria-label="Hasaki Studio">
  <defs>
    <clipPath id="c"><rect x="1" y="1" width="30" height="30" rx="6.5"/></clipPath>
  </defs>
  <g clip-path="url(#c)">
    <rect x="1" y="1" width="10" height="30" fill="#1C2B49"/>
    <rect x="11" y="1" width="10" height="30" fill="#F6F3EC"/>
    <rect x="21" y="1" width="10" height="30" fill="#A62B2B"/>
  </g>
  <rect x="1" y="1" width="30" height="30" rx="6.5" fill="none"
        stroke="#000000" stroke-opacity="0.22" stroke-width="1.2"/>
</svg>
"""


def _edge_distance(x, y, size, radius):
    """Distance signée au bord du carré arrondi. Négative à l'intérieur."""
    cx = min(max(x, radius), size - radius)
    cy = min(max(y, radius), size - radius)
    dx, dy = x - cx, y - cy
    return (dx * dx + dy * dy) ** 0.5 - radius


def render(size, supersample=4):
    """Rend l'icône en RGBA, anti-aliasée par sur-échantillonnage."""
    s = size * supersample
    radius = s * 0.20
    border = max(1.0, s * 0.035)
    n = supersample * supersample
    rows = []

    for py in range(size):
        row = bytearray()
        for px in range(size):
            r_acc = g_acc = b_acc = hits = 0
            for sy in range(supersample):
                for sx in range(supersample):
                    x = px * supersample + sx + 0.5
                    y = py * supersample + sy + 0.5
                    d = _edge_distance(x, y, s, radius)
                    if d > 0:
                        continue  # hors de la forme
                    band = min(int(x * 3 / s), 2)
                    col = (BLEU, PAPIER, ROUGE)[band]
                    if d > -border:
                        # Liseré fin, obtenu en assombrissant la bande sous-jacente.
                        # Il délimite la bande claire sur un onglet blanc sans
                        # élargir visuellement la bande bleue, ce qu'un liseré
                        # bleu nuit uniforme provoquait.
                        col = tuple(round(c * 0.78) for c in col)
                    r_acc += col[0]
                    g_acc += col[1]
                    b_acc += col[2]
                    hits += 1
            if hits == 0:
                row += bytes((0, 0, 0, 0))
            else:
                row += bytes((r_acc // hits, g_acc // hits, b_acc // hits, 255 * hits // n))
        rows.append(bytes(row))
    return rows


def png(rows, size):
    """Encode des lignes RGBA en PNG."""
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def ico(images):
    """Encapsule des PNG dans un conteneur ICO."""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries, blobs = b"", b""
    for size, data in images:
        entries += struct.pack(
            "<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset
        )
        blobs += data
        offset += len(data)
    return header + entries + blobs


def main():
    open(os.path.join(OUT, "favicon.svg"), "w", encoding="utf-8").write(SVG)

    images = [(s, png(render(s), s)) for s in (16, 32, 48)]
    open(os.path.join(OUT, "favicon.ico"), "wb").write(ico(images))

    touch = png(render(180), 180)
    open(os.path.join(OUT, "apple-touch-icon.png"), "wb").write(touch)

    print("favicon.svg           %6d octets" % len(SVG))
    print("favicon.ico           %6d octets (16, 32, 48 px)" % os.path.getsize(os.path.join(OUT, "favicon.ico")))
    print("apple-touch-icon.png  %6d octets (180 px)" % len(touch))


if __name__ == "__main__":
    main()
