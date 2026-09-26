#!/usr/bin/env python3
"""Backfill Wikipedia lead descriptions for domestic breed nodes.

Breeds are common-name based, so they don't fit the scientific-name-keyed
enrichment passes. This walks every BREED node in the family JSONs, resolves
each breed to its canonical en.wikipedia article, and stores the article's lead
paragraphs on the node as `description` (plus `wikipediaTitle` and
`sourcedFrom`) so the UI never has to guess a title from a name.

Resolution is per (host species, breed name) — "Rex" is a rabbit breed *and* a
guinea-pig breed, "African"/"Chinese" are goose breeds, so a name alone is not
a key. Each breed walks a candidate ladder, most reliable first, and the first
candidate whose lead actually reads like a breed *of the host species* wins:

  1. CURATED pin. Short names that collide with places, ships or unrelated
     topics have no derivable title ("Alpine" -> "Alpine, Texas").
  2. Wikidata QID. `shared/data/breed-images.json` already carries a resolved
     QID per breed (experiments/book-view/scripts/fetchBreedImages.mjs).
     QID -> EnWikiPagesQid.PageId -> EnWikiPages.Title is exact: "Pekin" ->
     "American Pekin", "Boer" -> "Boer goat", "Persian" -> "Persian cat".
  3. Name + host-species hint: "<Breed> <hint>", "<Breed> (<hint>)", "<Breed>".
  4. Section of a "List of <host> breeds" article, for breeds enwiki only
     documents inside a list (guinea pigs, many chickens and pigs).

The QID in breed-images.json is not trustworthy on its own - it was resolved to
find a portrait, so a wrong entity that happened to carry an image stuck. The
host-species check is what catches those ("Californian" -> Californian
(schooner), "Chinese" -> Chinese language, "Duroc" -> Duroc station).

The lead itself comes from the raw wikitext mirror, so the infobox and the
templates have to be rendered away before the prose is usable. That is what the
bulk of this file is.

Usage (from the repo root, with a tunnel to the wiki mirror on debbie):
    ssh -f -N -L 15433:127.0.0.1:5433 debbie
    python3 scripts/enrichBreedsFromWikipedia.py --resolve-only   # inspect titles
    python3 scripts/enrichBreedsFromWikipedia.py --apply          # write the data

Environment:
    WIKI_PG_DSN   libpq connection string for the mirror (see DEFAULT_DSN)
"""
import argparse
import json
import os
import re
import sys
import time
from glob import glob

DEFAULT_DSN = (
    "host=127.0.0.1 port=15433 dbname=snedtankt user=snedtankt "
    "password=hau8qpvFM6JYwvoDcztFT5NtfPBQ19"
)

# Host species -> the nouns its breed articles may legitimately use. Used both
# to build hinted title candidates and to validate the lead we get back. Several
# hosts have a second wording: the dog breeds lead with "scent hound", the
# Equus ones with "pony".
HOSTS = [
    ("Felis catus",                          ("cat",),         "List of cat breeds"),
    ("Canis lupus familiaris",               ("dog", "hound"), "List of dog breeds"),
    ("Equus ferus caballus",                 ("horse", "pony"), "List of horse breeds"),
    ("Capra hircus",                         ("goat",),       "List of goat breeds"),
    ("Ovis aries",                           ("sheep",),      "List of sheep breeds"),
    ("Sus scrofa domesticus",                ("pig",),        "List of pig breeds"),
    ("Bos taurus",                            ("cattle", "cow"), "List of cattle breeds"),
    ("Gallus gallus domesticus",             ("chicken", "hen"), "List of chicken breeds"),
    ("Meleagris gallopavo",                  ("turkey",),     "List of turkey breeds"),
    ("Anas platyrhynchos domesticus",        ("duck",),       "List of duck breeds"),
    ("Anser anser domesticus",               ("goose", "geese"), "List of goose breeds"),
    ("Columba livia domestica",              ("pigeon",),     "List of pigeon breeds"),
    ("Oryctolagus cuniculus",                ("rabbit", "hare"), "List of rabbit breeds"),
    ("Cavia porcellus",                      ("guinea pig", "cavy", "cavies"), "List of guinea pig breeds"),
]

