# ICZN Official Lists and Indexes -- validation report

Source: ICZN-lists (GBIF clone of the Commission's lists), CC0 1.0 waived.
Parsed from `names.txt`, which has no header; the column order is the one
in the archive README's `\copy names (...)` statement.

- ICZN names: 12,403 (8,158 available, 4,043 unavailable, 202 blank status)
- tree species checked: 1,755,597 in animalia
- matched: 1,159 (0.07%)
- of which available: 983
- of which **unavailable**: 157
- of which blank status: 19

## Why this is not an import

The Commission's lists are a judgement about availability, not a record of
which species exist. 0.1% coverage means this fills no gap and is not a
candidate for an import pass; what it does is catch names we hold that the
Commission has ruled on, which no amount of name or id matching had found.
The `opinions` column carries the ruling -- a plenary power, a Direction, a
homonymy decision -- and that reasoning is the only place it lives. It is
not encoded as a data field: a species is not "ICZN-valid" in the way it is
"in Asia", and recording that as a boolean would be a claim about a name we
may not even be using in the same sense.

## The 157 unavailable names we hold

Across 72 families. Most are junior homonyms or names suppressed by plenary
power, and in most cases the species is also present under a different,
available name -- so this is a spelling/usage question rather than a missing
taxon. A sample:

- `agamidae` **Draco ocellatus** -- {651}
- `agamidae` **Hydrosaurus ocellarius** -- {1948}
- `agamidae` **Stellio graecus** -- {651}
- `agamidae` **Stellio italicus** -- {651}
- `agamidae` **Stellio salvaquardia** -- {540}
- `agamidae` **Tropidolepis aculeatus** -- {1909}
- `agamidae` **Tropidolepis bellii** -- {1909}
- `agamidae` **Tropidolepis fasciatus** -- {1909}
- `amphisbaenidae` **Amphisbaena dubia** -- {664}
- `amphisbaenidae` **Amphisbaena flavescens** -- {380}
- `amphisbaenidae` **Amphisbaena marmorata** -- {380}
- `aphididae` **Tychea graminis** -- {1654}
- `apidae` **Melissodes fonscolombei** -- {750}
- `bostrichidae` **Lyctus brunneus** -- {1771}
- `bovidae` **Antilope zebrata** -- {1291}
- `bovidae` **Rhynotragus semiticus** -- {2029}
- `bufonidae` **Bufo cruciger** -- {651}
- `canidae` **Canis antarticus** -- {451}
- `canidae` **Vulpes minimus** -- {1129}
- `carabidae` **Carabus auropunctatus** -- {380}
- `carabidae` **Carabus caerulescens** -- {380}
- `carabidae` **Carabus rufipes** -- {380}
- `carabidae` **Carabus trigonus** -- {380}
- `carabidae` **Cicindela aurichalcea** -- {380}
- `carabidae` **Cicindela crucifera** -- {380}

Full list: `scripts/validateIczn.py`
