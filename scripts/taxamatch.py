#!/usr/bin/env python3
"""Fuzzy name matching for scientific names, ported from the GlobalNames Ruby gems.

Two pieces, both from Tony Rees' Taxamatch and the GlobalNames Architecture:

- **Damerau-Levenshtein with block transpositions.** Not the ordinary
  Damerau variant: this one allows a *block* of up to `block_size` characters to
  be transposed with its neighbour at a cost of 1, following Boehmer & Rees
  2008. That matters for taxonomic names, where a misspelling is often a
  transposition of several adjacent letters -- "Pseudorhynchus" against
  "Pseudoryhnchus" -- which plain Levenshtein scores as several edits.
- **Taxamatch's decision logic.** Edit-distance thresholds scaled by name length,
  a phonetic fallback so names that merely sound alike still match, and an author
  check so two names spelled alike but published by different authors do not.

Ported from the gems rather than called from Ruby, because this project is Python
and shelling out per name pair is not an option at 1.3M names. The gems remain the
reference: `scripts/validateTaxamatch.py` checks this port against them.

Two deliberate differences from the original, both noted at their definitions:

- The gems atomize names with the `biodiversity` gem's Treetop grammar. This uses
  **GNparser** instead, which does the same job faster and reports cardinality,
  rank and authorship separately. Where the two parsers disagree about where a
  name's boundaries lie, results can differ -- measured rather than assumed.
- The gems mutate hash keys in place while matching (`genus1[0]`, `sp1[0]`). This
  does not, so repeated matching of the same pair is stable.
"""
import re
import subprocess
import unicodedata

__all__ = ["damerau_levenshtein", "Taxamatch", "parse_names", "normalize",
           "phonetize", "authmatch"]


# --------------------------------------------------------------------------
# Damerau-Levenshtein, ported from ext/damerau_levenshtein/damerau_levenshtein.c
# --------------------------------------------------------------------------
def damerau_levenshtein(str1, str2, block_size=1, max_distance=10):
    """Edit distance allowing transposition of blocks up to `block_size` long.

    Direct port of the C, including its quirks, because the quirks are load
    bearing: the single-character-length early return, the `block_size == 0`
    switch to pure Levenshtein, and the early exit that returns
    `current_distance` rather than the true value once a row exceeds
    `max_distance`. Keeping them means distances computed here are comparable
    with the gem's, which is what the validation script checks.

    Characters are compared as code points, matching the C's `unpack("U*")`.
    """
    s = list(str1)
    t = list(str2)
    pure_levenshtein = False
    if block_size == 0:
        pure_levenshtein = True
        block_size = 1

    sl, tl = len(s), len(t)
    if sl == 0:
        return tl
    if tl == 0:
        return sl
    # The C notes this case must be handled or the main loop indexes out of range.
    if sl == 1 and tl == 1 and s[0] != t[0]:
        return 1

    sl += 1
    tl += 1
    d = [0] * (sl * tl)
    for i in range(tl):
        d[i * sl] = i

    stop_execution = False
    current_distance = 0
    for i in range(1, sl):
        d[i] = i
        if stop_execution:
            break
        current_distance = 10000
        for j in range(1, tl):
            cost = 0 if s[i - 1] == t[j - 1] else 1
            half_sl = (sl - 1) // 2
            half_tl = (tl - 1) // 2
            block = block_size if (block_size < half_sl or half_sl == 0) else half_sl
            block = block if (block < half_tl or half_tl == 0) else half_tl

            while block >= 1:
                swap1 = swap2 = True
                i1 = i - block * 2
                j1 = j - block * 2
                # The C reads these cells before its `i >= 2*block && j >=
                # 2*block` guard, so near either end of the matrix it indexes
                # outside the arrays -- undefined behaviour whose result the
                # guard then discards. Loop 1 touches s[i1 .. i1+block) and
                # t[i1+block .. i1+2*block); loop 2 touches t[j1 .. j1+block) and
                # s[j1+block .. j1+2*block). Bounding all of it and calling an
                # out-of-range window "not a transposition" keeps real
                # transpositions scoring 1 and makes the port memory-safe.
                in_range = (i1 >= 0 and j1 >= 0
                            and i1 + block <= len(s) and i1 + 2 * block <= len(t)
                            and j1 + block <= len(t) and j1 + 2 * block <= len(s))
                if not in_range:
                    swap1 = swap2 = False
                else:
                    for k in range(i1, i1 + block):
                        if s[k] != t[k + block]:
                            swap1 = False
                            break
                    for k in range(j1, j1 + block):
                        if t[k] != s[k + block]:
                            swap2 = False
                            break

                mn = d[j * sl + i - 1] + 1
                ins = d[(j - 1) * sl + i] + 1
                if ins < mn:
                    mn = ins
                if (not pure_levenshtein and i >= 2 * block
                        and j >= 2 * block and swap1 and swap2):
                    transp = d[(j - block * 2) * sl + i - block * 2] + cost + block - 1
                    if transp < mn:
                        mn = transp
                    block = 0
                elif block == 1:
                    subs = d[(j - 1) * sl + i - 1] + cost
                    if subs < mn:
                        mn = subs
                block -= 1
            d[j * sl + i] = mn
            if current_distance > mn:
                current_distance = mn
        if current_distance > max_distance:
            stop_execution = True

    distance = d[sl * tl - 1]
    if stop_execution:
        distance = current_distance
    return distance


