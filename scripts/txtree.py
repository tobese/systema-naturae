#!/usr/bin/env python3
"""Reader for ChecklistBank's TextTree format (.txtree, or .tree): an
indentation tree with inline rank tags and info blocks.

2026-10-31: no longer one file. Four more archives in the queue carry it --
European Butterflies (303328), Fossil Birds of Australia (274271, a
`.tree` member), Archis botany (53677), the algae reprise (304685) -- each
using parts of the format BioLib doesn't: `=` for a synonym and `$` for a
basionym, `{PUB=...}` info blocks, `# comments`, a `†` prefix, and accepted
lines with no [rank] at all (274271's species are bare binomials). Those are
handled below; colChecklist.load() now dispatches here.

The original notes, from when BioLib was the only example:

The sole known example on the shelf is BioLib Coccinellidae (54592, a
worldwide ladybird beetle classification) -- grep confirms no other
archive carries a `.txtree` member. That is why this is its own small
module rather than a branch bolted onto colChecklist.py's dispatcher: the
same reasoning that keeps coldp.py (one container family) separate from
colChecklist.py's own several (DwCA/ILDIS/EUNIS/...) applies a second time
here, for a shape with exactly one real-world instance to generalise from.
If a second `.txtree` archive ever turns up, wiring this in via load()'s
return shape (which already matches colChecklist.load()'s (taxa, names,
meta)) is the natural next step then, grounded in a second real example
rather than a speculative one now.

Format, verified against the full 2988-line file, not a sample:

  - One taxon per line, 2 spaces of indentation per rank level.
  - An accepted name is "<name> <authorship>? [<rank>]", optionally
    followed by "{VERN=lang:name,lang:name,...}". How many of the leading
    words are the name vs. the authorship depends on rank -- a uninomial
    (1 word) at genus and above, a binomial (2) at species, a trinomial
    (3) at subspecies/variety/form -- ordinary binomial nomenclature, not
    something the file states explicitly, so getting the count wrong
    would silently swap words between the two fields. Checked against
    every accepted line in the real file (zero anomalies) before trusting
    it rank by rank, below.
  - A synonym/historical name starts with "*" and carries no [rank] tag at
    all. It sits at the same indentation depth as the accepted siblings
    around it, so its *contextual* rank (what it's a historical name
    for) is recoverable from that depth -- but checked against the whole
    file, synonym lines appear at every depth including species and
    subspecies, with word counts up to 7, so there is no reliable
    name/authorship split for them the way there is for an accepted line.
    Guessing one would risk exactly the kind of silently-wrong answer the
    WCVP fix (colChecklist.py, _rows()) exists to avoid. The untouched
    text is kept as `raw_name` instead of being forced into `name` +
    `authorship`.
"""
import re

# Leading-word count per rank, i.e. where the name ends and authorship
# begins on an ACCEPTED line. Only the ranks actually present in the one
# known real file are listed; an unrecognized rank raises rather than
# guessing a word count, so a second .txtree archive with a rank outside
# this set fails loudly instead of silently misreading every row at that
# rank the way the dispatch gaps fixed earlier tonight did.
RANK_NAME_WORDS = {
    "kingdom": 1, "phylum": 1, "subphylum": 1, "superclass": 1, "class": 1,
    "subclass": 1, "infraclass": 1, "parvclass": 1, "superorder": 1,
    "order": 1, "suborder": 1, "infraorder": 1, "parvorder": 1,
    "superfamily": 1, "family": 1, "subfamily": 1, "tribe": 1, "subtribe": 1,
    "genus": 1, "subgenus": 1, "section": 1,
    "species": 2,
    "subspecies": 3, "variety": 3, "form": 3,
}

_INFO_RE = re.compile(r"\s*\{(?P<key>[A-Z]+)=(?P<val>[^{}]*)\}\s*$")
_RANK_RE = re.compile(r"\s*\[(?P<rank>[a-zA-Z_ ]+)\]\s*$")
_COMMENT_RE = re.compile(r"\s+#.*$")

# Lowercase words that open an authorship rather than continue a name
# ("Pelicanus proavus de Vis, 1892" is a binomial, not a trinomial).
_AUTHOR_PARTICLES = {"de", "da", "das", "del", "della", "der", "den", "di",
                     "du", "dos", "la", "le", "ter", "van", "von", "zu"}


def _parse_vernacular(raw):
    """"lang:name,lang:name" -> [{"language": ..., "name": ...}, ...]."""
    out = []
    for pair in raw.split(","):
        if ":" not in pair:
            continue
        lang, name = pair.split(":", 1)
        out.append({"language": lang.strip(), "name": name.strip()})
    return out


def _infer_rank(words):
    """Rank for an accepted line that carries no [rank] tag, or None.

    Only the cases the name itself settles: a binomial (second word a
    lowercase epithet) is a species, and a third lowercase epithet makes it
    a subspecies. A bare uninomial stays None rather than being guessed
    from its ending -- nothing downstream needs its rank, since
    colChecklist.chain() only reads ranks that are tagged.
    """
    def epithet(w):
        return (w[:1].islower() and w not in _AUTHOR_PARTICLES
                and w.replace("-", "").isalpha())
    if len(words) >= 2 and words[0][:1].isupper() and epithet(words[1]):
        if len(words) >= 3 and epithet(words[2]):
            return "subspecies"
        return "species"
    return None


