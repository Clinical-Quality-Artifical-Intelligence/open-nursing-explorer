#!/usr/bin/env python3
"""Build the Open Nursing Knowledge Explorer OKF bundle.

Parses the local NMC skill files (the Code, RN proficiency platforms 1-7,
SSSA) into a cross-linked markdown corpus, then emits an
okf-explorer-bundle.v0 JSON bundle consumable by the OKF Explorer app.

Sources: NMC Code (2015, updated 2018); Standards of Proficiency for
Registered Nurses (2018); Standards for Student Supervision and
Assessment (2018). All public NMC standards, nmc.org.uk.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SKILLS = Path("/Users/nursingcitizendevelopment/.claude/skills")
HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus"
BUNDLE_OUT = HERE / "okf-bundle.json"

CODE_TS = "2018-10-10T00:00:00Z"      # Code last updated
PROF_TS = "2018-05-17T00:00:00Z"      # Future Nurse proficiencies published
SSSA_TS = "2018-05-17T00:00:00Z"
GLOSS_TS = "2026-07-14T00:00:00Z"

THEME_SLUGS = {1: "prioritise-people", 2: "practise-effectively",
               3: "preserve-safety", 4: "promote-professionalism-and-trust"}

PLATFORM_TITLES = {
    1: "Being an accountable professional",
    2: "Promoting health and preventing ill health",
    3: "Assessing needs and planning care",
    4: "Providing and evaluating care",
    5: "Leading and managing nursing care and working in teams",
    6: "Improving safety and quality of care",
    7: "Coordinating care",
}

# Curated platform -> Code section mapping (editorially chosen, defensible)
PLATFORM_TO_CODE = {
    1: [1, 4, 6, 10, 13, 14, 16, 20, 22],
    2: [2, 3, 19],
    3: [2, 3, 4, 10, 13, 17],
    4: [1, 2, 3, 6, 18, 19],
    5: [8, 9, 11, 25],
    6: [14, 16, 17, 19, 23, 24],
    7: [3, 7, 8, 13, 25],
}

# Code section -> glossary term slugs
SECTION_TO_GLOSSARY = {
    1: ["person-centred-care"], 2: ["person-centred-care"],
    6: ["evidence-based-practice"], 11: ["delegation"],
    14: ["duty-of-candour"], 16: ["raising-concerns"],
    17: ["safeguarding"], 22: ["revalidation"],
    23: ["fitness-to-practise"],
}

GLOSSARY = {
    "person-centred-care": ("Person-centred care",
        "Care planned and delivered in partnership with the person, respecting their needs, preferences, values and right to be involved in decisions.",
        "Central to [Code section 1](../code/section-01.md), [Code section 2](../code/section-02.md) and [Platform 3](../platforms/platform-3.md) / [Platform 4](../platforms/platform-4.md)."),
    "evidence-based-practice": ("Evidence-based practice",
        "Practising in line with the best available evidence, keeping knowledge and skills up to date, and ensuring advice given is evidence-informed.",
        "Required by [Code section 6](../code/section-06.md) and threaded through every proficiency platform, especially [Platform 1](../platforms/platform-1.md)."),
    "duty-of-candour": ("Duty of candour",
        "The professional duty to be open and honest when something goes wrong: act to put it right, explain fully and promptly, and apologise.",
        "Set out in [Code section 14](../code/section-14.md) and assessed as proficiency 1.3 in [Platform 1](../platforms/platform-1.md)."),
    "delegation": ("Delegation",
        "Transferring the performance of a task to another person while retaining accountability for the delegation decision: delegate only within the other person's competence, supervise adequately, and confirm the outcome meets the required standard.",
        "Governed by [Code section 11](../code/section-11.md); delegation and assignment of care is assessed in [Platform 5](../platforms/platform-5.md)."),
    "raising-concerns": ("Raising concerns",
        "Acting without delay when there is a risk to patient safety or public protection, escalating through appropriate channels, and never obstructing others who raise concerns.",
        "Required by [Code section 16](../code/section-16.md) and [Code section 17](../code/section-17.md); proficiencies in [Platform 6](../platforms/platform-6.md) address reporting near misses and incidents."),
    "safeguarding": ("Safeguarding",
        "Protecting people who are vulnerable or at risk from harm, neglect or abuse, sharing information appropriately and keeping to relevant law.",
        "Required by [Code section 17](../code/section-17.md); safeguarding proficiencies appear in [Platform 3](../platforms/platform-3.md), [Platform 4](../platforms/platform-4.md) and [Platform 6](../platforms/platform-6.md)."),
    "revalidation": ("Revalidation",
        "The three-yearly NMC process by which registrants demonstrate continued fitness to practise: practice hours, CPD, reflective accounts, reflective discussion, feedback and confirmation.",
        "Underpinned by [Code section 22](../code/section-22.md); reflective accounts are written against the Code themes."),
    "fitness-to-practise": ("Fitness to practise",
        "A registrant's suitability to remain on the register without restriction — the NMC investigates concerns about conduct, competence or health.",
        "Cooperation with investigations is required by [Code section 23](../code/section-23.md)."),
    "supernumerary-status": ("Supernumerary status",
        "Students on NMC-approved programmes are additional to the workforce during practice placements: they learn through participation but are not counted in staffing numbers.",
        "A key principle of the [SSSA](../sssa/index.md) — see [key principles](../sssa/key-principles.md)."),
    "preceptorship": ("Preceptorship",
        "A structured period of support for newly registered professionals as they transition from student to accountable practitioner.",
        "Builds on [Platform 1](../platforms/platform-1.md); role-modelling expectations appear in [Code section 20](../code/section-20.md)."),
}

SSSA_ROLES = {
    "practice-supervisor": ("Practice supervisor",
        "Supports and supervises students in practice, contributing to their records and assessment.",
        """# Practice supervisor

