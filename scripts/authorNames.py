#!/usr/bin/env python3
"""Which written forms of an author's name refer to the same person, by
Wikidata identity rather than by spelling.

taxamatch.same_authorship settles formatting -- "and" / "&", initials,
particles, compound names, diacritics. It cannot settle that "DC." is
"de Candolle", "Vain." is "Wainio", or that "Walsingham" and "de Grey" are
one man (Thomas de Grey, 6th Baron Walsingham). Those were the commonest
same-year author disagreements left in the cross-family duplicates
(2026-10-31: 233 binomials Linnaeus/Linne, 184 Grey/Walsingham, 44 DC/Candolle).

The index is scripts/fetchAuthorIndex.py's Wikidata pull: IPNI abbreviations,
labels, family names and aliases, each normalised exactly like taxamatch's
author words, pointing at the QIDs that carry them. Two author forms are the
same person when their QID sets intersect and at least one side resolves to
exactly one QID -- a bare "Smith" names dozens of people and must not match
every one of them.

    idx = authorNames.load()
    authorNames.same_person(("DC",), ("CANDOLLE",), idx)   -> True
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources  # noqa: E402
import taxamatch  # noqa: E402

DEFAULT = os.path.join(sources.ROOT, "author-index", "wikidata-authors.json")


def _key(form):
    return " ".join(taxamatch._name_words(form))


# Which code a kingdom's names are cited under. "Walsingham" is a zoologist
# (Thomas de Grey) in a zoological citation and a botanist (Lesley
# Walsingham) in a botanical one; one index for both made each ambiguous.
CODE = {"animalia": "zoo", "plantae": "bot", "fungi": "bot", "chromista": "bot"}


def _in_code(rec, code):
    if code == "zoo":
        return bool(rec.get("zoobank") or rec.get("zoo"))
    if code == "bot":
        return bool(rec.get("ipni") or rec.get("abbr"))
    return True


def load(path=DEFAULT, code=None):
    """normalised name form -> {QID}. {} when the index has not been fetched,
    so callers degrade to spelling-only comparison rather than failing.
    `code`: "zoo", "bot" or None for both -- see CODE."""
    try:
        with open(path, encoding="utf-8") as fh:
            people = json.load(fh)["people"]
    except FileNotFoundError:
        return {}
    idx = collections.defaultdict(set)
    for qid, rec in people.items():
        if not _in_code(rec, code):
            continue
        # An abbreviation is indexed exactly, initials kept: "A.DC." is
        # Alphonse and "DC." his father, and dropping the initial made "DC"
        # name three Candolles.
        for abbr in (rec.get("abbr") or []) + (rec.get("zoo") or []):
            k = taxamatch.normalize_author(taxamatch._fold(abbr))
            if k:
                idx[" ".join(taxamatch._digraphs(w) for w in k.split())].add(qid)
        for form in (rec.get("family") or []) + (rec.get("aliases") or []):
            k = _key(form)
            if k:
                idx[k].add(qid)
                idx[k.split()[-1]].add(qid)
        if rec.get("label"):
            # Every surname word of the label, given name skipped: "Thomas de
            # Grey, 6th Baron Walsingham" answers to GREY and WALSINGHAM both.
            words = _key(rec["label"]).split()
            idx[" ".join(words)].add(qid)
            for w in words[1:] or words:
                idx[w].add(qid)
    return dict(idx)


def resolve(words, idx):
    """An author's word-tuple -> the QIDs it can name."""
    if not words:
        return set()
    return idx.get(" ".join(words), set()) | idx.get(words[-1], set())


def same_person(words_a, words_b, idx):
    """One side's candidates all lie within the other's: "DC" (one man) within
    "Candolle" (the family), "Linne" and "Linnaeus" (father and son, both
    ways). A partial overlap -- two common surnames that happen to share one
    person -- is not enough."""
    a, b = resolve(words_a, idx), resolve(words_b, idx)
    return bool(a) and bool(b) and (a <= b or b <= a)
