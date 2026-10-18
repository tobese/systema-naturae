#!/usr/bin/env python3
"""Reader for BioLib's .txtree format: an indentation tree with inline rank
tags and vernacular-name blocks.

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
import zipfile

# Leading-word count per rank, i.e. where the name ends and authorship
# begins on an ACCEPTED line. Only the ranks actually present in the one
# known real file are listed; an unrecognized rank raises rather than
# guessing a word count, so a second .txtree archive with a rank outside
# this set fails loudly instead of silently misreading every row at that
# rank the way the dispatch gaps fixed earlier tonight did.
RANK_NAME_WORDS = {
    "kingdom": 1, "phylum": 1, "class": 1, "order": 1, "superfamily": 1,
    "family": 1, "subfamily": 1, "tribe": 1, "subtribe": 1, "genus": 1,
    "subgenus": 1, "section": 1,
    "species": 2,
    "subspecies": 3, "variety": 3, "form": 3,
}

_VERN_RE = re.compile(r"\s*\{VERN=(?P<vern>.*)\}\s*$")
_RANK_RE = re.compile(r"\s*\[(?P<rank>[a-zA-Z ]+)\]\s*$")


def _parse_vernacular(raw):
    """"lang:name,lang:name" -> [{"language": ..., "name": ...}, ...]."""
    out = []
    for pair in raw.split(","):
        if ":" not in pair:
            continue
        lang, name = pair.split(":", 1)
        out.append({"language": lang.strip(), "name": name.strip()})
    return out


def _parse_line(content):
    """One stripped-of-indentation line -> a taxon dict, minus id/parent.

    `content` still carries a leading "*" for a synonym line; indentation
    (and therefore depth/parent) is the caller's job, not this function's,
    since a single line carries no idea of its own position in the tree.
    """
    is_synonym = content.startswith("*")
    if is_synonym:
        content = content[1:]

    vern = []
    m = _VERN_RE.search(content)
    if m:
        vern = _parse_vernacular(m.group("vern"))
        content = content[: m.start()]

    rank = None
    m = _RANK_RE.search(content)
    if m:
        rank = m.group("rank").strip()
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
        }

    want = RANK_NAME_WORDS.get(rank)
    if want is None:
        raise KeyError(f"txtree: unrecognized rank {rank!r} in line {content!r}")
    words = content.split()
    name = " ".join(words[:want])
    authorship = " ".join(words[want:]) or None
    return {
        "raw_name": content, "name": name, "authorship": authorship,
        "rank": rank, "is_synonym": False, "vernacular": vern,
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


def load(path):
    """(taxa, names, meta), the same shape colChecklist.load() returns.

    `names` is always {} here -- there is no separate name registry in
    this format the way ColDP's Name.tsv is one, matching how
    colChecklist.py's own _coldp() returns {} for the same reason.
    """
    with zipfile.ZipFile(path) as z:
        member = next((n for n in z.namelist() if n.lower().endswith(".txtree")), None)
        if member is None:
            raise KeyError(f"no .txtree member in {path}")
        text = z.read(member).decode("utf-8", errors="replace")

    import colChecklist as CC
    return parse_lines(text.split("\n")), {}, CC.metadata(path)
