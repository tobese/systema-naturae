"""Measure the dedupe's outcome against GBIF, reading the working tree directly.

Three outcomes matter for every removed node:
  correct    the surviving copy is in the family GBIF assigns the usageKey
  regression the dedupe discarded the only correctly-placed copy
  neutral    neither copy was in that family, so no choice was right

Same-file collisions are the trap: both copies sit in one family, so removing
either is correct and a naive "did we remove something in GBIF's family" test
reports all of them as regressions. That miscount is what made an earlier
version of this look like 1,647 broken removals.
"""
import collections
import json
import subprocess
import sys

sys.path.insert(0, "scripts")
from tree import iter_family_files, iter_species_with_parent, KINGDOMS  # noqa: E402

PRE = "f38eb7458a^"      # the last commit before the dedupe emptied 689 families
norm = lambda x: (x or "").lower().replace(" ", "").replace("-", "")


def survivors_by_key():
    """usageKey -> the set of families the working tree still holds it in."""
    where = collections.defaultdict(set)
    for kingdom in KINGDOMS:
        for fam in iter_family_files(kingdom):
            try:
                d = fam.load()
            except Exception:
                continue
            slug = fam.path.split("/src/data")[0].split("/")[-1].lower()
            for _parent, s in iter_species_with_parent(d):
                key = str((s.get("sourceIds") or {}).get("gbif") or "")
                if key:
                    where[key].add(slug)
    return where


def main():
    cache = json.load(open("portal/data/gbif-family-cache.json"))
    fams = cache["families"]
    where = survivors_by_key()

    files = [f for f in subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "taxonomy"],
        capture_output=True, text=True).stdout.split()
        if f.endswith(".json") and "/src/data/" in f]

    proc = subprocess.Popen(["git", "cat-file", "--batch"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    counts = collections.Counter()
    regressions = collections.Counter()
    for f in files:
        proc.stdin.write(f"{PRE}:{f}\n".encode())
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        if len(header) < 3:
            continue
        pre = json.loads(proc.stdout.read(int(header[2])))
        proc.stdout.read(1)
        now = {s["id"] for _q, s in
               iter_species_with_parent(json.loads(open(f).read()))
               if s.get("id")}
        for _q, s in iter_species_with_parent(pre):
            sid = s.get("id")
            if not sid or sid in now:
                continue
            key = str((s.get("sourceIds") or {}).get("gbif") or "")
            want = fams.get(key)
            if not want:
                counts["no cached family"] += 1
                continue
            held = {norm(x) for x in where.get(key, set())}
            removed_from = norm(f.split("/src/data")[0].split("/")[-1].lower())
            if norm(want) in held:
                counts["correct"] += 1
            elif norm(want) == removed_from:
                # We threw away the only copy in the family GBIF names, and kept
                # one GBIF contradicts. This is the real damage.
                counts["regression"] += 1
                regressions[key] += 1
            else:
                # Neither copy is in GBIF's family -- `Cicurina porteri` sits in
                # cicurinidae and dictynidae while GBIF says Hahniidae. The tree
                # never placed it correctly, so which copy survives is not a
                # decision this dedupe can get wrong.
                counts["neutral (neither copy was in GBIF's family)"] += 1
    proc.stdin.close()
    proc.wait()

    total = sum(counts.values())
    print(f"removed nodes measured: {total:,}")
    for k, v in counts.most_common():
        print(f"  {v:>6,}  {k}")
    if regressions:
        print(f"  regressions by usageKey: {len(regressions)}")


if __name__ == "__main__":
    main()
