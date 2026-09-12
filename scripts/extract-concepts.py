#!/usr/bin/env python3
"""Extract ISO 93333 clause-3 entries into geolexica-shaped concept YAML,
with authored concept-system relations (generic / partitive / associative).

Source of truth: the Metanorma draft (cc-dpp-vocabulary). Re-run after any
vocabulary change; the sync check (scripts/check-concepts.py) compares the
generated set against the draft and fails on drift.
"""
import re
import sys
import pathlib

SRC = pathlib.Path.home() / "src/calconnect/cc-dpp-vocabulary/sources/iso-93333/sections"
OUT = pathlib.Path(__file__).resolve().parent.parent / "concepts"
OUT.mkdir(exist_ok=True)


def clean(t):
    t = re.sub(r"[`*_]", "", t).strip()
    return re.sub(r"\s+", " ", t)


entries, order = {}, []
for f in sorted(SRC.glob("03-*.adoc")):
    stem = f.stem.split("-")
    group = stem[0] + "-" + stem[1]
    text = f.read_text()
    for m in re.finditer(
        r'(?:\[\[[^\]]*\]\]\n\n?)?=== ([^\n]+)\n(.*?)(?=\n(?:\[\[[^\]]*\]\]\n\n?)?=== |\Z)',
        text, re.S,
    ):
        term, body = clean(m.group(1)), m.group(2)
        defpara, notes, sources, alts = [], [], [], []
        for ln in body.split("\n"):
            s = ln.strip()
            if not s:
                continue
            if s.startswith("NOTE:"):
                notes.append(clean(s[5:]))
            elif s.startswith("[.source]"):
                continue
            elif s.startswith("<<"):
                sources += re.findall(r"<<([^>,]+)", s)
            elif s.startswith("alt:"):
                alts.append(clean(s[4:]))
            elif s.startswith("="):
                continue
            else:
                defpara.append(s)
        if not defpara:
            continue
        domain = any(n.startswith("Domain-scoped entry") for n in notes)
        entry = dict(
            term=term,
            definition=clean(" ".join(defpara)),
            notes=[n for n in notes if not n.startswith("Domain-scoped entry")],
            sources=[clean(x) for x in sources],
            alts=alts,
            group=group,
            domain=domain,
        )
        if term not in entries:
            entries[term] = entry
            order.append(term)