Any **registered health or social care professional** can serve as a practice supervisor.

## Requirements
- Current knowledge and experience relevant to the student's proficiencies
- Receives preparation for the role
- Contributes to student records and to assessment decisions
- Provides ongoing support and supervision of students in practice

## In the framework
Practice supervisors support students towards the [proficiency platforms](../platforms/index.md) and role-model the [Code](../code/index.md) — see [Code section 9](../code/section-09.md) (support students' and colleagues' learning) and [Code section 20](../code/section-20.md) (act as a role model).

Related roles: [practice assessor](practice-assessor.md), [academic assessor](academic-assessor.md)."""),
    "practice-assessor": ("Practice assessor",
        "Conducts assessments and makes practice assessment decisions, informed by practice supervisors.",
        """# Practice assessor

## Requirements
- Registered with the NMC (or the relevant regulator for their profession)
- Current knowledge and experience in the student's field of practice
- Completes NMC-approved preparation
- Conducts assessments and makes assessment decisions
- Must be **different from the academic assessor** for each assessment period
- Collaborates with [practice supervisors](practice-supervisor.md) to gather evidence

## In the framework
Practice assessors judge achievement of the [proficiency platforms](../platforms/index.md); assessment decisions must reflect the standards of the [Code](../code/index.md), including [Code section 9](../code/section-09.md).

Related role: [academic assessor](academic-assessor.md)."""),
    "academic-assessor": ("Academic assessor",
        "Makes and records academic assessment decisions, considering practice assessor recommendations.",
        """# Academic assessor

## Requirements
- Registered with the NMC
- Current knowledge and expertise in the student's field of practice
- Makes and records academic assessment decisions
- Must be **different from the practice assessor** for each assessment period
- Considers recommendations from [practice assessors](practice-assessor.md)

