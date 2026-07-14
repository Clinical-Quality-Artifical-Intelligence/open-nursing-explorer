---
type: "Index"
title: "Open Nursing Knowledge Explorer"
description: "The NMC professional standards corpus — the Code, the Future Nurse proficiency platforms and annexes, and the SSSA — as a cross-linked open knowledge bundle."
tags: [index, root, nmc, nursing, okf]
timestamp: 2026-07-14T00:00:00Z
resource: "https://www.nmc.org.uk/standards/"
---

# Open Nursing Knowledge Explorer

The professional standards that govern UK nursing, published by the Nursing and Midwifery Council (NMC), presented as a single cross-linked knowledge graph.

## Contents
- **[The Code](code/index.md)** — 25 professional standards across 4 themes (2015, updated 2018)
- **[Proficiency platforms](platforms/index.md)** — the 7 Future Nurse platforms, plus [Annexe A](annexes/annexe-a.md) (communication skills) and [Annexe B](annexes/annexe-b.md) (nursing procedures)
- **[Student supervision and assessment](sssa/index.md)** — the SSSA roles and principles (2018)
- **[Glossary](glossary/index.md)** — key professional concepts

## How the pieces fit
Every **proficiency platform** cross-references the **Code** sections it shares wording with; the **SSSA** defines who supervises and assesses achievement of the platforms; the **annexes** are the specific skills and procedures a platform requires; the **glossary** anchors shared concepts. Use the graph view to see the whole web.

## How the Code cross-reference works
The links between proficiency statements and Code sections on this site are **not an official NMC crosswalk** — none is published. They are computed by matching disclosed keyword and phrase evidence between the text of each proficiency statement and the text of each Code section (see `CODE_KEYWORDS` in [`build_nmc_bundle.py`](https://github.com/Clinical-Quality-Artifical-Intelligence/open-nursing-explorer/blob/main/build_nmc_bundle.py)). Every cross-reference shown quotes the specific statement number and the matched phrase, so you can check the reasoning yourself rather than take it on trust.

## Credits and original idea
This site is built on the [OKF Explorer](https://github.com/chris-page-gov/okf-explorer), an open-source knowledge-bundle viewer created by **Chris Page** ([@chris-page-gov](https://github.com/chris-page-gov)) — the Open Knowledge Format and the Svelte app that renders this graph are his design and engineering, used here under the project's MIT licence. This bundle — the NMC content, the corpus structure, and the Code cross-reference methodology — was built by Nursing Citizen Development CIC as an application of that idea to UK nursing regulation.

## Keeping this current
The Code and the Future Nurse standards are periodically reviewed by the NMC. This repository will be updated whenever the NMC publishes a revised Code or revalidation requirements, or revises the proficiency standards — the corpus is generated from a build script, so a re-run against updated source text produces a new release. Check the [repository](https://github.com/Clinical-Quality-Artifical-Intelligence/open-nursing-explorer) for the latest version and its build date.

*An open resource from Nursing Citizen Development CIC. Content summarises public NMC standards — always refer to [nmc.org.uk/standards](https://www.nmc.org.uk/standards/) for the authoritative text.*
