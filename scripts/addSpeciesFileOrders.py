#!/usr/bin/env python3
"""Add a Species File order and its families to portal/data/taxonomy.json.

The importer writes family data; this writes the part the portal needs to find it
-- an ORDER node and FAMILY children carrying `appSlug` and `speciesCount`,
which is what buildData.ts resolves a family through.

Reads the fragments the importer emits (/tmp/<slug>_families.json), so the two
cannot disagree about names or counts. Idempotent: re-running updates the
speciesCount of families already present and inserts only the ones that are
missing, so it is safe to run after a re-import.

Id collisions are a hard error. FAMILY ids are `FAM_<NAME>`, so two different
orders claiming the same family name would produce one id and one of them would
silently never resolve -- the failure mode the data-contract test exists to
catch, better caught here where the cause is obvious.

Usage:
    python3 scripts/addSpeciesFileOrders.py --dry-run
    python3 scripts/addSpeciesFileOrders.py --apply
"""
import argparse
import json
import os
import sys

TAXONOMY = "portal/data/taxonomy.json"

# slug -> order metadata. Written out rather than derived, because `commonName`
# and `description` are editorial: the sources have no order-level prose, and
# inventing it from the family list would produce confident filler.
ORDERS = {
    "phasmida": {
        "name": "Phasmida", "commonName": "Stick insects and leaf insects",
        "description": "Phasmids, or stick insects, are among the most camouflaged "
                       "insects: their bodies and legs mimic twigs, bark and leaves so "
                       "closely that a resting individual is difficult to distinguish from "
                       "its background. Many feed on foliage at night, hold their bodies "
                       "rigidly, and are most active after dusk. Their camouflage is "
                       "paired with an unusually prolonged life cycle -- several species "
                       "take a year or more to mature, and some large species live for "
                       "several years, which is exceptional among insects. They are "
                       "restricted to warm regions and are absent from the polar and "
                       "desert extremes; several species are pests of forestry and "
                       "horticulture, while many island forms are narrow endemics.",
    },
    "plecoptera": {
        "name": "Plecoptera", "commonName": "Stoneflies",
        "description": "Stoneflies are weak-flying aquatic insects whose nymphs live "
                       "in well-oxygenated streams, making them reliable indicators of "
                       "water quality; nymphs graze on algae and decaying plant matter "
                       "and often spend months underwater. The adults live only a few "
                       "days to a fortnight, usually near the water they emerged from, "
                       "which is why they are so rarely noticed despite their ancient "
                       "lineage. They have two tails and a long prothorax, and their "
                       "nymphs often have two claws on each leg, which permits them to "
                       "cling beneath stones in fast water. One widespread species, "
                       "Perla marginata, is familiar to anglers as a fish food, and the "
                       "order's protoneurial nymphs are among the closest living "
                       "relatives of the winged insects.",
    },
    "mantodea": {
        "name": "Mantodea", "commonName": "Mantises",
        "description": "Mantises are predatory insects recognised by their raptorial "
                       "forelegs, folded in the prayer-like posture that gives the order "
                       "its name. Their heads are exceptionally mobile, turning through "
                       "large angles to track prey, and many species have a single "
                       "faceted eye that appears to give binocular vision where the other "
                       "is blind. They occur on every continent except Antarctica, with "
                       "the greatest diversity in the tropics, and typically ambush prey "
                       "that approaches within a striking range. Mating behaviour "
                       "involves the male offering a nutritional package to the female, "
                       "who may eat the male afterwards, a combination of courtship gift "
                       "and predation that has been studied intensively.",
    },
    "dermaptera": {
        "name": "Dermaptera", "commonName": "Earwigs",
        "description": "Earwigs are recognised by the paired forceps-like cerci at the "
                       "end of the abdomen, which are straight in the suborder "
                       "Forficulura and curved in the second suborder. Most are "
                       "omnivorous scavengers living near the soil surface and under "
                       "bark, but a minority are predatory. Despite their common name "
                       "the earwigs are not especially associated with human ears, "
                       "though they are attracted to warmth and to damp, sheltered "
                       "places. Several species are wingless, including the widely "
                       "introduced European earwig, and the order is one of very few "
                       "whose female cares for her eggs and young nymphs.",
    },
    "grylloblattodea": {
        "name": "Grylloblattodea", "commonName": "Rock crawlers",
        "description": "Grylloblattodea, commonly called rock crawlers, was long "
                       "treated as an offshoot of the Orthoptera but is now understood as "
                       "its own ancient order, morphologically intermediate between the "
                       "cockroaches and crickets. All members are wingless, slow-moving "
                       "and strongly nocturnal, and they live in cold, high-altitude "
                       "habitats -- glacier margins, talus slopes and ice caves -- where "
                       "they feed on windblown organic matter and on whatever small "
                       "animals they can catch. The order contains a single family and "
                       "fewer than forty described species, several of which are "
                       "restricted to a single mountain range, making it one of the most "
                       "vulnerable insect orders in terms of habitat loss.",
    },
    "zoraptera": {
        "name": "Zoraptera", "commonName": "Angel insects",
        "description": "Angel insects are a small order of minute insects, a few "
                       "millimetres long, that live in damp forest litter and on rotting "
                       "wood. They have two forms: a pale, wingless morph that lives in "
                       "the soil, and a darker winged morph that disperses to foliage, a "
                       "pattern otherwise associated with termites and psocids. The "
                       "group was controversial for a century because its affinities "
                       "remained unclear, and it has variously been placed among the "
                       "Embioptera, Psocodea and termites. The order contains one "
                       "recognised family and roughly thirty species, so its discovery "
                       "history and its tiny diversity are the main things that keep it "
                       "out of general knowledge.",
    },
    "coleorrhyncha": {
        "name": "Coleorrhyncha", "commonName": "Twisted-wing parasites",
        "description": "Coleorrhyncha, the twisted-wing parasites, is one of the smallest "
                       "insect orders and has one family of about thirty described species. "
                       "They are obligate parasitoids of booklice and barklice "
                       "(Psocodea), which they locate by chemical cues, attacking the "
                       "nymphs and injecting a virus-like agent that suppresses the host's "
                       "immune response so the parasite can develop inside it. The order "
                       "is remarkable for the males' fan-like hind wings, which are "
                       "strongly twisted and function as a courtship display rather than "
                       "for flight, and which were long mistaken for highly modified "
                       "forewings. Nothing about them suggested they belonged together, "
                       "which is why the order sat alone in its own superfamily for "
                       "decades.",
    },
    # The Aphid Species File covers infraorder Aphidomorpha. We hold no
    # Hemiptera at all, so it creates the order -- but only Aphidomorpha of it,
    # which the description says rather than letting a reader assume the order
    # is otherwise complete.
    "aphid": {
        "name": "Hemiptera", "commonName": "True bugs",
        "description": "Hemiptera, the true bugs, is the largest order of "
                       "non-flying insects and one of the largest orders of "
                       "insects overall, with roughly 80,000 species in some "
                       "300 families. They are defined by piercing-sucking "
                       "mouthparts: a rostrum enclosing needle-like stylets "
                       "that pierce plant or animal tissue, which is why so many "
                       "are serious agricultural pests. What is present here is "
                       "currently infraorder Aphidomorpha only -- the aphids and "
                       "their relatives -- imported from the Aphid Species File, "
                       "so the rest of the order is not yet covered. Aphid "
                       "morphology is distinctive: pear-shaped soft-bodied "
                       "insects with cornicles, paired abdominal projections "
                       "that vent defensive droplets, and a near-universal "
                       "parthenogenetic life cycle in which females reproduce "
                       "without mating, often for most of the year.",
    },
    # Chrysididae is a family of Hymenoptera, not an order, so it lands under
    # Hymenoptera while the rest land under Insecta.
    "chrysididae": {
        "parent": "Hymenoptera", "name": "Chrysididae",
        "commonName": "Cuckoo wasps",
        "description": None,  # family-level description belongs to the data file
    },
}