# Authored concept-system relations: term -> [(relation type, target term)]
# Types: broader / narrower (generic); part_of / has_part / narrower_part
# (partitive); associative; equivalent.
R = {
 "digital product passport": [("broader", "projection"), ("has_part", "profile"), ("associative", "digital twin")],
 "digital product passport id": [("part_of", "digital product passport")],
 "unique product identifier": [("broader", "unique identifier")],
 "identification": [("associative", "identification scheme")],
 "identification scheme": [("associative", "domain")],
 "self-issuing system": [("associative", "issuing agency")],
 "persistence": [("associative", "unique identifier")],
 "economic operator": [("broader", "actor")],
 "digital product passport service provider": [("broader", "actor")],
 "main digital product passport service provider": [("narrower_part", "digital product passport service provider")],
 "back-up digital product passport service provider": [("narrower_part", "digital product passport service provider")],
 "issuing agency": [("broader", "actor")],
 "notified actor": [("broader", "actor")],
 "consumer": [("broader", "actor")], "customer": [("broader", "actor")],
 "expert": [("broader", "actor")], "reviewer": [("broader", "actor")],
 "exporter": [("broader", "actor")], "seller": [("broader", "actor")],
 "subcontractor": [("broader", "actor")], "buyer": [("broader", "actor")],
 "producer": [("broader", "actor")], "supplier": [("broader", "actor")],
 "retailer": [("broader", "actor")], "sorter": [("broader", "actor")],
 "recycler": [("broader", "actor")],
 "yarn producer": [("broader", "actor"), ("associative", "textile product")],
 "apparel producer": [("broader", "actor"), ("associative", "textile product")],
 "textile collector": [("broader", "actor"), ("associative", "textile product")],
 "eService platform": [("associative", "actor")],
 "traceability platform": [("associative", "traceability")],
 "sustainability management platform": [("associative", "circular economy")],
 "textile product": [("narrower", "product")],
 "product circularity": [("narrower", "circular economy")],
 "end-of-use": [("part_of", "life cycle")], "end-of-life": [("part_of", "life cycle")],
 "collection": [("associative", "circular economy")],
 "value chain": [("associative", "life cycle")],
 "traceability system": [("has_part", "traceable asset")],
 "controlled DPP data": [("part_of", "digital product passport")],
 "verification": [("associative", "validation")],
 "Asset Administration Shell": [("has_part", "Submodel")],
 "Submodel": [("has_part", "SubmodelElement"), ("narrower_part", "Asset Administration Shell")],
 "SubmodelElement": [("narrower_part", "Submodel"), ("has_part", "property")],
 "Submodel template": [("broader", "Submodel")],
 "Submodel template element": [("narrower_part", "Submodel template")],
 "type asset": [("broader", "asset")], "instance asset": [("broader", "asset")],
 "property": [("narrower_part", "SubmodelElement")],
 "capability": [("narrower_part", "SubmodelElement")],
 "operation": [("narrower_part", "SubmodelElement")],
 "digital twin": [("broader", "digital representation")],
 "mass balance model": [("associative", "mass balance accounting")],
 "profile": [("equivalent", "lens")],
 "jurisdiction profile": [("narrower", "profile")],
 "sector overlay": [("narrower", "profile")],
 "lens": [("equivalent", "profile"), ("associative", "trust list")],
 "as-of query": [("associative", "as-of state")],
 "materialized view": [("equivalent", "projection")],
 "child passport": [("associative", "digital product passport")],
 "containment event": [("associative", "installation")],
 "genealogy": [("associative", "derived passport")],
 "offline minimum": [("narrower_part", "Tier-A payload")],
 "degradation ladder": [("has_part", "Tier-A payload"), ("has_part", "Tier-B payload"), ("has_part", "Tier-C archive")],
 "dormant identifier": [("narrower", "unique identifier")],
 "dormant-to-live adoption": [("associative", "dormant identifier")],
 "device commitment": [("associative", "edge segment")],
 "roll-up attestation": [("associative", "traversal set")],
 "stamp": [("narrower_part", "lens-scoped attestation")],
 "lens-scoped attestation": [("has_part", "stamp"), ("broader", "jurisdiction stamp")],
 "jurisdiction stamp": [("narrower_part", "lens-scoped attestation")],
 "derived passport": [("broader", "digital product passport"), ("associative", "transformation event")],
 "transformation event": [("has_part", "inputReference"), ("has_part", "quantity carve-out")],
 "inputReference": [("narrower_part", "transformation event")],
 "quantity carve-out": [("narrower_part", "transformation event")],
 "mass balance accounting": [("broader", "mass balance model")],
 "consumed passport": [("associative", "transformation event")],
 "blind provenance": [("associative", "blind edge")],
 "characteristic profile": [("narrower", "profile"), ("has_part", "trigger predicate")],
 "trigger predicate": [("narrower_part", "characteristic profile")],
 "commissioning": [("associative", "qualified attestor")],
 "attribution": [("associative", "qualified attestor")],
 "provenance gap": [("associative", "attribution")],
 "condition report": [("associative", "provenance gap")],
 "restitution flag": [("associative", "provenance gap")],
 "silent subject": [("narrower_part", "capability class")],
 "passive-auth subject": [("narrower_part", "capability class")],
 "logged-contact subject": [("narrower_part", "capability class")],
 "connected subject": [("narrower_part", "capability class")],
 "passive twin": [("narrower_part", "digital twin")],
 "active twin": [("narrower_part", "digital twin")],
 "truth mode": [("associative", "active twin")],
 "service-center model": [("associative", "passive twin")],
 "self-testimony": [("associative", "active twin")],
 "state of health": [("associative", "sensor attestation")],
 "continuous conformity monitoring": [("associative", "state of health")],
 "sensor attestation": [("associative", "state of health")],
 "installation": [("associative", "association"), ("associative", "membership")],
 "association": [("associative", "installation"), ("associative", "membership")],
 "membership": [("associative", "installation"), ("associative", "group node")],
 "group node": [("has_part", "membership")],
 "binding strength": [("part_of", "installation")],
 "slot identity": [("part_of", "installation")],
 "pairing": [("part_of", "installation")],
 "absorbed component": [("narrower_part", "component")],
 "recoverability": [("part_of", "installation")],
 "harvested part": [("associative", "installation")],
 "custody transfer": [("associative", "custodian")],
 "custodian": [("broader", "actor")],
 "blind edge": [("associative", "installation")],
 "escrowed disclosure": [("associative", "blind edge")],
 "proof of binding": [("associative", "blind edge")],
 "enumeration resistance": [("associative", "blind edge")],
 "predicate-based recall": [("associative", "traversal set")],
 "owner-push disclosure": [("associative", "blind edge")],
 "dark identity": [("narrower_part", "unique identifier")],
 "confidential profile": [("narrower_part", "profile")],
 "trust marker": [("associative", "trust list")],
 "master list": [("broader", "trust list")],
 "revocation window": [("associative", "trust marker")],
 "three verification readings": [("associative", "verification")],
 "freshness verdict": [("associative", "verification")],
 "coverage report": [("associative", "verification")],
 "discovery registry": [("has_part", "service descriptor"), ("has_part", "listing gate"), ("associative", "onboarding ceremony")],
 "service descriptor": [("narrower_part", "discovery registry"), ("has_part", "protocol binding"), ("has_part", "verification mechanism bundle")],
 "protocol binding": [("narrower_part", "service descriptor")],
 "verification mechanism bundle": [("narrower_part", "service descriptor")],
 "listing gate": [("narrower_part", "discovery registry")],
 "operator credential": [("associative", "service descriptor")],
 "onboarding ceremony": [("associative", "discovery registry")],
 "read federation": [("associative", "discovery registry")],
 "service federation": [("associative", "discovery registry")],
 "trust federation": [("associative", "discovery registry")],
 "seed bundle": [("associative", "onboarding ceremony")],
 "registry pinning": [("associative", "seed bundle")],
}

