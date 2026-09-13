#!/usr/bin/env python3
"""Build the static documentation site of the two model sets into html/."""
import html
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "html"
OUT.mkdir(exist_ok=True)

GROUP_TITLES = {
    "03-1": "The digital product passport", "03-2": "Identity and carriers",
    "03-3": "Actors", "03-4": "Life cycle", "03-5": "Trust and verification",
    "03-6": "Semantics", "03-7": "Measurement",
    "03-8": "Framework: profiles", "03-9": "Framework: projection",
    "03-10": "Framework: provenance and the identity lattice",
    "03-11": "Framework: stamps and the transformation algebra",
    "03-12": "Framework: characteristic profiles",
    "03-13": "Framework: capability classes and twins",
    "03-14": "Framework: the relationship algebra",
    "03-15": "Framework: visibility", "03-16": "Framework: federation",
    "03-17": "Framework: the scheme calculus, sovereignty segments and the projection calculus",
    "annex-b": "Annex B (informative): AAS vocabulary",
}
MODEL_TITLES = {
    "identity": "Identity and the identity lattice",
    "record": "Record and twin",
    "projection": "Projection and the projection calculus",
    "trust": "Trust and the party model",
    "semantics": "Semantics and the registry",
    "scheme": "The scheme calculus",
    "algebra": "The product algebra",
}
VIEW_CAPTIONS = {
    "IdentityLattice": "Identity, carriers and the identity lattice",
    "PartyModel": "The party model and the trust objects",
    "ProjectionCalculus": "Projection, segments, the descriptor and the frozen view",
    "ProductAlgebra": "The product algebra",
    "SchemeCalculus": "Schemes, declarations, the layer vector and routes",
    "RecordAndSemantics": "Events, twin, commitments and the registry",
}

STYLE = """
body{font:15px/1.55 Georgia,serif;margin:0;color:#1c1c1c;background:#faf9f7}
header{border-bottom:2px solid #234;border-spacing:0;padding:1rem 2rem;
 background:#fff;display:flex;justify-content:space-between;align-items:baseline}
header a{color:#234;text-decoration:none;font-family:Menlo,monospace;font-size:.85rem}
main{max-width:70rem;margin:2rem auto;padding:0 2rem}
h1{font-size:1.6rem}h2{font-size:1.15rem;margin-top:2.4rem;color:#234;
 border-bottom:1px solid #ccc;padding-bottom:.3rem}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.85rem;
 font-family:Menlo,monospace}
th,td{border:1px solid #ddd;padding:.35rem .55rem;text-align:left;vertical-align:top}
th{background:#f0efe9;font-weight:600}
img{max-width:100%;border:1px solid #ddd;background:#fff}
.note{color:#666;font-size:.8rem}
.dom{background:#fdf3d7}
a{color:#045}
"""


def esc(s):
    return html.escape(s, quote=True)


def load_concepts():
    cons = {}
    for f in sorted((ROOT / "concepts").glob("concept-*.yaml")):
        t = f.read_text()
        term = re.search(r'^term: "(.*)"$', t, re.M).group(1)
        tid = int(re.search(r"^termid: (\d+)$", t, re.M).group(1))
        definition = re.search(r'^  definition: "(.*)"$', t, re.M).group(1)
        group = re.search(r'^  clause_group: "(.*)"$', t, re.M).group(1)
        domain = re.search(r"^  domain_scoped: (true|false)$", t, re.M).group(1) == "true"
        rels, cur = [], None
        for ln in t.split("\n"):
            s = ln.strip()
            m = re.match(r"- type: (\w+)$", s)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r"target: (\d+)$", s)
            if m and cur:
                rels.append((cur, int(m.group(1))))
                cur = None
        inf = re.search(r"^  informative: (true|false)$", t, re.M)
        cons[tid] = dict(term=term, definition=definition, group=group,
                         domain=domain, rels=rels,
                         informative=bool(inf and inf.group(1) == "true"))
    return cons


