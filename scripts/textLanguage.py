#!/usr/bin/env python3
"""Decide whether a block of text is written in the portal's language.

The portal is an English interface, so a French or German taxonomic treatment is
not a usable description however good the prose is. 1,185 species were shipped
with one -- `Camponotus quadrilaterus` showed a reader German morphology for its
worker -- because the GBIF description fillers select on a record's `type` and
never look at language: a GBIF treatment is contributed text in whatever language
the source publication used, and GBIF neither translates nor tags it.

Counted by *distinct* function words per language, not by a stopword list,
because `die`, `des`, `el`, `lo` and `una` all occur inside ordinary English
words and inside species names, so one hit proves nothing. Three distinct
markers in one passage is a language rather than a coincidence.

Deliberately biased towards missing rather than over-firing. The remedy for a
false positive here is a cleared description, which is real data loss, while the
cost of a miss is one non-English description surviving -- the same position it
was in before this module existed.

This lives in one place because three files need the same verdict and three
copies of a word list drift apart, which is how the Spanish/Italian overlap below
went unnoticed until the Italian case failed its own test.
"""
import re

# Markers are chosen to be distinctive rather than merely frequent: `habitat`,
# `especie`, `una` and `habitat` are shared between Spanish and Italian and would
# make Spanish text report as Italian. Each list therefore leans on words the
# other Romance languages do not use.
FOREIGN_MARKERS = {
    "de": re.compile(
        r"\b(und|der|die|das|werden|wird|sich|durch|einen|einem|einer|eines|"
        r"ungefähr|Länge|Körper|Fühler|Flügel|Beine|Färbung|Männchen|"
        r"Weibchen|Gattung|unterscheidet|Merkmale|Kopf|Brust|Abdomen|"
        r"häufig|Größe)\b", re.I),
    "fr": re.compile(
        r"\b(le|les|une|des|est|sont|espèce|genre|famille|habitat|"
        r"répartition|phénologie|caractères|exemplaire|feuille|floraison|"
        r"longueur|largeur|description)\b", re.I),
    "es": re.compile(
        r"\b(el|los|las|una|uno|especie|género|familia|hábitat|distribución|"
        r"longitud|anchura|descripción|ejemplar|distribuye|habita|"
        r"floración|caracteres)\b", re.I),
    "it": re.compile(
        r"\b(della|delle|degli|dello|questa|questo|essere|sono|anche|"
        r"stazione|maschio|femmina|gambe|antenne|dimensioni|può|più|"
        r"lunghezza|larghezza|descrizione|genere|famiglia)\b", re.I),
}

MIN_FOREIGN_MARKERS = 3


def foreign_language(text):
    """ISO code of the language `text` is written in, or None if it reads as English."""
    if not text:
        return None
    for code, rx in FOREIGN_MARKERS.items():
        if len({m.group(0).lower() for m in rx.finditer(text)}) >= MIN_FOREIGN_MARKERS:
            return code
    return None