# Breeds whose article cannot be derived from the breed name: the bare name
# resolves to a place, a ship, a language or a different subject, or the breed
# only exists as a section of a larger article. Keyed "<host breed>".
CURATED = {
    # sheep
    "sheep Lincoln":            "Lincoln sheep",
    "sheep Border Leicester":   "Border Leicester",
    "sheep Cheviot":           "Cheviot sheep",
    "sheep Dorset":             "Dorset Horn",
    "sheep Hampshire":         "Hampshire Down",
    # goats
    "goat Alpine":             "Alpine goat",
    "goat Pygmy":              "Pygmy goat",
    "goat Cashmere":           "Cashmere goat",
    "goat LaMancha":           "American Lamancha",
    "goat Nubian":             "Anglo-Nubian",
    "goat Oldenburg":          "Oldenburger",
    "goat Toggenburg":         "Toggenburger",
    "goat East Friesian":      "Fries Melkschaap",
    # pigs
    "pig Duroc":               "Duroc pig",
    "pig Tamworth":            "Tamworth pig",
    "pig Yorkshire":           "Yorkshire pig",
    "pig Berkshire":           "Berkshire pig",
    "pig Landrace":            "Danish Landrace pig",
    "pig Mangalitsa":          "Mangalica",
    "pig Hampshire":           "Hampshire pig",
    "pig Belgian Draft":       "American Belgian Draft",
    "pig Brahman":             "American Brahman",
    "pig Juliana":             ("List of pig breeds", "Juliana"),
    # cattle
    "cattle Angus":            "Aberdeen Angus",
    "cattle Ayrshire":         "Ayrshire cattle",
    "cattle Brown Swiss":      "Brown Swiss cattle",
    "cattle Charolais":        "Charolais cattle",
    "cattle Dexter":           "Dexter cattle",
    "cattle Galloway":         "Galloway cattle",
    "cattle Guernsey":         "Guernsey cattle",
    "cattle Hereford":         "Hereford cattle",
    "cattle Highland":         "Highland cattle",
    "cattle Holstein":         "Holstein Friesian",
    "cattle Jersey":           "Jersey cattle",
    "cattle Limousin":         "Limousin cattle",
    "cattle Milking Shorthorn": "Dairy Shorthorn",
    "cattle Piedmontese":      "Piedmontese cattle",
    "cattle Santa Gertrudis":  "Santa Gertrudis cattle",
    "cattle Simmental":        "Simmental cattle",
    "cattle Bresse":           "Bresse chicken",   # actually a chicken, see below
    # chickens
    "chicken Sussex":          "Sussex chicken",
    "chicken Bresse":          "Bresse chicken",
    "chicken Cochin":          "Cochin chicken",
    "chicken Dominique":       "Dominique chicken",
    "chicken Frizzle":         "Frizzle (chicken breed)",
    "chicken Orpington":       "Orpington chicken",
    "chicken Plymouth Rock":   "Plymouth Rock chicken",
    "chicken Polish":          "Polish chicken",
    "chicken Sebright":        "Sebright chicken",
    "chicken White Leghorn":   "Leghorn chicken",
    "chicken Wyandotte":       "Wyandotte chicken",
    "chicken Indian Runner":   "Indian Runner duck",  # duck, see below
    "chicken Cornish Cross":   ("List of chicken breeds", "Cornish Cross"),
    # turkeys
    "turkey Broad Breasted Bronze": "Bronze turkey",
    "turkey Narragansett":     "Narragansett turkey",
    "turkey Royal Palm":       "Royal Palm turkey",
    # ducks
    "duck Pekin":              "American Pekin",
    "duck Call":               "Call duck",
    "duck Cayuga":             "Cayuga duck",
    "duck Indian Runner":      "Indian Runner duck",
    "duck Magpie":             "Magpie duck",
    "duck Muscovy":            "Muscovy duck",
    "duck Rouen":              "Rouen (duck)",
    # geese. "Emden" alone is the German city; the goose is "Emden (goose)".
    "goose Embden":            "Emden (goose)",
    "goose African":           "African goose",
    "goose Chinese":           "Chinese goose",
    "goose Sebastopol":        "Sebastopol goose",
    "goose Pilgrim":           "Pilgrim goose",
    "goose Toulouse":          "Toulouse (goose)",
    # pigeons
    "pigeon Mondain":          "French Mondain",
    "pigeon Fantail":          "Fantail pigeon",
    "pigeon Jacobin":          "Jacobin pigeon",
    "pigeon King":             "King pigeon",
    "pigeon Tumbler":          "Tumbler pigeons",
    "pigeon Pouter":           ("List of pigeon breeds", "Pouter"),
    # rabbits
    "rabbit Californian":      "Californian rabbit",
    "rabbit Rex":              "Rex rabbit",
    "rabbit Netherland Dwarf": "Netherland Dwarf rabbit",
    "rabbit Flemish Giant":    "Flemish Giant rabbit",
    "rabbit Lionhead":         "Lionhead rabbit",
    "rabbit English Angora":   "Angora rabbit",
    "rabbit New Zealand White": "New Zealand White rabbit",
    "rabbit American Chinchilla": ("List of rabbit breeds", "American Chinchilla"),
    "rabbit Chinchilla":       ("List of rabbit breeds", "Chinchilla"),
    # guinea pigs
    "guinea pig Peruvian":     "Peruvian guinea pig",
    "guinea pig Rex":          ("List of guinea pig breeds", "Rex"),
    "guinea pig Teddy":        "Teddy guinea pig",
    "guinea pig Himalayan":    "Himalayan guinea pig",
    "guinea pig Abyssinian":   "Abyssinian guinea pig",
    "guinea pig Silkie":       ("List of guinea pig breeds", "Silkie"),
    "guinea pig American":     "American guinea pig",
    "guinea pig English":      ("List of guinea pig breeds", "English"),
    "guinea pig Coronet":     ("List of guinea pig breeds", "Coronet"),
    "guinea pig Texan":        ("List of guinea pig breeds", "Texan"),
    "guinea pig Smooth Coat":  ("List of guinea pig breeds", "Smooth Coat"),
    "guinea pig White Crested": ("List of guinea pig breeds", "White Crested"),
    "guinea pig American Crested": ("List of guinea pig breeds", "American Crested"),
    # horses
    "horse Andalusian":        "Andalusian horse",
    "horse Arabian":           "Arabian horse",
    "horse Clydesdale":        "Clydesdale horse",
    "horse Friesian":          "Friesian horse",
    "horse Hanoverian":        "Hanoverian horse",
    "horse Icelandic":         "Icelandic horse",
    "horse KWPN":              "Dutch Warmblood",
    "horse Lipizzaner":        "Lipizzan",
    "horse Missouri Fox Trotter": "Missouri Fox Trotter",
    "horse New Forest Pony":   "New Forest pony",
    "horse Oldenburg":         "Oldenburger",
    "horse Quarter Horse":     "American Quarter Horse",
    "horse Shetland Pony":     "Shetland pony",
    "horse Shire":             "Shire horse",
    "horse Swedish Warmblood": "Swedish Warmblood",
    "horse Tennessee Walking": "Tennessee Walking Horse",
    "horse Trakehner":         "Trakehner",
    "horse Welsh Pony":        "Welsh Pony and Cob",
    "horse Welsh Harlequin":   "Welsh Harlequin",
    "horse American Cream Draft": "American Cream Draft",
    # dogs
    "dog Boxer":                "Boxer (dog breed)",
    "dog Chihuahua":            "Chihuahua (dog breed)",
    "dog Doberman Pinscher":    "Dobermann",
    "dog Pointer":              "Pointer (dog breed)",
    "dog Pomeranian":           "Pomeranian dog",
    "dog Dalmatian":            "Dalmatian dog",
    "dog Collie":               "Collie",
    "dog Old English Sheepdog": "Old English Sheepdog",
    "dog German Shepherd":      "German Shepherd",
    # cats
    "cat Bambino":              ("List of experimental cat breeds", "Bambino"),
    "cat Savannah":             "Savannah cat",
    "cat Bengal":               "Bengal cat",
    "cat Balinese":             "Balinese cat",
    "cat Burmese":              "Burmese cat",
    "cat Persian":              "Persian cat",
    "cat Siamese":              "Siamese cat",
    "cat Somali":               "Somali cat",
    "cat Sphynx":               "Sphynx cat",
    "cat Tonkinese":            "Tonkinese cat",
    "cat Donskoy":              "Donskoy cat",
    "cat Siberian":             "Siberian cat",
    "cat Abyssinian":           "Abyssinian cat",
    "cat Norwegian Forest Cat": "Norwegian Forest Cat",
}