def _parse_line(content):
    """One stripped-of-indentation line -> a taxon dict, minus id/parent.

    `content` still carries a leading "*" for a synonym line; indentation
    (and therefore depth/parent) is the caller's job, not this function's,
    since a single line carries no idea of its own position in the tree.
    """
    content = _COMMENT_RE.sub("", content)
    # "*" is BioLib's synonym marker, "=" (or homotypic "≡") the TextTree
    # spec's; "$" after it flags the basionym, which is still a synonym here.
    is_synonym = content[:1] in ("*", "=", "≡")
    if is_synonym:
        content = content[1:].lstrip("$")
    extinct = content.startswith("†")
    if extinct:
        content = content[1:]

    vern = []
    while True:
        m = _INFO_RE.search(content)
        if not m:
            break
        if m.group("key") == "VERN":
            vern = _parse_vernacular(m.group("val"))
        content = content[: m.start()]

    rank = None
    m = _RANK_RE.search(content)
    if m:
        rank = m.group("rank").strip().lower()
        content = content[: m.start()]

    content = content.strip()

    if is_synonym:
        # No rank tag, and (confirmed against the whole file) no reliable
        # word count to split on -- see this module's docstring. The
        # synonym's own text is preserved whole rather than guessed into
        # name/authorship.
        return {
            "raw_name": content, "name": None, "authorship": None,
            "rank": None, "is_synonym": True, "vernacular": vern,
            "extinct": extinct,
        }

    words = content.split()
    if rank is None:
        rank = _infer_rank(words)
    elif rank == "unranked":
        # A clade the source deliberately leaves without a rank (53684's
        # "Cyclorrhapha [unranked]"), never a guess at what it would be.
        rank = None
    if rank is None:
        # That, an untagged uninomial, or a placeholder like "AVES INCERTAE
        # SEDIS": kept as a node so its children still hang somewhere, with
        # no name, so it is never offered as a species or matched as a
        # family.
        return {
            "raw_name": content, "name": None, "authorship": None,
            "rank": None, "is_synonym": False, "vernacular": vern,
            "extinct": extinct,
        }
    want = RANK_NAME_WORDS.get(rank)
    if want is None:
        raise KeyError(f"txtree: unrecognized rank {rank!r} in line {content!r}")
    name = " ".join(words[:want])
    authorship = " ".join(words[want:]) or None
    return {
        "raw_name": content, "name": name, "authorship": authorship,
        "rank": rank, "is_synonym": False, "vernacular": vern,
        "extinct": extinct,
    }


def parse_lines(lines):
    """Lines of .txtree text -> a flat list of taxon dicts with synthetic
    sequential ids and a parent id resolved from indentation depth.

    Split out from load() so the parsing logic itself -- the part worth
    testing against the real file's exact content -- doesn't require a
    zip on disk to exercise.
    """
    taxa = []
    # stack[d] is the id of the most recently emitted taxon at depth d,
    # i.e. the parent for anything that next appears at depth d+1.
    stack = {}
    next_id = 1
    for raw_line in lines:
        if not raw_line.strip():
            continue
        stripped = raw_line.lstrip(" ")
        indent = len(raw_line) - len(stripped)
        if indent % 2 != 0:
            raise ValueError(f"txtree: odd indentation ({indent}) on {raw_line!r}")
        depth = indent // 2

        row = _parse_line(stripped)
        row["id"] = str(next_id)
        next_id += 1
        row["parent"] = stack.get(depth - 1) if depth > 0 else None
        taxa.append(row)

        # A synonym line doesn't start a new lineage -- nothing nests
        # under it in this format (confirmed: no star line has a deeper
        # child in the real file) -- so it must not become the parent
        # stack[depth] entry a following *accepted* sibling or child would
        # otherwise inherit from.
        if not row["is_synonym"]:
            stack[depth] = row["id"]
    return taxa


def find_member(names):
    """The TextTree member of an archive's name list, or None. macOS's
    __MACOSX/._* resource forks share the extension and are skipped."""
    return next((n for n in names
                 if n.lower().endswith((".txtree", ".tree"))
                 and not n.startswith("__MACOSX")), None)


def load(path):
    """(taxa, names, meta), the same shape colChecklist.load() returns.

    `names` is always {} here -- there is no separate name registry in
    this format the way ColDP's Name.tsv is one, matching how
    colChecklist.py's own _coldp() returns {} for the same reason.
    """
    import colChecklist as CC
    c = CC._Container(path)
    try:
        member = find_member(c.namelist())
        if member is None:
            raise KeyError(f"no .txtree/.tree member in {path}")
        text = c.read(member).decode("utf-8", errors="replace")
    finally:
        c.close()

    return parse_lines(text.split("\n")), {}, CC.metadata(path)