missing = [t for t in R if t not in entries]
bad = [(t, tt) for t, rl in R.items() for _, tt in rl if tt not in entries]
if missing or bad:
    print("MISSING terms:", missing)
    print("BAD targets:", bad)
    sys.exit(1)

tid = {t: i for i, t in enumerate(order, 1)}


def q(s):
    return '"' + s.replace('"', '\\"') + '"'


total_rel = 0
for t in order:
    e = entries[t]
    y = [
        "---",
        f"term: {q(t)}",
        f"termid: {tid[t]}",
        "eng:",
        f"  id: {tid[t]}",
        f"  term: {q(t)}",
        f"  definition: {q(e['definition'])}",
        "  language_code: eng",
    ]
    if e["notes"]:
        y.append("  notes:")
        y += [f"  - {q(n)}" for n in e["notes"]]
    else:
        y.append("  notes: []")
    y += ["  examples: []", "  entry_status: valid", "  classification: preferred"]
    if e["sources"]:
        y.append("  authoritative_source:")
        y.append(f"    ref: {q(', '.join(e['sources']))}")
        y.append("    clause: '3'")
    y.append("  date_accepted: '2026-09-12'")
    y += [
        "custom:",
        f"  clause_group: {q(e['group'])}",
        f"  domain_scoped: {str(e['domain']).lower()}",
    ]
    rels = R.get(t, [])
    if rels:
        y.append("related:")
        for typ, target in rels:
            y.append(f"- type: {typ}")
            y.append(f"  target: {tid[target]}")
            total_rel += 1
    (OUT / f"concept-{tid[t]}.yaml").write_text("\n".join(y) + "\n")

index = ["# concept index (generated by scripts/extract-concepts.py)"]
for t in order:
    index.append(f"{tid[t]}\t{t}\t{entries[t]['group']}")
(OUT / "index.txt").write_text("\n".join(index) + "\n")
print(f"concepts: {len(order)}, relations: {total_rel}")