LEAD = 2                                    # lead paragraphs to keep

# ---------------------------------------------------------------- wikitext ---

# Templates whose first (or second) argument is what a reader actually sees.
# Everything else collapses to a space, which is why {{lang|my|...}} would
# otherwise leave a dangling "}}" behind.
DISPLAY_ARG0 = {"nihongo", "nowrap", "nobr", "nsp", "transliteration", "respell",
                "ipa", "audio", "wikispecies", "wiktionary", "wikiquote", "sic",
                "h:title", "vern"}
DISPLAY_ARG1 = {"lang", "llang"}          # {{lang|code|text}}


def find_block_end(text, start):
    """text[start:start+2] is '{{' or '{|'; index just past the match, or -1."""
    depth, j, n = 0, start, len(text)
    while j < n - 1:
        two = text[j:j + 2]
        if two in ("{{", "{|"):
            depth += 1
            j += 2
            continue
        if two in ("}}", "|}"):
            depth -= 1
            j += 2
            if depth == 0:
                return j
            continue
        j += 1
    return -1


def split_args(body):
    """Split a template body on top-level '|', ignoring nested braces."""
    parts, buf, depth, i, n = [], [], 0, 0, len(body)
    while i < n:
        if body[i:i + 2] in ("{{", "{|"):
            depth += 1
            buf.append(body[i:i + 2])
            i += 2
            continue
        if body[i:i + 2] in ("}}", "|}"):
            depth -= 1
            buf.append(body[i:i + 2])
            i += 2
            continue
        if body[i] == "|" and depth == 0:
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(body[i])
        i += 1
    parts.append("".join(buf))
    return parts