# --------------------------------------------------------------------------
# Normalizer -- ported verbatim from taxamatch_rb/normalizer.rb
# --------------------------------------------------------------------------
_FOLD = {
    "ÀÂÅÃÄÁẤẠÁáàâåãäăãắảạậầằá": "A",
    "ÉÈÊËéèêëĕěếệểễềẻ": "E",
    "ÍÌÎÏíìîïǐĭīĩỉï": "I",
    "ÓÒÔØÕÖỚỔóòôøõöŏỏỗộơọỡốơồờớổő": "O",
    "ÚÙÛÜúùûüůưừựủứụű": "U",
    "Ýýÿỹ": "Y",
    "Ææ": "AE",
    "ČÇčćç": "C",
    "ŠŞśšşſ": "S",
    "Đđð": "D",
    "Žžź": "Z",
    "Ññńň": "N",
    "Œœ": "OE",
    "ß": "B",
    "Ķ": "K",
    "ğ": "G",
    "Řř": "R",
}


def _utf8_to_ascii(string):
    string = re.sub(r"\s{2,}", " ", string)
    string = string.replace("×", "x")
    for src, dst in _FOLD.items():
        string = "".join(dst if ch in src else ch for ch in string)
    return string


def normalize(string):
    """Uppercase, strip accents, replace anything outside ASCII with '?'."""
    return re.sub(r"[^\x00-\x7F]", "?", _utf8_to_ascii((string or "").strip().upper()))


def normalize_word(word):
    return re.sub(r"[^A-Z0-9\-]", "", normalize(word)).strip()


def normalize_author(string):
    return re.sub(r"\s{2,}", " ", re.sub(r"[^A-Z]", " ", normalize(string))).strip()


def normalize_year(year_string):
    year = int(re.sub(r"[^\d]", "", year_string or "") or 0)
    if year == 0 or not (1757 <= year <= 2100):
        return None
    return year


# --------------------------------------------------------------------------
# Phonetizer -- ported from taxamatch_rb/phonetizer.rb
# --------------------------------------------------------------------------
_INITIAL = [("AE", "E"), ("CN", "N"), ("CT", "T"), ("CZ", "C"), ("DJ", "J"),
            ("EA", "E"), ("EU", "U"), ("GN", "N"), ("KN", "N"), ("MC", "MAC"),
            ("MN", "N"), ("OE", "E"), ("QU", "Q"), ("PS", "S"), ("PT", "T"),
            ("TS", "S"), ("WR", "R"), ("X", "Z")]


def normalize_ending(a_word):
    """Fold -is/-im/-as endings to -a so gender and case endings do not matter."""
    a_word = re.sub(r"IS$", "A", a_word)
    a_word = re.sub(r"IM$", "A", a_word)
    return re.sub(r"AS$", "A", a_word)


def phonetize(a_word, do_normalize_ending=False):
    """A crude phonetic encoding, so names that sound alike can still match."""
    a_word = normalize((a_word or "").strip())
    if a_word == "":
        return ""
    for prefix, repl in _INITIAL:
        if a_word.startswith(prefix):
            a_word = repl + a_word[len(prefix):]
            break
    first = a_word[0]
    rest = a_word[1:]
    rest = rest.replace("AE", "I").replace("IA", "A").replace("OE", "I")
    rest = rest.replace("OI", "A").replace("SC", "S").replace("H", "")
    rest = rest.translate(str.maketrans("EOUYKZ", "IAIICS"))
    out = ""
    for ch in first + rest:          # Ruby's String#squeeze
        if not out or out[-1] != ch:
            out += ch
    if do_normalize_ending and len(out) > 4:
        out = normalize_ending(out)
    return out


