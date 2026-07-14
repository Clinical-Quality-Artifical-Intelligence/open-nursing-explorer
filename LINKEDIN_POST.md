# LinkedIn post draft — Open Nursing Knowledge Explorer (v2)

*(Attach the graph-view screenshot. Trim the "Why now" section first if you
need to shorten for LinkedIn.)*

---

Every three years, every nurse, midwife and nursing associate in the UK sits
down and asks: *have I actually practised in line with the Code?*

Revalidation isn't a box-ticking exercise — it's how 750,000+ registrants
continuously prove they're safe to practise. But ask any student or newly
qualified nurse where "the Code" actually lives day to day, and you'll get a
shrug. It's a PDF. The seven proficiency platforms you were assessed against
on placement are a different PDF. The supervision framework that governed
who signed you off is a third. Three documents, no visible links between
them.

So I built the connective tissue: **Open Nursing Knowledge Explorer** —
the NMC Code (25 sections, 4 themes), all seven Future Nurse proficiency
platforms plus Annexe A (communication skills) and Annexe B (nursing
procedures), and the Standards for Student Supervision and Assessment
(SSSA), as one searchable, cross-linked knowledge graph.

**Credit where it's due:** this is built entirely on top of the
[OKF Explorer](https://github.com/chris-page-gov/okf-explorer), an
open-source knowledge-bundle viewer created by Chris Page. The format and
the app are his idea and his engineering. What I've added is the NMC
content — and, because I didn't want to just assert connections between the
Code and the proficiencies (no official NMC crosswalk exists), I built the
cross-referencing to be **auditable**: every link between a proficiency
statement and a Code section quotes the specific wording they share, so
you can check my working rather than take it on trust.

**Why now:** NHS England's 10 Year Health Plan commits to three shifts —
hospital to community, analogue to digital, sickness to prevention — and
names a specific role for AI in delivering them, including ambient AI
scribing and clinician-support tools. Every nursing AI tool riding that
shift (documentation copilots, reflective-account assistants, standards
Q&A) is only as good as its underlying knowledge structure. Feed an AI
three disconnected PDFs and it guesses at the connections between them.
Feed it an open, structured, linked dataset and it doesn't have to. This is
that structured layer, built as open infrastructure rather than a walled
product.

**What it's for:**
- Students building portfolio evidence — see exactly which Code clauses a
  proficiency statement echoes, in one click
- Practice supervisors and assessors — navigate the SSSA roles and what
  each is accountable for
- Preceptorship and revalidation — trace a reflective account back to the
  Code theme it demonstrates
- Educators and curriculum designers — the whole standards landscape as one
  graph, not four PDFs
- Anyone building nursing AI tools — an open, machine-readable knowledge
  base to ground answers in, instead of hallucinated citations

Fully open source, self-hosted as a static site (no database, no backend,
no lock-in), free to fork — and it stays live: I'll update it whenever the
NMC revises the Code, revalidation requirements or the proficiency
standards, since the whole thing is generated from a build script rather
than hand-written.

🔗 Live: https://clinical-quality-artifical-intelligence.github.io/open-nursing-explorer/
🔗 Code: https://github.com/Clinical-Quality-Artifical-Intelligence/open-nursing-explorer
🔗 Built on: https://github.com/chris-page-gov/okf-explorer

This is what I mean by **Nursing Citizen Development** — nurses building
the digital infrastructure of their own profession, in the open, instead of
waiting for it to be built for them. If the NHS is serious about the
digital shift, the standards that govern our practice should be as open
and machine-readable as the tools being built on top of them.

#NursingInnovation #DigitalNursing #NMC #NursingCitizenDevelopment #OpenData
#Revalidation #NursingEducation #HealthTech #AIinNursing #10YearHealthPlan

---

## Notes for you before posting

- **"750,000+ registrants"** is close to the current NMC register size but I
  haven't pulled today's exact figure from the NMC register report — check
  before publishing under the CIC's name, or soften to "hundreds of
  thousands."
- The **Code↔proficiency cross-references are computed by keyword matching**,
  disclosed and auditable in the repo, but still an editorial method, not an
  NMC-endorsed crosswalk — the post says this plainly; keep that framing if
  you trim the post, don't let it read as "the NMC's official mapping."
- The **10 Year Health Plan / ambient AI scribing** claims are sourced from
  NHS England's July 2025 "Fit for the Future" plan and RCN/King's Fund
  coverage of it — solid grounding, but it's worth a skim of
  [gov.uk's summary](https://www.gov.uk/government/publications/10-year-health-plan-for-england-fit-for-the-future)
  yourself before quoting it, since health policy commitments shift.
- Consider whether `Clinical-Quality-Artifical-Intelligence` (note: the org
  name has a typo, "Artifical") is the identity you want visible in the
  live URL for a Nursing Citizen Development-branded launch post — happy to
  rename or move the repo if you'd rather the URL match the brand cleanly.