def render_templates(text):
    """Replace every {{...}} block: known display templates contribute their
    visible argument, the rest collapse to a space. Repeat until stable so
    nested templates resolve too."""
    for _ in range(8):
        out, i, n, changed = [], 0, len(text), False
        while i < n:
            if text[i:i + 2] == "{{":
                end = find_block_end(text, i)
                if end == -1:
                    out.append(text[i:])
                    break
                changed = True
                args = split_args(text[i + 2:end - 2])
                name = args[0].strip().lower()
                disp = ""
                if name in DISPLAY_ARG0 and len(args) > 1:
                    disp = args[1]
                elif name in DISPLAY_ARG1 and len(args) > 2:
                    disp = args[2]
                elif name.startswith("lang-") and len(args) > 1:
                    disp = args[1]
                out.append(render_templates(disp) if disp else " ")
                i = end
                continue
            out.append(text[i])
            i += 1
        text = "".join(out)
        if not changed:
            break
    return text


def strip_wikilinks(s):
    """Resolve [[...]] links, honouring nesting.

    A plain regex cannot do this: a captioned image is
    ``[[File:X.jpg|thumb|A flock in [[Sernur]] ]]`` and the caption's own link
    closes the ``]]`` early, so a ``[^\\]]*`` matcher leaves the tail of the
    caption behind as debris. File/Image/Category/Media targets are dropped,
    everything else collapses to its display text.
    """
    out, i, n = [], 0, len(s)
    while i < n:
        if s.startswith("[[", i):
            depth, j, closed = 0, i, False
            while j < n - 1:
                if s.startswith("[[", j):
                    depth += 1
                    j += 2
                    continue
                if s.startswith("]]", j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        closed = True
                        break
                    continue
                j += 1
            if not closed:                        # unbalanced: keep the remainder
                out.append(s[i:])
                break
            body = s[i + 2:j - 2]
            target = body.split("|", 1)[0].strip()
            if re.match(r"(?i)^(file|image|media|category)\s*:", target):
                pass                            # drop the whole link
            else:
                out.append(body.split("|")[-1].strip() if "|" in body else target)
            i = j
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


def clean_markup(s):
    """Wikitext -> plain prose, with the debris removed templates leave behind."""
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<ref[^>]*?/>", "", s)
    s = re.sub(r"<ref[^>]*?>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = render_templates(s)
    s = re.sub(r"'{2,5}", "", s)
    s = strip_wikilinks(s)
    s = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", s)
    s = re.sub(r"\[https?://\S+\]", "", s)
    for a, b in (("&nbsp;", " "), ("&ndash;", "-"), ("&mdash;", "-"), ("&amp;", "&"),
                 ("&quot;", '"'), ("&deg;", " degrees"), ("&minus;", "-"),
                 ("&times;", "x")):
        s = s.replace(a, b)
    s = re.split(r"\n?\s*==[^=]", s)[0]
    # Parentheticals that were only there to carry a non-Latin or templated gloss.
    s = re.sub(r"\([^()]*[^\x00-\x7f][^()]*\)", "", s)
    s = re.sub(r"\(\s*(?:,\s*)+[^()]*\)", "", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\(\s*[a-z]{2}\s*\)", "", s)
    s = re.sub(r"\[\s*\]", "", s)
    s = re.sub(r";\s*\(", " (", s)
    s = re.sub(r"([.,])\s*,\s*(though|although|but|and|while|which)\b", r"\1 \2", s)
    s = re.sub(r"\s(?:at|from|in|of|to|by|with|weighing|measuring|reaching)\s*([.,])", r"\1", s)
    s = re.sub(r"([.!?])\s+([a-z])", lambda m: m.group(1) + " " + m.group(2).upper(), s)
    s = re.sub(r"\s+([,;:.])", r"\1", s)
    s = re.sub(r"[,;:]{2,}", ",", s)
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"\s+\)", ")", s)
    s = re.sub(r"\s+", " ", s)
    # Leftover table/template scaffolding. A "|" or "}" surviving template
    # rendering is always debris, never prose.
    for ch in ("{", "}", "|", "[[", "]]"):
        s = s.replace(ch, " ")
    s = re.sub(r"\s+", " ", s)
    # Trim template debris from the edges but keep a real closing full stop.
    s = s.strip(" \t\n{}|;:-")
    return s.lstrip(".,;:").rstrip(",;:").strip()


def lead_paragraphs(text, section=None, max_paras=LEAD):
    """First `max_paras` prose paragraphs, skipping the infobox and headings.

    A paragraph that does not start like a sentence is a fragment left behind by
    a table or an unbalanced template, not prose, so it is skipped rather than
    shown to the reader.
    """
    if section:
        m = re.search(r"^=+\s*" + re.escape(section) + r"\s*=+\s*$", text, flags=re.M)
        if not m:
            return []
        text = text[m.end():]
        nxt = re.search(r"^=+[^=\n]", text, flags=re.M)
        if nxt:
            text = text[:nxt.start()]
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = render_templates(text)
    paras = []
    for chunk in re.split(r"\n\s*\n", text):
        c = chunk.strip()
        if not c or c.startswith("="):
            if c.startswith("=") and paras:
                break
            continue
        if c.startswith(("*", ":", "#", "|", "!", "{")) or c.startswith("__"):
            continue
        c = clean_markup(c)
        if len(c) < 40:
            continue
        if not (c[0].isupper() or c[0].isdigit() or c[0] in "\"'“‘("):
            continue
        if re.match(r"(?i)^(file|image|media)\s*:", c):
            continue
        paras.append(c)
        if len(paras) >= max_paras:
            break
    return paras


def looks_like_breed(paragraphs, host_nouns, from_list=False):
    """Reject an article that is about something other than a breed of the host
    species. Strict on purpose: requiring a host noun is what stops "Silkie"
    (a guinea pig) being described by the Silkie chicken, and "Racing Homer" by
    the sport of pigeon racing.

    A section lifted out of a "List of <host> breeds" article is trusted by
    construction - it is a breed of that host by definition, and its text is
    often a comparison ("resembles the Silkie...") that never names the host. A
    breed whose own article genuinely never names the host needs an explicit
    CURATED pin rather than a looser rule here.
    """
    text = " ".join(paragraphs).lower()
    if not text:
        return False
    if from_list:
        return True
    return any(n in text for n in host_nouns)


# ------------------------------------------------------------------ titles ---

def host_of(species):
    """(accepted nouns, "List of ... breeds" article) for a species name."""
    for sci, nouns, lst in HOSTS:
        if species and species.startswith(sci.split()[0]):
            return nouns, lst
    return (), None


def host_key(species):
    """The single word used to key the CURATED table for this host."""
    nouns, _ = host_of(species)
    return nouns[0] if nouns else None


def candidate_titles(name, host_noun, qid_title):
    """Ordered (title, section|None) candidates for one (species, breed)."""
    out = []
    pin = CURATED.get(f"{host_noun} {name}") if host_noun else None
    if pin:
        out.append(pin if isinstance(pin, tuple) else (pin, None))
    if qid_title:
        out.append((qid_title, None))
    base = re.sub(r"\s*\(.*\)\s*$", "", name).strip()
    if host_noun:
        out += [(f"{base} {host_noun}", None), (f"{base} ({host_noun})", None)]
    out.append((base, None))
    for generic in ("cat", "dog", "horse", "breed"):
        out.append((f"{base} ({generic})", None))
    seen, uniq = set(), []
    for t, s in out:
        k = (t.lower(), s)
        if k not in seen:
            seen.add(k)
            uniq.append((t, s))
    return uniq


# ---------------------------------------------------------------- inventory ---

def collect_breeds(root):
    """{family_dir: (path, [(breed_name, species, node_id, has_description)])}"""
    out = {}
    for p in sorted(glob(os.path.join(root, "*", "*", "*", "src", "data", "*.json"))):
        try:
            tree = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        fam = p.split(os.sep)[-4]
        rows = []

        def walk(node, species):
            if node.get("rank") in ("SPECIES", "SUBSPECIES") and node.get("name"):
                species = node["name"]
            if node.get("rank") == "BREED":
                rows.append((node["name"], species, node.get("id"),
                             bool(node.get("description"))))
            for c in node.get("children") or []:
                walk(c, species)

        walk(tree, None)
        if rows:
            out[fam] = (p, rows)
    return out


# --------------------------------------------------------------------- db ----

def connect(dsn):
    try:
        import psycopg2
    except ImportError:
        sys.exit("psycopg2 is required (pip install psycopg2-binary)")
    return psycopg2.connect(dsn)


def fetch_pages(cur, titles):
    """title(lower) -> {title, text}, following redirect chains. A self-redirect
    (enwiki anchors its own list pages) counts as a page, not a redirect."""
    raw = {}
    frontier, seen = sorted({t.lower() for t in titles}), set()
    while frontier:
        keys = [k for k in frontier if k not in seen]
        seen |= set(keys)
        if not keys:
            break
        for i in range(0, len(keys), 300):
            cur.execute(
                'SELECT DISTINCT ON (lower("Title")) "Title", "IsRedirect", '
                '"RedirectTarget", "Wikitext" FROM "EnWikiPages" '
                'WHERE lower("Title") = ANY(%s) '
                'ORDER BY lower("Title"), "IsRedirect" ASC',
                (keys[i:i + 300],))
            for title, isr, target, text in cur.fetchall():
                rec = raw.setdefault(title.lower(), {})
                rec.setdefault("title", title)
                if isr and target and target.lower() != title.lower():
                    rec["redirect"] = target
                elif text is not None:
                    rec["text"] = text
        frontier = [raw[k]["redirect"].lower() for k in keys
                    if "redirect" in raw.get(k, {})]

    def resolve(key, depth=0):
        if key not in raw or depth > 5:
            return None
        rec = raw[key]
        if "text" in rec:
            return rec
        if "redirect" in rec:
            return resolve(rec["redirect"].lower(), depth + 1)
        return None

    out = {}
    for key in seen:
        final = resolve(key)
        if final:
            out[key] = {"title": final["title"], "text": final["text"]}
    return out


def qid_titles(cur, qids):
    """QID -> enwiki title, via the PageId both tables share."""
    out = {}
    for i in range(0, len(qids), 300):
        cur.execute(
            'SELECT q."Qid", p."Title" FROM "EnWikiPagesQid" q '
            'JOIN "EnWikiPages" p USING ("PageId") WHERE q."Qid" = ANY(%s)',
            (qids[i:i + 300],))
        for q, t in cur.fetchall():
            out[q] = t
    return out


# -------------------------------------------------------------------- main ---

# ------------------------------------------------------------- portraits ----
# shared/data/breed-images.json is the book's ONLY portrait source for breeds
# (the graph instead fetches live from the REST API). It was originally built by
# experiments/book-view/scripts/fetchBreedImages.mjs, which resolves breeds by
# NAME through Wikidata search - fine for a sidecar, but it lands on the wrong
# entity whenever a breed name is also a place or a person, and a wrong entity
# that happens to carry an image sticks. "Alpine" (a goat) resolved to Q661540,
# the city of Alpine, Texas, and took a photograph of the town with it.
#
# Here the article comes from the validated resolution above instead, so the
# portrait is whatever that breed's own article leads with.

# A breed with no article of its own redirects into one of these, so the title
# after redirect-following is what identifies the case. A pinned section alone
# is not enough: "American guinea pig" and "Teddy guinea pig" both land on
# "List of guinea pig breeds" without ever being written as a section.
LIST_PAGE = re.compile(r"^List of .+ breeds$", re.I)

UA = ("SystemaNaturaeDev/1.0 (https://github.com/tobese/systema-naturae; "
      "breed-portrait backfill)")

COMMONS_HOSTS = ("upload.wikimedia.org", "thumb.wikimedia.org",
                 "commons.wikimedia.org", "en.wikipedia.org")


def commons_filename(url):
    """Reduce a Wikimedia image URL to the bare Commons filename the book wants.

    The sidecar convention is a bare filename: extractSlice's toThumb() wraps it
    in Special:FilePath?width=N, and SpeciesEntry's withWidth() rewrites that
    width to 400 for the hover preview and 1600 for the lightbox. An absolute
    upload.wikimedia.org URL bypasses both - it serves one fixed size, and the
    ?utm_source=... tracking query the REST API appends is not a width= param,
    so withWidth cannot upgrade it.
    """
    if not url or not url.startswith("http"):
        return url
    if not any(h in url for h in COMMONS_HOSTS):
        return url
    from urllib.parse import unquote
    path = url.split("?", 1)[0]
    name = path.rsplit("/", 1)[-1]
    if "/thumb/" in path:                    # .../thumb/a/ab/X.jpg/380px-X.jpg
        if re.match(r"^\d+px-", name):
            name = name.split("-", 1)[1]
    return unquote(name)


def qid_for_title(cur, title):
    cur.execute(
        'SELECT "Qid" FROM "EnWikiPagesQid" q JOIN "EnWikiPages" p USING ("PageId") '
        'WHERE lower(p."Title") = lower(%s)', (title,))
    row = cur.fetchone()
    return row[0] if row else None


def wikidata_p18(qid):
    """P18 (depicted image) for a Wikidata item, as a bare Commons filename.

    The REST summary only carries the article's *lead* image and plenty of breed
    articles have none - "Alpine goat" is one. P18 is the item's canonical
    picture regardless of where the article places it.
    """
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
            headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            ent = json.loads(r.read())["entities"][qid]
    except Exception:
        return None
    for claim in ent.get("claims", {}).get("P18", []):
        value = (claim.get("mainsnak") or {}).get("datavalue") or {}
        if isinstance(value.get("value"), str) and value["value"]:
            return value["value"]
    return None


def wiki_summary(title):
    import urllib.parse
    import urllib.request
    url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
           + urllib.parse.quote(title.replace(" ", "_")))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception:
        return None


def write_portraits(args, meta, pages, cur):
    start = time.time()
    path = os.path.join(args.root, "shared/data/breed-images.json")
    current = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}

    # (species, name) -> (validated article title, is-a-list-page)
    resolved = {}
    for key, info in meta.items():
        species, name = key
        host_noun = host_key(species)
        for title, section in candidate_titles(name, host_noun, None):
            rec = pages.get(title.lower())
            if not rec or "text" not in rec:
                continue
            paras = lead_paragraphs(rec["text"], section)
            if not paras:
                continue
            from_list = bool(section) or bool(LIST_PAGE.match(rec["title"]))
            if not looks_like_breed(paras, host_of(species)[0], from_list=from_list):
                continue
            resolved[key] = (rec["title"], from_list)
            break

    redo = {n.strip() for n in (args.redo_portraits or "").split(",") if n.strip()}
    todo, list_only = [], []
    for key, (title, from_list) in sorted(resolved.items()):
        name = key[1]
        have = (current.get(name) or {}).get("image")
        if from_list:
            # The breed has no article of its own; its prose - and any lead
            # image - lives inside a "List of <host> breeds" page, and that
            # image belongs to some *other* breed on the list. Attaching it
            # would put a photo of the wrong animal on the row.
            list_only.append(name)
            continue
        if args.force or name in redo or not have:
            todo.append((key, title))
    print(f"portraits: {len(resolved)} breeds resolved to an article; "
          f"{len(todo)} to fetch, {len(list_only)} documented only inside a list "
          f"page (no portrait attached)")

    out = dict(current)
    added = changed = dropped = normalised = 0
    for name, entry in out.items():
        raw = entry.get("image")
        if raw and raw.startswith("http"):
            fn = commons_filename(raw)
            if fn != raw:
                out[name] = {**entry, "image": fn}
                normalised += 1
    # Six breed display names are shared by two host species ("Rex" is a rabbit
    # and a cavy, "Silkie" a chicken and a cavy, "Abyssinian" a cat and a cavy,
    # "Hampshire"/"Hereford" sheep-or-pig vs cattle-or-pig, "Texel" sheep and
    # cavy) and this sidecar is keyed by name alone, so one of each pair writes
    # over the other. A list-only breed must therefore never drop a portrait
    # that a *different* species legitimately resolved - that is how the cavy
    # Rex ended up deleting the rabbit Rex's photo.
    name_keyed = {name for (_sp, name), (_t, from_list) in resolved.items() if not from_list}
    for name in list_only:
        if name in name_keyed:
            print(f"    keeping {name!r}: also a non-list breed of another species, "
                  f"one name key cannot hold both")
            continue
        if (out.get(name) or {}).get("image"):
            out[name] = {k: v for k, v in out[name].items() if k != "image"}
            dropped += 1

    for i, (key, title) in enumerate(todo, 1):
        name = key[1]
        j = wiki_summary(title)
        img = commons_filename(((j or {}).get("originalimage") or {}).get("source")
                               or ((j or {}).get("thumbnail") or {}).get("source"))
        # The mirror's own QID for this article wins over the one the REST
        # summary reports: for "Alpine goat" the summary answers Q141438738,
        # which carries no P18, while the mirror's Q2840092 is the goat breed
        # and has the picture.
        qid = qid_for_title(cur, title) or (j or {}).get("wikibase_item")
        if not img:
            # No lead image on the article: fall back to the Wikidata item's P18
            # before concluding there is no portrait at all.
            img = commons_filename(wikidata_p18(qid)) if qid else None
            if img:
                print(f"    {name}: no lead image, took P18 {img}")
        if img:
            was = (current.get(name) or {}).get("image")
            out[name] = {k: v for k, v in {"qid": qid, "image": img}.items() if v}
            if not was:
                added += 1
            elif was != img:
                changed += 1
        elif (args.force or name in redo) and (out.get(name) or {}).get("image"):
            # Re-fetched, and the validated article has no lead image and no
            # P18, so whatever is stored cannot be verified against it. Drop it
            # rather than keep an unverifiable picture.
            out[name] = {k: v for k, v in out[name].items() if k != "image"}
            dropped += 1
            print(f"    dropped unverifiable portrait for {name!r}")
        if i % 15 == 0 or i == len(todo):
            el = time.time() - start
            print(f"  {i}/{len(todo)} {100*i/len(todo):.0f}% elapsed {el:.0f}s "
                  f"eta {(el/i)*(len(todo)-i):.0f}s")
        time.sleep(0.25)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(sorted(out.items())), indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {path}: +{added} new, {changed} changed, {dropped} misleading or "
          f"unverifiable portrait(s) dropped, {normalised} URL(s) normalised to a "
          f"bare Commons filename")