## In the framework
Academic assessors confirm progression against the [proficiency platforms](../platforms/index.md) within the programme, upholding the [Code](../code/index.md)."""),
    "key-principles": ("SSSA key principles",
        "Supernumerary status, hub-and-spoke placements, raising concerns about students, reasonable adjustments, and inter-professional learning.",
        """# SSSA key principles

- **[Supernumerary status](../glossary/supernumerary-status.md)** of students during practice placements
- **Hub and spoke** placement models
- **Raising and escalating concerns** about students — see [Code section 16](../code/section-16.md)
- **Reasonable adjustments** for students with disabilities
- **Inter-professional learning** opportunities

These principles shape how [practice supervisors](practice-supervisor.md), [practice assessors](practice-assessor.md) and [academic assessors](academic-assessor.md) work together."""),
}


def fm(type_: str, title: str, description: str, ts: str, tags: list[str],
       resource: str = "", aliases: str = "") -> str:
    esc = lambda s: s.replace('"', "'")
    lines = ["---", f'type: "{esc(type_)}"', f'title: "{esc(title)}"',
             f'description: "{esc(description)}"', f"tags: [{', '.join(tags)}]",
             f"timestamp: {ts}"]
    if resource:
        lines.append(f'resource: "{resource}"')
    if aliases:
        lines.append(f'aliases: "{esc(aliases)}"')
    lines.append("---\n")
    return "\n".join(lines)


def parse_code() -> tuple[list[tuple[int, str]], dict[int, tuple[str, int, list[tuple[str, str]]]]]:
    text = (SKILLS / "nmc-code" / "SKILL.md").read_text(encoding="utf-8")
    themes: list[tuple[int, str]] = []
    sections: dict[int, tuple[str, int, list[tuple[str, str]]]] = {}
    current_theme = 0
    current_section = 0
    for line in text.splitlines():
        m = re.match(r"### Theme (\d): (.+)", line)
        if m:
            current_theme = int(m.group(1))
            themes.append((current_theme, m.group(2).strip()))
            continue
        m = re.match(r"\*\*(\d+)\. (.+)\*\*", line)
        if m and current_theme:
            current_section = int(m.group(1))
            sections[current_section] = (m.group(2).strip(), current_theme, [])
            continue
        m = re.match(r"- (\d+\.\d+) (.+)", line)
        if m and current_section and m.group(1).split(".")[0] == str(current_section):
            sections[current_section][2].append((m.group(1), m.group(2).strip()))
    return themes, sections


def parse_platform(n: int) -> list[tuple[str, str]]:
    text = (SKILLS / f"proficiency-rn-platform{n}" / "SKILL.md").read_text(encoding="utf-8")
    stmts = re.findall(r"\*\*(\d+\.\d+)\*\* (.+)", text)
    return [(num, body.strip()) for num, body in stmts if num.split(".")[0] == str(n)]


def code_section_page(num: int, title: str, theme_num: int, theme_title: str,
                      clauses: list[tuple[str, str]]) -> str:
    slug = THEME_SLUGS[theme_num]
    body = [f"# {num}. {title}\n",
            f"Theme: [{theme_title}](theme-{theme_num}-{slug}.md)\n",
            "## To achieve this, you must:\n"]
    body += [f"- **{cn}** {ct}" for cn, ct in clauses]
    platforms = [p for p, secs in PLATFORM_TO_CODE.items() if num in secs]
    if platforms:
        body.append("\n## Assessed through")
        body += [f"- [Platform {p}: {PLATFORM_TITLES[p]}](../platforms/platform-{p}.md)" for p in platforms]
    terms = SECTION_TO_GLOSSARY.get(num, [])
    if terms:
        body.append("\n## Key concepts")
        body += [f"- [{GLOSSARY[t][0]}](../glossary/{t}.md)" for t in terms]
    return "\n".join(body) + "\n"


def platform_page(n: int, stmts: list[tuple[str, str]]) -> str:
    body = [f"# Platform {n}: {PLATFORM_TITLES[n]}\n",
            "At the point of registration, the registered nurse will be able to:\n"]
    body += [f"- **{num}** {text}" for num, text in stmts]
    body.append("\n## Related Code sections")
    body += [f"- [Code section {s}](../code/section-{s:02d}.md)" for s in PLATFORM_TO_CODE[n]]
    body.append("\n## Assessment")
    body.append("Achievement is assessed in practice under the [Standards for Student Supervision and Assessment](../sssa/index.md).")
    return "\n".join(body) + "\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_corpus() -> None:
    themes, sections = parse_code()

    # Root index
    write(CORPUS / "index.md", fm(
        "Index", "Open Nursing Knowledge Explorer",
        "The NMC professional standards corpus — the Code, the Future Nurse proficiency platforms, and the SSSA — as a cross-linked open knowledge bundle.",
        GLOSS_TS, ["index", "root", "nmc", "nursing", "okf"],
        resource="https://www.nmc.org.uk/standards/") + """