def model_stats():
    stats = {}
    for f in sorted((ROOT / "models").glob("*.lutaml")):
        t = f.read_text()
        classes = re.findall(r"^(?:abstract )?class (\w+)", t, re.M)
        enums = re.findall(r"^enum (\w+)", t, re.M)
        stats[f.stem] = (classes, enums)
    return stats


def build():
    cons = load_concepts()
    stats = model_stats()

    # models page
    sections = ["<h2>Structural models</h2>"]
    sections.append(
        "<p>Each model states its classes, attributes, enumerations and "
        "definitions, in LutaML, one file per concern. The diagrams are "
        "rendered from the same sources.</p>")
    for stem, title in MODEL_TITLES.items():
        classes, enums = stats[stem]
        view = next(
            (v for v in VIEW_CAPTIONS
             if v.lower().startswith(stem[:6])
             and (ROOT / "views" / (v + ".lutaml")).exists()),
            stem,
        )
        imgp = ROOT / "images" / (view + ".png")
        img = f"images/{view}.png" if imgp.exists() else None
        body = [f"<h3>{esc(title)}</h3>",
                f"<p class='note'>models/{stem}.lutaml — "
                f"{len(classes)} classes, {len(enums)} enumerations"
                + (f"; view {view}" if img else "") + "</p>"]
        if img:
            body.append(f"<img src='{img}' alt='{esc(title)} diagram'>")
        body.append("<details><summary>Classes</summary><ul>" +
                    "".join(f"<li><code>{esc(c)}</code></li>" for c in classes) +
                    "</ul></details>")
        sections.append("\n".join(body))

    models_html = page("Models of the UniDPP framework", "\n".join(sections),
                       "models")
    (OUT / "index.html").write_text(models_html)

    # concepts page
    groups = {}
    for tid, c in sorted(cons.items()):
        groups.setdefault(c["group"], []).append((tid, c))
    rows = []
    for group in sorted(groups):
        rows.append(f"<h2>{esc(GROUP_TITLES.get(group, group))}</h2>")
        rows.append("<table><tr><th>id</th><th>term</th><th>definition</th>"
                    "<th>relations</th></tr>")
        for tid, c in groups[group]:
            rels = "; ".join(f"{typ} → {cons[t]['term']}"
                             for typ, t in c["rels"] if t in cons) or "—"
            cls = " class='dom'" if c["domain"] else ""
            dom = " ▲domain-scoped" if c["domain"] else ""
            dom += " ▲informative" if c.get("informative") else ""
            rows.append(
                f"<tr{cls}><td>{tid}</td>"
                f"<td><b>{esc(c['term'])}</b>{dom}</td>"
                f"<td>{esc(c['definition'][:400])}</td>"
                f"<td>{esc(rels)}</td></tr>")
        rows.append("</table>")
    note = ("<p class='note'>Domain-scoped entries (marked) carry criteria of "
            "application owned by a community; they are recorded for "
            "navigational completeness and are not harmonized across "
            "communities.</p>")
    concepts_html = page("Concepts of the DPP vocabulary (ISO 93333)",
                         note + "\n".join(rows), "concepts")
    (OUT / "concepts.html").write_text(concepts_html)

    if (ROOT / "images").exists():
        shutil.copytree(ROOT / "images", OUT / "images", dirs_exist_ok=True)
    print(f"site built: {OUT} (index.html, concepts.html, "
          f"{len(cons)} concepts)")


def page(title, body, active):
    nav = [("index.html", "Models"), ("concepts.html", "Concepts"),
           ("https://unidpp.org", "unidpp.org")]
    links = " · ".join(f'<a href="{h}">{esc(t)}</a>' if t.lower() != active.lower()
                       else f"<b>{esc(t)}</b>" for h, t in nav)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{STYLE}</style></head>
<body><header><span>{esc(title)}</span><span>{links}</span></header>
<main>{body}</main></body></html>"""


if __name__ == "__main__":
    build()