def find_node(node, pred):
    if pred(node):
        return node
    for c in node.get("children") or []:
        r = find_node(c, pred)
        if r:
            return r
    return None


def collect_family_ids(node, out):
    if node.get("rank") == "FAMILY":
        out.add(node.get("id"))
    for c in node.get("children") or []:
        collect_family_ids(c, out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--taxonomy", default=TAXONOMY)
    args = ap.parse_args()

    raw = open(args.taxonomy, encoding="utf-8").read()
    tax = json.loads(raw)
    arthropoda = find_node(tax, lambda n: n.get("rank") == "CLASS" and n.get("name") == "Insecta")
    if not arthropoda:
        sys.exit("FATAL: Insecta class node not found")

    used_ids = collect_family_ids(tax, set())
    used_names = {}
    for o in arthropoda["children"]:
        used_names.setdefault(o["name"].lower(), o["name"])

    added_orders, adopted, added_families, updated = [], [], [], 0
    for slug, meta in ORDERS.items():
        frag_path = f"/tmp/{slug}_families.json"
        if not os.path.exists(frag_path):
            sys.exit(f"FATAL: {frag_path} missing -- run\n"
                     f"       python3 scripts/importSpeciesFile.py --slug {slug}\n"
                     f"       first; it writes the fragment on a dry run.")
        frag = json.load(open(frag_path, encoding="utf-8"))

        if meta.get("parent"):
            parent = find_node(tax, lambda n: n.get("name") == meta["parent"])
            holder = parent
            if holder is None:
                sys.exit(f"FATAL: {meta['parent']} not found")
            # Families go straight into the parent. This must be set on every
            # iteration: left to default, `bucket` holds the previous slug's
            # order and the family lands in the wrong order entirely.
            bucket = None
        else:
            # Compare lowercased: used_names is keyed that way, and
            # "Plecoptera" not being in {"plecoptera": ...} made this silently
            # propose re-adding seven orders that already exist.
            if meta["name"].lower() in used_names:
                # Adopt the existing order and add to it. Aborting here made the
                # script all-or-nothing across every slug, so it could only ever
                # be run once -- which is also how the case-sensitivity bug below
                # survived to propose duplicating seven orders.
                bucket = next(o for o in arthropoda["children"]
                              if o["name"].lower() == meta["name"].lower())
                adopted.append(meta["name"])
            else:
                bucket = {"id": meta["name"].upper(), "name": meta["name"],
                          "rank": "ORDER", "commonName": meta["commonName"],
                          "description": meta["description"],
                          "extinct": False, "fossil": False, "children": []}
                arthropoda["children"].append(bucket)
                added_orders.append(meta["name"])

        existing_by_name = {c["name"].lower(): c for c in (holder["children"]
                                                           if bucket is None else bucket["children"])
                            if c.get("rank") == "FAMILY"}
        for f in frag:
            name = f["name"]
            base = "FAM_" + name.upper().replace(" ", "").replace("†", "")
            fid = base
            # A name can be claimed twice across kingdoms. The fossil stonefly
            # †Personidae is a real homonym of the gastropod family Personidae
            # already in the tree, and both are legitimate -- the fossil one is
            # not the mollusc. Collapsing them onto one id would make whichever
            # lost the race unresolvable, so the second gets a suffix. The †
            # stays in `name`, which is what marks it extinct downstream.
            n = 2
            while fid in used_ids and name.lower() not in existing_by_name:
                fid = f"{base}_{n}"
                n += 1
            target = existing_by_name.get(name.lower())
            if target:
                if target.get("speciesCount") != f["speciesCount"]:
                    updated += 1
                target["speciesCount"] = f["speciesCount"]
                target["appSlug"] = f["appSlug"]
                continue
            node = {"id": fid, "name": name, "rank": "FAMILY",
                    "appSlug": f["appSlug"], "speciesCount": f["speciesCount"]}
            (holder["children"] if bucket is None else bucket["children"]).append(node)
            used_ids.add(fid)
            added_families.append(f"{meta['name']}/{name}")

    if bucket is not None and len(ORDERS) > 1:
        arthropoda["children"].sort(key=lambda o: o["name"])

    print(f"orders added:   {len(added_orders)}  {', '.join(added_orders)}")
    if adopted:
        print(f"orders adopted: {len(adopted)}  {', '.join(adopted)}")
    print(f"families added: {len(added_families)}")
    print(f"families updated (speciesCount): {updated}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0
    with open(args.taxonomy, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(tax, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote {args.taxonomy}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