# --------------------------------------------------------------------------
# Authmatch -- ported from taxamatch_rb/authmatch.rb (Patrick Leary)
# --------------------------------------------------------------------------
def _fuzzy_match_authors(a1, a2):
    ed = damerau_levenshtein(a1, a2, 1, 3)
    return (ed <= 3 and min(len(a1), len(a2)) > ed * 2
            and (ed < 2 or a1[0] == a2[0]))


def _remove_duplicate_authors(authors1, authors2):
    u1, u2 = list(authors1), list(authors2)
    for au1 in authors1:
        for au2 in authors2:
            m1 = m2 = False
            if au1 == au2:
                m1 = m2 = True
            elif au1 == au2[:len(au1)]:
                m1 = True
            elif au2 == au1[:len(au2)]:
                m2 = True
            if ((len(au1) >= 3 and m1) or (len(au2) >= 3 and m2) or (m1 and m2)):
                if au1 in u1:
                    u1.remove(au1)
                if au2 in u2:
                    u2.remove(au2)
            elif m1:
                if au1 in u1:
                    u1.remove(au1)
            elif m2:
                if au2 in u2:
                    u2.remove(au2)
            elif (len(au1) > 1 and len(au2) > 1
                  and _fuzzy_match_authors(au1, au2)):
                if au1 in u1:
                    u1.remove(au1)
                if au2 in u2:
                    u2.remove(au2)
    return u1, u2


def _compare_years(years1, years2):
    if not years1 and not years2:
        return 0
    if len(years1) == 1 and len(years2) == 1:
        return abs(int(years1[0]) - int(years2[0]))
    return None


def authmatch(authors1, authors2, years1, years2):
    """0 means the authorship contradicts the name; non-zero is a score."""
    u1, u2 = _remove_duplicate_authors(authors1, authors2)
    year_diff = _compare_years(years1, years2)
    before = len(authors1) + len(authors2)
    after = len(u1) + len(u2)
    if after == 0:
        if year_diff is not None:
            score = 100 if year_diff == 0 else (54 if year_diff == 1 else 0)
        else:
            score = 94
    elif len(u1) == 0 or len(u2) == 0:
        if year_diff is not None:
            score = 91 if year_diff == 0 else (51 if year_diff == 1 else 0)
        else:
            score = 90
    else:
        score = round((1 - after / before) * 100)
        if not (year_diff is None or year_diff == 0):
            score = 0
    return score if score > 50 else 0


# --------------------------------------------------------------------------
# Atomization via GNparser, standing in for the gems' Treetop grammar
# --------------------------------------------------------------------------
def _find_gnparser():
    """Locate the gnparser binary: PATH first, then the Go bin directory.

    `go install` puts it in $GOPATH/bin, which is usually not on PATH, so a bare
    "gnparser" fails in exactly the situation where the tool was just installed.
    """
    import os
    import shutil
    found = shutil.which("gnparser")
    if found:
        return found
    for cand in (os.path.join(os.environ.get("GOPATH", ""), "bin", "gnparser"),
                 os.path.expanduser("~/go/bin/gnparser"),
                 "/usr/local/bin/gnparser", "/opt/homebrew/bin/gnparser"):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return "gnparser"


GNPARSER = _find_gnparser()
_SUBSP_MARKERS = (" subsp. ", " var. ", " forma ", " f. ")


def parse_names(names):
    """names -> {name: {'genus','species','infraspecies','authors','years'}} via GNparser.

    One GNparser invocation for the whole list; it is roughly 50,000 names a
    second, so per-name calls are not viable at this scale.
    """
    import csv
    import io
    import os
    import tempfile
    names = list(dict.fromkeys(n for n in names if n))
    if not names:
        return {}
    # gnparser takes a file path; passing "-" makes it parse the literal string
    # "-" as a name rather than reading stdin.
    fd, tmp = tempfile.mkstemp(prefix="gnparser-", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(names) + "\n")
        try:
            proc = subprocess.run([GNPARSER, tmp], capture_output=True,
                                  text=True, timeout=900)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(
                f"gnparser not usable ({e}). Install it with:\n"
                f"  go install github.com/gnames/gnparser/gnparser@latest") from e
        out = proc.stdout
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    res = {}
    for row in csv.DictReader(io.StringIO(out)):
        verbatim = (row.get("Verbatim") or "").strip()
        if not verbatim:
            continue
        full = (row.get("CanonicalFull") or "").strip()
        stem = (row.get("CanonicalStem") or "").strip()
        canon = full or stem
        genus = species = infraspecies = ""
        for marker in _SUBSP_MARKERS:
            if marker in canon:
                genus_species, infraspecies = canon.split(marker, 1)
                break
        else:
            genus_species = canon
        parts = genus_species.split()
        if len(parts) >= 2:
            genus, species = parts[0], parts[1]
            extra = parts[2:]
            if extra and not infraspecies:
                infraspecies = " ".join(extra)
        elif len(parts) == 1:
            genus = parts[0]
        auth = ((row.get("Authorship") or "").strip()
                .replace("(", "").replace(")", "").strip())
        authors = normalize_author(auth) if auth else ""
        year = normalize_year(row.get("Year") or "")
        res[verbatim] = {
            "genus": genus, "species": species,
            "infraspecies": infraspecies,
            "authors": [authors] if authors else [],
            "years": [year] if year else [],
        }
    return res


