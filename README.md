# Open Nursing Knowledge Explorer

The NMC professional standards — **the Code** (25 sections, 4 themes), the seven
**Future Nurse proficiency platforms**, and the **SSSA** — presented as a single
cross-linked knowledge graph, browsable in the
[OKF Explorer](https://github.com/chris-page-gov/okf-explorer) (Svelte 5 static app).

An open resource from Nursing Citizen Development CIC. Content summarises public
NMC standards; always refer to [nmc.org.uk/standards](https://www.nmc.org.uk/standards/)
for the authoritative text.

## What's here

| Path | What it is |
|---|---|
| `_site/` | **The finished static site.** Serve this folder anywhere — no server code, no database. |
| `corpus/` | The generated markdown corpus (55 nodes: root, code/, platforms/, sssa/, glossary/) with YAML frontmatter and cross-links. |
| `okf-bundle.json` | The OKF bundle (schema `okf-explorer-bundle.v0`): 55 nodes, 251 typed edges (`maps to Code`, `assessed through`, `defines term`, `lists`, `related`). |
| `build_nmc_bundle.py` | Regenerates `corpus/` **and** `okf-bundle.json` from the NMC skill files in `~/.claude/skills/` (nmc-code, proficiency-rn-platform1..7, education-sssa). |

## Run locally

```sh
python3 -m http.server 4173 --directory _site
# open http://localhost:4173
```

Deep links work: `/#code/section-14.md`, `/?q=candour`, `/?view=graph`.

## Rebuild after editing content

1. Edit the source data in `build_nmc_bundle.py` (glossary, SSSA text, platform→Code
   mappings) or the parsed skill files, then:
   `python3 build_nmc_bundle.py && cp okf-bundle.json _site/`
2. The explorer app itself only needs rebuilding if you change the app. It comes from
   github.com/chris-page-gov/okf-explorer `apps/okf-explorer` with **one patch**:
   `DEFAULT_BUNDLE = './okf-bundle.json'` in `src/routes/+page.svelte` (was the
   author's remote demo bundle). Build with `pnpm install && pnpm build`, copy
   `build/` over `_site/` (keep `okf-bundle.json`, `okf-registry.json` and the
   corpus folders).

## Gotchas discovered while building

- The app reads edges from a **`relationships`** key on each corpus, not `edges`.
  The bundle emits both.
- Node `aliases` must be an **array of strings**. The upstream sample bundle uses a
  semicolon-joined string; feeding that to the app crashes search (`aliases.map` on
  a string) — any URL with `?q=` shows "No bundle loaded".
- Do **not** `git init` this folder on the backup drive: the drive is ExFAT and
  macOS AppleDouble `._*` files corrupt git packs. Keep the repo elsewhere (or on
  GitHub) and treat this folder as a working copy.

## Deployment options

The site is fully static (relative paths), so any of:
- **Azure Static Web Apps** (free tier on the startup subscription) — just point it at `_site/`
- **Hugging Face Spaces** (static SDK), next to the nursing AI toolkit
- **GitHub Pages**

## Licence / attribution

Explorer app: chris-page-gov/okf-explorer (see its LICENSE-CODE.md).
NMC standards content © Nursing and Midwifery Council; summarised here for
educational use with links to source documents.