# Open Nursing Knowledge Explorer

The professional standards that govern UK nursing, published by the Nursing and Midwifery Council (NMC), presented as a single cross-linked knowledge graph.

## Contents
- **[The Code](code/index.md)** — 25 professional standards across 4 themes (2015, updated 2018)
- **[Proficiency platforms](platforms/index.md)** — the 7 Future Nurse platforms every registered nurse must achieve (2018)
- **[Student supervision and assessment](sssa/index.md)** — the SSSA roles and principles (2018)
- **[Glossary](glossary/index.md)** — key professional concepts

## How the pieces fit
Every **proficiency platform** maps to the **Code** sections it enacts; the **SSSA** defines who supervises and assesses achievement of the platforms; the **glossary** anchors shared concepts. Use the graph view to see the whole web.

*An open resource from Nursing Citizen Development CIC. Content summarises public NMC standards — always refer to [nmc.org.uk/standards](https://www.nmc.org.uk/standards/) for the authoritative text.*
""")

    # Code index + themes + sections
    theme_links = "\n".join(
        f"- **[Theme {tn}: {tt}](theme-{tn}-{THEME_SLUGS[tn]}.md)** — sections "
        + ", ".join(f"[{sn}](section-{sn:02d}.md)" for sn, (st, stn, _) in sorted(sections.items()) if stn == tn)
        for tn, tt in themes)
    write(CORPUS / "code" / "index.md", fm(
        "Index", "The Code",
        "Professional standards of practice and behaviour for nurses, midwives and nursing associates — 25 sections in 4 themes.",
        CODE_TS, ["index", "code", "nmc"],
        resource="https://www.nmc.org.uk/standards/code/") + f"""
# The Code

Professional standards of practice and behaviour for nurses, midwives and nursing associates (NMC, 2015; updated 2018).

{theme_links}

Back to the [explorer root](../index.md).
""")

    for tn, tt in themes:
        section_list = "\n".join(
            f"- [{sn}. {st}](section-{sn:02d}.md)"
            for sn, (st, stn, _) in sorted(sections.items()) if stn == tn)
        write(CORPUS / "code" / f"theme-{tn}-{THEME_SLUGS[tn]}.md", fm(
            "Code theme", f"Theme {tn}: {tt}",
            f"Code theme {tn} of 4 — {tt}.", CODE_TS, ["code", "theme"]) + f"""
# Theme {tn}: {tt}

Sections in this theme:

{section_list}

Part of [the Code](index.md).
""")

    for sn, (st, stn, clauses) in sorted(sections.items()):
        tt = dict(themes)[stn]
        write(CORPUS / "code" / f"section-{sn:02d}.md", fm(
            "Code section", f"{sn}. {st}",
            f"Code section {sn} ({tt}): {st}.", CODE_TS,
            ["code", f"theme-{stn}"], aliases=f"code {sn}; section {sn}")
            + "\n" + code_section_page(sn, st, stn, tt, clauses))

    # Platforms
    plat_links = "\n".join(
        f"- [Platform {n}: {PLATFORM_TITLES[n]}](platform-{n}.md)" for n in range(1, 8))
    write(CORPUS / "platforms" / "index.md", fm(
        "Index", "Standards of proficiency for registered nurses",
        "The seven Future Nurse proficiency platforms (NMC, 2018) that every registered nurse must achieve at the point of registration.",
        PROF_TS, ["index", "platforms", "proficiency"],
        resource="https://www.nmc.org.uk/standards/standards-for-nurses/standards-of-proficiency-for-registered-nurses/") + f"""
# Standards of proficiency for registered nurses

The seven platforms (NMC, 2018):

{plat_links}

Plus **Annexe A** (communication and relationship management skills) and **Annexe B** (nursing procedures).

Achievement is supervised and assessed under the [SSSA](../sssa/index.md). Every platform enacts sections of [the Code](../code/index.md). Back to the [explorer root](../index.md).
""")

    for n in range(1, 8):
        stmts = parse_platform(n)
        write(CORPUS / "platforms" / f"platform-{n}.md", fm(
            "Proficiency platform", f"Platform {n}: {PLATFORM_TITLES[n]}",
            f"The {len(stmts)} proficiency statements of Future Nurse platform {n} — {PLATFORM_TITLES[n]}.",
            PROF_TS, ["platform", "proficiency"], aliases=f"platform {n}")
            + "\n" + platform_page(n, stmts))

    # SSSA
    write(CORPUS / "sssa" / "index.md", fm(
        "Index", "Standards for Student Supervision and Assessment (SSSA)",
        "The NMC framework (2018) defining practice supervisors, practice assessors and academic assessors, and the principles of student supervision.",
        SSSA_TS, ["index", "sssa", "education"],
        resource="https://www.nmc.org.uk/standards/standards-for-nurses/") + """
# Standards for Student Supervision and Assessment (SSSA)

The NMC framework (2018) for supervising and assessing students in practice.

## Roles
- [Practice supervisor](practice-supervisor.md)
- [Practice assessor](practice-assessor.md)
- [Academic assessor](academic-assessor.md)

## Principles
- [Key principles](key-principles.md) — supernumerary status, hub-and-spoke placements, raising concerns, reasonable adjustments, inter-professional learning

Students are assessed against the [proficiency platforms](../platforms/index.md). Back to the [explorer root](../index.md).
""")
    for slug, (title, desc, body) in SSSA_ROLES.items():
        write(CORPUS / "sssa" / f"{slug}.md",
              fm("SSSA role" if slug != "key-principles" else "SSSA principle",
                 title, desc, SSSA_TS, ["sssa"]) + "\n" + body + "\n")

    # Glossary
    term_links = "\n".join(f"- [{v[0]}]({k}.md) — {v[1]}" for k, v in GLOSSARY.items())
    write(CORPUS / "glossary" / "index.md", fm(
        "Index", "Glossary",
        "Key professional concepts used across the NMC standards.",
        GLOSS_TS, ["index", "glossary"]) + f"""
# Glossary

{term_links}

Back to the [explorer root](../index.md).
""")
    for slug, (title, definition, usage) in GLOSSARY.items():
        write(CORPUS / "glossary" / f"{slug}.md", fm(
            "Glossary term", title, definition, GLOSS_TS, ["glossary"],
            aliases=slug.replace("-", " ")) + f"""
# Definition
{definition}

# In the standards
{usage}
""")


# ---------- bundle builder (mirrors okf-explorer-bundle.v0) ----------

SECTION_ORDER = ["root", "code", "platforms", "sssa", "glossary"]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def route_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "index"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    m = FM_RE.match(text)
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip().strip('"')
        meta[key.strip()] = val
    return meta, text[m.end():].lstrip("\n")


def edge_kind(src: dict, tgt: dict) -> str:
    if tgt["section"] == "glossary" and tgt["type"] != "Index":
        return "defines term"
    if src["type"] == "Index":
        return "lists"
    if src["section"] == "platforms" and tgt["section"] == "code":
        return "maps to Code"
    if src["section"] == "code" and tgt["section"] == "platforms":
        return "assessed through"
    if src["section"] == tgt["section"]:
        return "related"
    return "links to"


def build_bundle() -> None:
    nodes: dict[str, dict] = {}
    bodies: dict[str, str] = {}
    for path in sorted(CORPUS.rglob("*.md")):
        pid = path.relative_to(CORPUS).as_posix()
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        section = pid.split("/", 1)[0] if "/" in pid else "root"
        aliases = {route_slug(Path(pid).with_suffix("").as_posix()),
                   pid.lower(), pid.removesuffix(".md").lower()}
        if "/" not in pid:
            aliases.add(route_slug(Path(pid).stem))
        if pid == "index.md":
            aliases.add("index")
        for alias in (meta.get("aliases") or "").split(";"):
            if alias.strip():
                aliases.add(route_slug(alias.strip()))
        nodes[pid] = {
            "id": pid,
            "type": meta.get("type", ""),
            "title": meta.get("title", pid),
            "description": meta.get("description", ""),
            "timestamp": meta.get("timestamp", ""),
            "resource": meta.get("resource", ""),
            "aliases": [a.strip() for a in (meta.get("aliases") or "").split(";") if a.strip()],
            "route_aliases": sorted(aliases),
            "section": section,
            "source": pid,
            "body": body,
        }
        bodies[pid] = body

    errors: list[str] = []
    edge_set: set[tuple[str, str]] = set()
    import os
    for pid, body in bodies.items():
        for m in LINK_RE.finditer(body):
            href = m.group(1).strip().split("#", 1)[0].split("?", 1)[0]
            if not href or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href):
                continue
            target = os.path.normpath((Path(pid).parent / href).as_posix()).replace("\\", "/")
            if target.endswith(".md"):
                if target in nodes:
                    edge_set.add((pid, target))
                else:
                    errors.append(f"{pid} -> missing {target}")
    if errors:
        raise SystemExit("Broken links:\n" + "\n".join(errors))

    edges = [{"source": s, "target": t,
              "kind": edge_kind(nodes[s], nodes[t]),
              "label": edge_kind(nodes[s], nodes[t])}
             for s, t in sorted(edge_set)]

    sections_present = sorted({n["section"] for n in nodes.values()})
    section_order = [s for s in SECTION_ORDER if s in sections_present]
    section_order += [s for s in sections_present if s not in section_order]
    timestamps = sorted(n["timestamp"] for n in nodes.values() if n["timestamp"])

    bundle = {
        "corpora": {
            "nmc-standards": {
                "id": "nmc-standards",
                "label": "NMC Standards",
                "title": "Open Nursing Knowledge Explorer",
                "subtitle": "The NMC Code, the Future Nurse proficiency platforms, and the SSSA as one cross-linked knowledge graph.",
                "root": "index.md",
                "source_root": ".",
                "markdown_url": "index.md",
                "sections": section_order,
                "nodes": nodes,
                "edges": edges,
                "relationships": edges,
            }
        },
        "generated_at": timestamps[-1] if timestamps else "",
        "generated_by": "build_nmc_bundle.py (Open Nursing Knowledge Explorer)",
        "kind": "okf-bundle",
        "meta": {
            "corpus_order": ["nmc-standards"],
            "default_corpus": "nmc-standards",
            "title": "Open Nursing Knowledge Explorer",
        },
        "okf_version": "0.1",
        "schema": "okf-explorer-bundle.v0",
    }
    BUNDLE_OUT.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    print(f"nodes={len(nodes)} edges={len(edges)} -> {BUNDLE_OUT}")


if __name__ == "__main__":
    import shutil
    if CORPUS.exists():
        shutil.rmtree(CORPUS)
    build_corpus()
    build_bundle()
