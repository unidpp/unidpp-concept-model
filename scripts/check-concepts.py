#!/usr/bin/env python3
"""Validate the concept set: structure, term uniqueness, relation
integrity, the domain-scope discipline, and synchronization with the
Metanorma draft (cc-dpp-vocabulary). Exits non-zero on any failure."""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CON = ROOT / "concepts"
SRC = pathlib.Path.home() / "src/calconnect/cc-dpp-vocabulary/sources/iso-93333/sections"

TYPES = {"broader", "narrower", "part_of", "has_part", "narrower_part",
         "associative", "equivalent"}
errors = []


def fail(msg):
    errors.append(msg)


def parse(path):
    text = path.read_text()
    d = {"term": None, "termid": None, "definition": False,
         "notes": [], "related": [], "domain": None, "group": None}
    m = re.search(r'^term: "(.*)"$', text, re.M)
    if m:
        d["term"] = m.group(1)
    m = re.search(r"^termid: (\d+)$", text, re.M)
    if m:
        d["termid"] = int(m.group(1))
    if re.search(r"^  definition: ", text, re.M):
        d["definition"] = True
    for n in re.findall(r'^  - "(.*)"$', text, re.M):
        d["notes"].append(n)
    cur = None
    for ln in text.split("\n"):
        s = ln.strip()
        m = re.match(r"- type: (\w+)$", s)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"target: (\d+)$", s)
        if m and cur:
            d["related"].append((cur, int(m.group(1))))
            cur = None
    m = re.search(r"^  domain_scoped: (true|false)$", text, re.M)
    if m:
        d["domain"] = m.group(1) == "true"
    m = re.search(r'^  clause_group: "(.*)"$', text, re.M)
    if m:
        d["group"] = m.group(1)
    return d


files = sorted(CON.glob("concept-*.yaml"))
by_id, by_term = {}, {}
for f in files:
    d = parse(f)
    if not d["term"] or d["termid"] is None:
        fail(f"{f.name}: missing term or termid")
        continue
    if not d["definition"]:
        fail(f"{f.name}: missing definition")
    if d["termid"] in by_id:
        fail(f"{f.name}: duplicate termid {d['termid']}")
    if d["term"] in by_term:
        fail(f"{f.name}: duplicate term '{d['term']}'")
    by_id[d["termid"]] = d
    by_term[d["term"]] = d

for tid, d in by_id.items():
    for typ, target in d["related"]:
        if typ not in TYPES:
            fail(f"concept-{tid}: unknown relation type '{typ}'")
        if target not in by_id:
            fail(f"concept-{tid}: relation target {target} does not exist")
    if d["domain"] is None or d["group"] is None:
        fail(f"concept-{tid}: missing custom block")
    # The domain-scope note is carried by the flag here; the draft-side
    # check follows below.

# Sync with the draft: the term set of the draft equals the term set here.
draft_terms = set()
for f in sorted(SRC.glob("03-*.adoc")):
    for m in re.finditer(r"^=== ([^\n]+)$", f.read_text(), re.M):
        t = re.sub(r"\s+", " ", m.group(1).strip())
        draft_terms.add(t)
extra = set(by_term) - draft_terms
missing = draft_terms - set(by_term)
if extra:
    fail(f"concepts not in draft: {sorted(extra)[:5]}")
if missing:
    fail(f"draft terms missing from the set: {sorted(missing)[:5]}")

# Domain-scope discipline: the number of domain-scoped flags equals the
# number of domain-scope notes in the draft.
draft_domain_notes = 0
for f in sorted(SRC.glob("03-*.adoc")):
    draft_domain_notes += f.read_text().count("NOTE: Domain-scoped entry")
flagged = sum(1 for d in by_id.values() if d["domain"])
if draft_domain_notes != flagged:
    fail(f"domain-scope drift: {draft_domain_notes} notes in the draft, "
         f"{flagged} flags in the set")

# Index consistency.
idx = (CON / "index.txt").read_text().split("\n")[1:]
idx_ids = {int(l.split("\t")[0]) for l in idx if l and not l.startswith("#")}
if idx_ids != set(by_id):
    fail("index.txt out of sync with the concept files")

rel_count = sum(len(d["related"]) for d in by_id.values())
unrelated = [d["term"] for d in by_id.values() if not d["related"]]

if errors:
    for e in errors:
        print(f"FAIL: {e}")
    sys.exit(1)
print(f"concepts: {len(by_id)}, relations: {rel_count}, "
      f"domain-scoped: {sum(1 for d in by_id.values() if d['domain'])}, "
      f"entries without relations (informational): {len(unrelated)}")
print("concept set valid and synchronized with the draft")