def main():
    ap = argparse.ArgumentParser()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--root", default=root)
    ap.add_argument("--dsn", default=os.environ.get("WIKI_PG_DSN", DEFAULT_DSN))
    ap.add_argument("--resolve-only", action="store_true",
                    help="print resolved titles + leads and exit, writing nothing")
    ap.add_argument("--apply", action="store_true",
                    help="write description/wikipediaTitle/sourcedFrom into the family JSONs")
    ap.add_argument("--force", action="store_true",
                    help="re-extract breeds that already have a description")
    ap.add_argument("--out", default="/tmp/breed-leads.json")
    ap.add_argument("--portraits", action="store_true",
                    help="fill shared/data/breed-images.json from the validated "
                         "article titles (the book's only portrait source for breeds)")
    ap.add_argument("--redo-portraits", default="",
                    help="comma-separated breed names to re-fetch even when they "
                         "already have a portrait (for ones known to be wrong)")
    args = ap.parse_args()

    inv = collect_breeds(args.root)
    images = json.load(open(os.path.join(args.root, "shared/data/breed-images.json"),
                           encoding="utf-8"))
    total = sum(len(r[1]) for r in inv.values())
    todo = sum(1 for r in inv.values() for x in r[1] if not x[3])
    print(f"{len(inv)} families, {total} breed nodes, {todo} without a description")

    # one row per (species, breed): "Rex" is both a rabbit and a guinea pig
    keys, meta = [], {}
    for _fam, (_path, rows) in inv.items():
        for name, species, _id, described in rows:
            k = (species, name)
            if k not in meta:
                keys.append(k)
            meta[k] = {"name": name, "species": species, "described": described}

    conn = connect(args.dsn)
    cur = conn.cursor()
    qids = sorted({(images.get(k[1]) or {}).get("qid") for k in keys} - {None})
    print(f"resolving {len(keys)} (species, breed) pairs; {len(qids)} Wikidata QIDs")
    qt = qid_titles(cur, qids)

    # every title any candidate might need, in one round trip
    want = set()
    for species, name in keys:
        for t, _s in candidate_titles(name, host_key(species),
                                     qt.get((images.get(name) or {}).get("qid"))):
            want.add(t)
        _h, lst = host_of(species)
        if lst:
            want.add(lst)
    print(f"fetching {len(want)} candidate articles ...")
    pages = fetch_pages(cur, want)

    result, unresolved = {}, []
    for species, name in keys:
        info = meta[(species, name)]
        if info["described"] and not args.force:
            continue
        host_nouns, lst = host_of(species)
        host_noun = host_key(species)
        qid = (images.get(name) or {}).get("qid")
        cands = candidate_titles(name, host_noun, qt.get(qid) if qid else None)
        if lst:
            cands.append((lst, name))
        pick = None
        pin = CURATED.get(f"{host_noun} {name}")
        for title, section in cands:
            rec = pages.get(title.lower())
            if not rec or "text" not in rec:
                continue
            paras = lead_paragraphs(rec["text"], section)
            if not paras:
                continue
            # a named section of a "List of <host> breeds" article is trusted:
            # it is a breed of that host by construction
            if not looks_like_breed(paras, host_nouns, from_list=bool(section)):
                continue
            via = "curated" if pin and (title, section) == (
                pin if isinstance(pin, tuple) else (pin, None)) else "ladder"
            pick = {"title": rec["title"], "paragraphs": paras, "via": via}
            break
        if pick:
            result[f"{species}||{name}"] = pick
        else:
            unresolved.append((species, name))

    print(f"resolved {len(result)}; unresolved {len(unresolved)}")
    for s, n in unresolved:
        print(f"  UNRESOLVED {n} (under {s})")

    if args.portraits:
        write_portraits(args, meta, pages, cur)
        return

    if args.resolve_only:
        for k, v in sorted(result.items()):
            species, name = k.split("||")
            print(f"  {name:28s} {v['title']:34s} {v['via']:8s} | {v['paragraphs'][0][:90]}")
        return

    json.dump(result, open(args.out, "w"), indent=1)
    if not args.apply:
        print(f"(dry run - leads in {args.out}; pass --apply to write the family JSONs)")
        return

    written = 0
    for fam, (path, rows) in inv.items():
        tree = json.load(open(path, encoding="utf-8"))
        hits = [0]

        def stamp(node, species):
            if node.get("rank") in ("SPECIES", "SUBSPECIES") and node.get("name"):
                species = node["name"]
            if node.get("rank") == "BREED":
                rec = result.get(f"{species}||{node.get('name')}")
                if rec and (args.force or not node.get("description")):
                    node["description"] = "\n".join(rec["paragraphs"])
                    node["wikipediaTitle"] = rec["title"]
                    node["sourcedFrom"] = "wikipedia"
                    hits[0] += 1
            for c in node.get("children") or []:
                stamp(c, species)

        stamp(tree, None)
        if hits[0]:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(tree, indent=2, ensure_ascii=False) + "\n")
            written += hits[0]
            print(f"  {fam}: described {hits[0]} breeds")

    print(f"done - {written} breed descriptions written")


if __name__ == "__main__":
    main()