# --------------------------------------------------------------------------
# Decision logic -- ported from taxamatch_rb/base.rb
# --------------------------------------------------------------------------
class Taxamatch:
    def __init__(self, parsed=None):
        self.parsed = parsed or {}

    def atomize(self, name):
        if name not in self.parsed:
            self.parsed.update(parse_names([name]))
        return self.parsed.get(name)

    @staticmethod
    def _match_genera(g1, g2):
        n1, n2 = normalize(g1), normalize(g2)
        min_length = min(len(n1), len(n2))
        ed = damerau_levenshtein(n1, n2, 1, 3)
        if min_length == 0 or ed / min_length > 0.2:
            return {"edit_distance": ed, "phonetic_match": False, "match": False}
        if phonetize(g1) == phonetize(g2):
            return {"edit_distance": ed, "phonetic_match": True, "match": True}
        match = (ed <= 3 and min_length > ed * 2
                 and (ed < 2 or n1[0] == n2[0]))
        return {"edit_distance": ed, "match": match, "phonetic_match": False}

    @staticmethod
    def _match_species(s1, s2):
        n1, n2 = normalize(s1), normalize(s2)
        min_length = min(len(n1), len(n2))
        ed = damerau_levenshtein(n1, n2, 1, 4)
        if min_length == 0 or ed / min_length > 0.3334:
            return {"edit_distance": ed, "phonetic_match": False, "match": False}
        p1 = normalize_ending(phonetize(s1, True))
        p2 = normalize_ending(phonetize(s2, True))
        if p1 == p2:
            return {"edit_distance": ed, "phonetic_match": True, "match": True}
        match = (ed <= 4 and min_length >= ed * 2
                 and (ed < 2 or n1[0] == n2[0])
                 and (ed < 4 or n1[0:3] == n2[0:3]))
        return {"edit_distance": ed, "match": match, "phonetic_match": False}

    def match(self, name1, name2):
        """True when the two strings denote the same taxon.

        Mirrors base.rb, including refusing to match a species against its own
        subspecies: an infraspecific name on one side only is a rank mismatch,
        not a spelling variant.
        """
        p1, p2 = self.atomize(name1), self.atomize(name2)
        if not p1 or not p2:
            return False
        if p1["genus"] and p2["genus"]:
            gm = self._match_genera(p1["genus"], p2["genus"])
            sm = self._match_species(p1["species"], p2["species"])
            result = dict(sm)
            if p1["infraspecies"] and p2["infraspecies"]:
                im = self._match_species(p1["infraspecies"], p2["infraspecies"])
                result["edit_distance"] += im["edit_distance"]
                result["match"] = result["match"] and im["match"]
            elif p1["infraspecies"] or p2["infraspecies"]:
                return False
            result["edit_distance"] += gm["edit_distance"]
            if result["edit_distance"] > 4:
                result["match"] = False
            result["match"] = result["match"] and gm["match"]
        elif p1["genus"] or p2["genus"]:
            return False                      # one binomial, one uninomial
        else:
            result = dict(self._match_genera(p1["genus"] or name1,
                                             p2["genus"] or name2))
        if result.get("match"):
            src1 = p1 if p1["infraspecies"] or p2["infraspecies"] else (
                p1 if p1["species"] else p1)
            src2 = p2 if p1["infraspecies"] or p2["infraspecies"] else (
                p2 if p2["species"] else p2)
            if authmatch(src1["authors"], src2["authors"],
                         src1["years"], src2["years"]) == 0:
                result["match"] = False
        return bool(result.get("match"))
