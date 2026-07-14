#!/usr/bin/env python3
"""Build the Open Nursing Knowledge Explorer OKF bundle.

Parses the local NMC skill files (the Code, RN proficiency platforms 1-7,
SSSA) into a cross-linked markdown corpus, adds Annexe A and Annexe B
(transcribed verbatim from the NMC's published PDF), computes a
transparent, text-derived cross-reference between proficiency statements
and Code sections, then emits an okf-explorer-bundle.v0 JSON bundle
consumable by the OKF Explorer app.

Sources: NMC Code (2015, updated 2018); Standards of Proficiency for
Registered Nurses ("Future Nurse", 2018), including Annexe A and Annexe B;
Standards for Student Supervision and Assessment (2018). All public NMC
standards, nmc.org.uk.

Code <-> proficiency cross-references are NOT an official NMC crosswalk.
They are computed by matching disclosed keyword/phrase evidence between
proficiency statement text and Code section text (see CODE_KEYWORDS below)
and are labelled "textual cross-reference" throughout, with the matched
statement and phrase shown so the reasoning is auditable, not asserted.
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

# Disclosed keyword evidence used to compute Code <-> proficiency
# cross-references. Each phrase is drawn from the actual wording of the
# named Code section. A hit means the proficiency statement's text shares
# that wording with the Code section — it is textual evidence, not a claim
# of official equivalence. See build_code_matches() and the module docstring.
CODE_KEYWORDS: dict[int, list[str]] = {
    1: ["individual choice", "dignity", "human rights"],
    2: ["preferences and concerns", "shared decision", "anxious or in distress", "listen to"],
    3: ["psychological needs", "physical, social and psychological", "life stages",
        "last few days and hours of life"],
    4: ["best interests", "informed consent", "consent", "mental capacity",
        "conscientious objection"],
    5: ["privacy and confidentiality", "confidential", "right to privacy"],
    6: ["evidence-based", "evidence base", "best available evidence"],
    7: ["communicate clearly", "language and communication needs",
        "verbal and non-verbal communication", "communication skills"],
    8: ["work cooperatively", "cooperatively", "preserve the safety"],
    9: ["share your skills", "support students", "constructive feedback"],
    10: ["accurate records", "clear and accurate records", "record keeping",
         "record-keeping", "records"],
    11: ["delegate", "delegating", "delegation", "scope of competence"],
    12: ["indemnity"],
    13: ["limits of your competence", "limits of competence", "suitably qualified",
         "refer"],
    14: ["open and candid", "candour", "apologise", "put right the situation",
         "breaking bad news"],
    15: ["emergency"],
    16: ["risk to patient safety", "raise and escalate", "escalate concerns",
         "public protection", "escalation"],
    17: ["vulnerable", "at risk of harm", "safeguarding", "abuse"],
    18: ["prescribe", "administer medicines", "administration of medicines",
         "dispense", "controlled drugs", "medicines"],
    19: ["potential for harm", "infection prevention and control",
         "infection prevention", "near misses", "human factors"],
    20: ["reputation of your profession", "role model", "discrimination",
         "social media"],
    21: ["position as a registered nurse", "financial dealings"],
    22: ["registration requirements", "continuing professional development", "cpd"],
    23: ["investigations and audits", "audit", "caution or charge"],
    24: ["complaint", "complaints"],
    25: ["leadership", "manage time, staff and resources", "wellbeing is protected"],
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

# ---------- Annexe A: Communication and relationship management skills ----------
# Transcribed verbatim from the NMC's published PDF ("Future nurse: Standards of
# proficiency for registered nurses"), Annexe A, sections 1-4.
ANNEXE_A_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    ("1. Underpinning communication skills for assessing, planning, providing and managing best practice, evidence-based nursing care", [
        ("1.1", "actively listen, recognise and respond to verbal and non-verbal cues"),
        ("1.2", "use prompts and positive verbal and non-verbal reinforcement"),
        ("1.3", "use appropriate non-verbal communication including touch, eye contact and personal space"),
        ("1.4", "make appropriate use of open and closed questioning"),
        ("1.5", "use caring conversation techniques"),
        ("1.6", "check understanding and use clarification techniques"),
        ("1.7", "be aware of own unconscious bias in communication encounters"),
        ("1.8", "write accurate, clear, legible records and documentation"),
        ("1.9", "confidently and clearly present and share verbal and written reports with individuals and groups"),
        ("1.10", "analyse and clearly record and share digital information and data"),
        ("1.11", "provide clear verbal, digital or written information and instructions when delegating or handing over responsibility for care"),
        ("1.12", "recognise the need for, and facilitate access to, translator services and material"),
    ]),
    ("2. Evidence-based, best practice approaches to communication for supporting people of all ages, their families and carers in preventing ill health and in managing their care", [
        ("2.1", "share information and check understanding about the causes, implications and treatment of a range of common health conditions including anxiety, depression, memory loss, diabetes, dementia, respiratory disease, cardiac disease, neurological disease, cancer, skin problems, immune deficiencies, psychosis, stroke and arthritis"),
        ("2.2", "use clear language and appropriate, written materials, making reasonable adjustments where appropriate in order to optimise people's understanding of what has caused their health condition and the implications of their care and treatment"),
        ("2.3", "recognise and accommodate sensory impairments during all communications"),
        ("2.4", "support and manage the use of personal communication aids"),
        ("2.5", "identify the need for and manage a range of alternative communication techniques"),
        ("2.6", "use repetition and positive reinforcement strategies"),
        ("2.7", "assess motivation and capacity for behaviour change and clearly explain cause and effect relationships related to common health risk behaviours including smoking, obesity, sexual practice, alcohol and substance use"),
        ("2.8", "provide information and explanation to people, families and carers and respond to questions about their treatment and care and possible ways of preventing ill health to enhance understanding"),
        ("2.9", "engage in difficult conversations, including breaking bad news and support people who are feeling emotionally or physically vulnerable or in distress, conveying compassion and sensitivity"),
    ]),
    ("3. Evidence-based, best practice communication skills and approaches for providing therapeutic interventions", [
        ("3.1", "motivational interview techniques"),
        ("3.2", "solution focused therapies"),
        ("3.3", "reminiscence therapies"),
        ("3.4", "talking therapies"),
        ("3.5", "de-escalation strategies and techniques"),
        ("3.6", "cognitive behavioural therapy techniques"),
        ("3.7", "play therapy"),
        ("3.8", "distraction and diversion strategies"),
        ("3.9", "positive behaviour support approaches"),
    ]),
    ("4. Evidence-based, best practice communication skills and approaches for working with people in professional teams", [
        ("4.1", "Demonstrate effective supervision, teaching and performance appraisal through the use of: clear instructions and explanations when supervising, teaching or appraising others (4.1.1); clear instructions and check understanding when delegating care responsibilities to others (4.1.2); unambiguous, constructive feedback about strengths and weaknesses and potential for improvement (4.1.3); encouragement to colleagues that helps them to reflect on their practice (4.1.4); unambiguous records of performance (4.1.5)"),
        ("4.2", "Demonstrate effective person and team management through the use of: strengths based approaches to developing teams and managing change (4.2.1); active listening when dealing with team members' concerns and anxieties (4.2.2); a calm presence when dealing with conflict (4.2.3); appropriate and effective confrontation strategies (4.2.4); de-escalation strategies and techniques when dealing with conflict (4.2.5); effective co-ordination and navigation skills through appropriate negotiation strategies, appropriate escalation procedures and appropriate approaches to advocacy (4.2.6)"),
    ]),
]

# ---------- Annexe B: Nursing procedures ----------
# Transcribed verbatim from the NMC's published PDF, Annexe B, Part 1 (sections
# 1-2) and Part 2 (sections 3-11).
ANNEXE_B_PARTS: list[tuple[str, list[tuple[str, list[tuple[str, str]]]]]] = [
    ("Part 1: Procedures for assessing people's needs for person-centred care", [
        ("1. Use evidence-based, best practice approaches to take a history, observe, recognise and accurately assess people of all ages", [
            ("1.1", "mental health and wellbeing status, including: signs of mental and emotional distress or vulnerability (1.1.1); cognitive health status and wellbeing (1.1.2); signs of cognitive distress and impairment (1.1.3); behavioural distress based needs (1.1.4); signs of mental and emotional distress including agitation, aggression and challenging behaviour (1.1.5); signs of self-harm and/or suicidal ideation (1.1.6)"),
            ("1.2", "physical health and wellbeing, including: symptoms and signs of physical ill health (1.2.1); symptoms and signs of physical distress (1.2.2); symptoms and signs of deterioration and sepsis (1.2.3)"),
        ]),
        ("2. Use evidence-based, best practice approaches to undertake the following procedures", [
            ("2.1", "take, record and interpret vital signs manually and via technological devices"),
            ("2.2", "undertake venepuncture and cannulation and blood sampling, interpreting normal and common abnormal blood profiles and venous blood gases"),
            ("2.3", "set up and manage routine electrocardiogram (ECG) investigations and interpret normal and commonly encountered abnormal traces"),
            ("2.4", "manage and monitor blood component transfusions"),
            ("2.5", "manage and interpret cardiac monitors, infusion pumps, blood glucose monitors and other monitoring devices"),
            ("2.6", "accurately measure weight and height, calculate body mass index and recognise healthy ranges and clinically significant low/high readings"),
            ("2.7", "undertake a whole body systems assessment including respiratory, circulatory, neurological, musculoskeletal, cardiovascular and skin status"),
            ("2.8", "undertake chest auscultation and interpret findings"),
            ("2.9", "collect and observe sputum, urine, stool and vomit specimens, undertaking routine analysis and interpreting findings"),
            ("2.10", "measure and interpret blood glucose levels"),
            ("2.11", "recognise and respond to signs of all forms of abuse"),
            ("2.12", "undertake, respond to and interpret neurological observations and assessments"),
            ("2.13", "identify and respond to signs of deterioration and sepsis"),
            ("2.14", "administer basic mental health first aid"),
            ("2.15", "administer basic physical first aid"),
            ("2.16", "recognise and manage seizures, choking and anaphylaxis, providing appropriate basic life support"),
            ("2.17", "recognise and respond to challenging behaviour, providing appropriate safe holding and restraint"),
        ]),
    ]),
    ("Part 2: Procedures for the planning, provision and management of person-centred nursing care", [
        ("3. Use evidence-based, best practice approaches for meeting needs for care and support with rest, sleep, comfort and the maintenance of dignity", [
            ("3.1", "observe and assess comfort and pain levels and rest and sleep patterns"),
            ("3.2", "use appropriate bed-making techniques including those required for people who are unconscious or who have limited mobility"),
            ("3.3", "use appropriate positioning and pressure-relieving techniques"),
            ("3.4", "take appropriate action to ensure privacy and dignity at all times"),
            ("3.5", "take appropriate action to reduce or minimise pain or discomfort"),
            ("3.6", "take appropriate action to reduce fatigue, minimise insomnia and support improved rest and sleep hygiene"),
        ]),
        ("4. Use evidence-based, best practice approaches for meeting the needs for care and support with hygiene and the maintenance of skin integrity", [
            ("4.1", "observe, assess and optimise skin and hygiene status and determine the need for support and intervention"),
            ("4.2", "use contemporary approaches to the assessment of skin integrity and use appropriate products to prevent or manage skin breakdown"),
            ("4.3", "assess needs for and provide appropriate assistance with washing, bathing, shaving and dressing"),
            ("4.4", "identify and manage skin irritations and rashes"),
            ("4.5", "assess needs for and provide appropriate oral, dental, eye and nail care and decide when an onward referral is needed"),
            ("4.6", "use aseptic techniques when undertaking wound care including dressings, pressure bandaging, suture removal, and vacuum closures"),
            ("4.7", "use aseptic techniques when managing wound and drainage processes"),
            ("4.8", "assess, respond and effectively manage pyrexia and hypothermia"),
        ]),
        ("5. Use evidence-based, best practice approaches for meeting the needs for care and support with nutrition and hydration", [
            ("5.1", "observe, assess and optimise nutrition and hydration status and determine the need for intervention and support"),
            ("5.2", "use contemporary nutritional assessment tools"),
            ("5.3", "assist with feeding and drinking and use appropriate feeding and drinking aids"),
            ("5.4", "record fluid intake and output and identify, respond to and manage dehydration or fluid retention"),
            ("5.5", "identify, respond to and manage nausea and vomiting"),
            ("5.6", "insert, manage and remove oral/nasal/gastric tubes"),
            ("5.7", "manage artificial nutrition and hydration using oral, enteral and parenteral routes"),
            ("5.8", "manage the administration of IV fluids"),
            ("5.9", "manage fluid and nutritional infusion pumps and devices"),
        ]),
        ("6. Use evidence-based, best practice approaches for meeting needs for care and support with bladder and bowel health", [
            ("6.1", "observe and assess level of urinary and bowel continence to determine the need for support and intervention assisting with toileting, maintaining dignity and privacy and managing the use of appropriate aids"),
            ("6.2", "select and use appropriate continence products; insert, manage and remove catheters for all genders; and assist with self-catheterisation when required"),
            ("6.3", "manage bladder drainage"),
            ("6.4", "assess bladder and bowel patterns to identify and respond to constipation, diarrhoea and urinary and faecal retention"),
            ("6.5", "administer enemas and suppositories and undertake rectal examination and manual evacuation when appropriate"),
            ("6.6", "undertake stoma care identifying and using appropriate products and approaches"),
        ]),
        ("7. Use evidence-based, best practice approaches for meeting needs for care and support with mobility and safety", [
            ("7.1", "observe and use evidence-based risk assessment tools to determine need for support and intervention to optimise mobility and safety, and to identify and manage risk of falls using best practice risk assessment approaches"),
            ("7.2", "use a range of contemporary moving and handling techniques and mobility aids"),
            ("7.3", "use appropriate moving and handling equipment to support people with impaired mobility"),
            ("7.4", "use appropriate safety techniques and devices"),
        ]),
        ("8. Use evidence-based, best practice approaches for meeting needs for respiratory care and support", [
            ("8.1", "observe and assess the need for intervention and respond to restlessness, agitation and breathlessness using appropriate interventions"),
            ("8.2", "manage the administration of oxygen using a range of routes and best practice approaches"),
            ("8.3", "take and interpret peak flow and oximetry measurements"),
            ("8.4", "use appropriate nasal and oral suctioning techniques"),
            ("8.5", "manage inhalation, humidifier and nebuliser devices"),
            ("8.6", "manage airway and respiratory processes and equipment"),
        ]),
        ("9. Use evidence-based, best practice approaches for meeting needs for care and support with the prevention and management of infection", [
            ("9.1", "observe, assess and respond rapidly to potential infection risks using best practice guidelines"),
            ("9.2", "use standard precautions protocols"),
            ("9.3", "use effective aseptic, non-touch techniques"),
            ("9.4", "use appropriate personal protection equipment"),
            ("9.5", "implement isolation procedures"),
            ("9.6", "use evidence-based hand hygiene techniques"),
            ("9.7", "safely decontaminate equipment and environment"),
            ("9.8", "safely use and dispose of waste, laundry and sharps"),
            ("9.9", "safely assess and manage invasive medical devices and lines"),
        ]),
        ("10. Use evidence-based, best practice approaches for meeting needs for care and support at the end of life", [
            ("10.1", "observe, and assess the need for intervention for people, families and carers, identify, assess and respond appropriately to uncontrolled symptoms and signs of distress including pain, nausea, thirst, constipation, restlessness, agitation, anxiety and depression"),
            ("10.2", "manage and monitor effectiveness of symptom relief medication, infusion pumps and other devices"),
            ("10.3", "assess and review preferences and care priorities of the dying person and their family and carers"),
            ("10.4", "understand and apply organ and tissue donation protocols, advanced planning decisions, living wills and health and lasting powers of attorney for health"),
            ("10.5", "understand and apply DNACPR (do not attempt cardiopulmonary resuscitation) decisions and verification of expected death"),
            ("10.6", "provide care for the deceased person and the bereaved respecting cultural requirements and protocols"),
        ]),
        ("11. Procedural competencies required for best practice, evidence-based medicines administration and optimisation", [
            ("11.1", "carry out initial and continued assessments of people receiving care and their ability to self-administer their own medications"),
            ("11.2", "recognise the various procedural routes under which medicines can be prescribed, supplied, dispensed and administered; and the laws, policies, regulations and guidance that underpin them"),
            ("11.3", "use the principles of safe remote prescribing and directions to administer medicines"),
            ("11.4", "undertake accurate drug calculations for a range of medications"),
            ("11.5", "undertake accurate checks, including transcription and titration, of any direction to supply or administer a medicinal product"),
            ("11.6", "exercise professional accountability in ensuring the safe administration of medicines to those receiving care"),
            ("11.7", "administer injections using intramuscular, subcutaneous, intradermal and intravenous routes and manage injection equipment"),
            ("11.8", "administer medications using a range of routes"),
            ("11.9", "administer and monitor medications using vascular access devices and enteral equipment"),
            ("11.10", "recognise and respond to adverse or abnormal reactions to medications"),
            ("11.11", "undertake safe storage, transportation and disposal of medicinal products"),
        ]),
    ]),
]


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


def build_code_matches(
    all_statements: dict[int, list[tuple[str, str]]],
    sections: dict[int, tuple[str, int, list[tuple[str, str]]]],
) -> tuple[dict[int, list[tuple[int, str, str]]], dict[int, list[tuple[str, str, str]]]]:
    """Compute textual cross-references between proficiency statements and Code
    sections using CODE_KEYWORDS. Matches both against the Code section title
    and its individual clauses.

    Returns (platform_to_code, code_to_platform):
      platform_to_code[platform_num] = [(code_section, statement_num, matched_phrase), ...]
      code_to_platform[code_section] = [(platform_and_statement, matched_phrase, statement_text), ...]
    """
    platform_to_code: dict[int, list[tuple[int, str, str]]] = {n: [] for n in all_statements}
    code_to_platform: dict[int, list[tuple[str, str, str]]] = {s: [] for s in sections}
    for n, stmts in all_statements.items():
        for stmt_num, stmt_text in stmts:
            low = stmt_text.lower()
            for section_num, phrases in CODE_KEYWORDS.items():
                for phrase in phrases:
                    # \b word-boundary match: a plain substring check would let
                    # "refer" match inside "preferences", "risk" inside
                    # "at risk of harm" is fine but single short words need
                    # boundaries to avoid false hits like that.
                    if re.search(r"\b" + re.escape(phrase) + r"\b", low):
                        platform_to_code[n].append((section_num, stmt_num, phrase))
                        code_to_platform[section_num].append((stmt_num, phrase, stmt_text))
                        break  # one match per section per statement is enough evidence
    return platform_to_code, code_to_platform


def code_section_page(num: int, title: str, theme_num: int, theme_title: str,
                      clauses: list[tuple[str, str]],
                      code_to_platform: dict[int, list[tuple[str, str, str]]]) -> str:
    slug = THEME_SLUGS[theme_num]
    body = [f"# {num}. {title}\n",
            f"Theme: [{theme_title}](theme-{theme_num}-{slug}.md)\n",
            "## To achieve this, you must:\n"]
    body += [f"- **{cn}** {ct}" for cn, ct in clauses]
    matches = code_to_platform.get(num, [])
    if matches:
        by_platform: dict[int, list[tuple[str, str]]] = {}
        for stmt_num, phrase, _text in matches:
            p = int(stmt_num.split(".")[0])
            by_platform.setdefault(p, []).append((stmt_num, phrase))
        body.append(
            "\n## Textual cross-references (proficiency statements)\n"
            "Not an official NMC crosswalk — computed by matching shared wording "
            "between this Code section and proficiency statement text. See "
            "[methodology](../index.md#how-the-code-crossreference-works)."
        )
        for p in sorted(by_platform):
            hits = ", ".join(f"**{sn}** (\"{ph}\")" for sn, ph in sorted(set(by_platform[p])))
            body.append(f"- [Platform {p}: {PLATFORM_TITLES[p]}](../platforms/platform-{p}.md) — {hits}")
    terms = SECTION_TO_GLOSSARY.get(num, [])
    if terms:
        body.append("\n## Key concepts")
        body += [f"- [{GLOSSARY[t][0]}](../glossary/{t}.md)" for t in terms]
    return "\n".join(body) + "\n"


def platform_page(n: int, stmts: list[tuple[str, str]],
                   platform_to_code: dict[int, list[tuple[int, str, str]]]) -> str:
    body = [f"# Platform {n}: {PLATFORM_TITLES[n]}\n",
            "At the point of registration, the registered nurse will be able to:\n"]
    body += [f"- **{num}** {text}" for num, text in stmts]
    matches = platform_to_code.get(n, [])
    if matches:
        by_section: dict[int, list[tuple[str, str]]] = {}
        for section_num, stmt_num, phrase in matches:
            by_section.setdefault(section_num, []).append((stmt_num, phrase))
        body.append(
            "\n## Textual cross-references (Code sections)\n"
            "Not an official NMC crosswalk — computed by matching shared wording "
            "between proficiency statement text and Code section text. See "
            "[methodology](../index.md#how-the-code-crossreference-works)."
        )
        for s in sorted(by_section):
            hits = ", ".join(f"**{sn}** (\"{ph}\")" for sn, ph in sorted(set(by_section[s])))
            body.append(f"- [Code section {s}](../code/section-{s:02d}.md) — {hits}")
    body.append("\n## Skills required")
    body.append("Demonstrated through [Annexe A](../annexes/annexe-a.md) (communication and relationship management skills) and [Annexe B](../annexes/annexe-b.md) (nursing procedures) — see proficiency 1.20.")
    body.append("\n## Assessment")
    body.append("Achievement is assessed in practice under the [Standards for Student Supervision and Assessment](../sssa/index.md).")
    return "\n".join(body) + "\n"


def annexe_a_page() -> str:
    body = ["# Annexe A: Communication and relationship management skills\n",
            "At the point of registration, the registered nurse will be able to safely "
            "demonstrate the following skills, required to meet the proficiency outcomes "
            "of [Platform 1, proficiency 1.20](../platforms/platform-1.md).\n"]
    for heading, items in ANNEXE_A_SECTIONS:
        body.append(f"\n## {heading}\n")
        body += [f"- **{num}** {text}" for num, text in items]
    body.append(
        "\n## Related Code sections\n"
        "Editorial cross-references, quoting the specific item and Code wording "
        "it echoes — not an official crosswalk:\n"
        "- **1.8** \"write accurate, clear, legible records\" → "
        "[Code section 10](../code/section-10.md) (accurate records)\n"
        "- **2.9** \"engage in difficult conversations, including breaking bad "
        "news\" → [Code section 14](../code/section-14.md) (candour)\n"
        "- **1.12** \"facilitate access to translator services\" → "
        "[Code section 7](../code/section-07.md) (communicate clearly)\n"
        "- **4.1.2** \"clear instructions... when delegating care responsibilities\" → "
        "[Code section 11](../code/section-11.md) (delegation)"
    )
    body.append("\nBack to [proficiency platforms](../platforms/index.md).")
    return "\n".join(body) + "\n"


def annexe_b_page() -> str:
    body = ["# Annexe B: Nursing procedures\n",
            "At the point of registration, the registered nurse will be able to safely "
            "demonstrate the following procedures, required to meet the proficiency "
            "outcomes of [Platform 1, proficiency 1.20](../platforms/platform-1.md) and "
            "[Platform 4](../platforms/platform-4.md).\n"]
    for part_heading, groups in ANNEXE_B_PARTS:
        body.append(f"\n## {part_heading}\n")
        for group_heading, items in groups:
            body.append(f"\n### {group_heading}\n")
            body += [f"- **{num}** {text}" for num, text in items]
    body.append(
        "\n## Related Code sections\n"
        "Editorial cross-references, quoting the specific item and Code wording "
        "it echoes — not an official crosswalk:\n"
        "- **2.11** \"recognise and respond to signs of all forms of abuse\" → "
        "[Code section 17](../code/section-17.md) (vulnerable people, safeguarding)\n"
        "- **9.1–9.9** infection prevention and control procedures → "
        "[Code section 19](../code/section-19.md) (infection prevention and control)\n"
        "- **11.6** \"exercise professional accountability in ensuring the safe "
        "administration of medicines\" → [Code section 18](../code/section-18.md) "
        "(administer medicines within the limits of your training)\n"
        "- **3.4** \"take appropriate action to ensure privacy and dignity at all "
        "times\" → [Code section 1](../code/section-01.md) / "
        "[Code section 5](../code/section-05.md)"
    )
    body.append("\nBack to [proficiency platforms](../platforms/index.md).")
    return "\n".join(body) + "\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_corpus() -> None:
    themes, sections = parse_code()
    all_statements = {n: parse_platform(n) for n in range(1, 8)}
    platform_to_code, code_to_platform = build_code_matches(all_statements, sections)

    # Root index
    write(CORPUS / "index.md", fm(
        "Index", "Open Nursing Knowledge Explorer",
        "The NMC professional standards corpus — the Code, the Future Nurse proficiency platforms and annexes, and the SSSA — as a cross-linked open knowledge bundle.",
        GLOSS_TS, ["index", "root", "nmc", "nursing", "okf"],
        resource="https://www.nmc.org.uk/standards/") + """
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
            + "\n" + code_section_page(sn, st, stn, tt, clauses, code_to_platform))

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

Plus **[Annexe A](../annexes/annexe-a.md)** (communication and relationship management skills) and **[Annexe B](../annexes/annexe-b.md)** (nursing procedures).

Achievement is supervised and assessed under the [SSSA](../sssa/index.md). Every platform cross-references sections of [the Code](../code/index.md) — see the [methodology](../index.md#how-the-code-crossreference-works). Back to the [explorer root](../index.md).
""")

    for n in range(1, 8):
        stmts = all_statements[n]
        write(CORPUS / "platforms" / f"platform-{n}.md", fm(
            "Proficiency platform", f"Platform {n}: {PLATFORM_TITLES[n]}",
            f"The {len(stmts)} proficiency statements of Future Nurse platform {n} — {PLATFORM_TITLES[n]}.",
            PROF_TS, ["platform", "proficiency"], aliases=f"platform {n}")
            + "\n" + platform_page(n, stmts, platform_to_code))

    # Annexes
    write(CORPUS / "annexes" / "index.md", fm(
        "Index", "Annexes A and B",
        "The skills (Annexe A) and procedures (Annexe B) a newly registered nurse must demonstrate, referenced by proficiency 1.20.",
        PROF_TS, ["index", "annexes", "proficiency"],
        resource="https://www.nmc.org.uk/standards/standards-for-nurses/standards-of-proficiency-for-registered-nurses/") + """
# Annexes A and B

Two annexes to the [proficiency platforms](../platforms/index.md), referenced directly by proficiency 1.20 ("Safely demonstrate evidence-based practice in all skills and procedures in Annexes A and B"):

- **[Annexe A: Communication and relationship management skills](annexe-a.md)** — 4 sections, from underpinning communication skills through to team leadership communication
- **[Annexe B: Nursing procedures](annexe-b.md)** — 2 parts (assessment procedures; planning, provision and management procedures), 11 procedure groups

Back to the [explorer root](../index.md).
""")
    write(CORPUS / "annexes" / "annexe-a.md", fm(
        "Annexe", "Annexe A: Communication and relationship management skills",
        "The communication and relationship management skills a newly registered nurse must demonstrate, in 4 sections.",
        PROF_TS, ["annexe", "communication"], aliases="annexe a; annex a")
        + "\n" + annexe_a_page())
    write(CORPUS / "annexes" / "annexe-b.md", fm(
        "Annexe", "Annexe B: Nursing procedures",
        "The nursing procedures a newly registered nurse must demonstrate, in 2 parts covering assessment and care management.",
        PROF_TS, ["annexe", "procedures"], aliases="annexe b; annex b")
        + "\n" + annexe_b_page())

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

SECTION_ORDER = ["root", "code", "platforms", "annexes", "sssa", "glossary"]
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
        return "textual cross-reference"
    if src["section"] == "code" and tgt["section"] == "platforms":
        return "textual cross-reference"
    if src["section"] == "platforms" and tgt["section"] == "annexes":
        return "requires skills in"
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
                "subtitle": "The NMC Code, the Future Nurse proficiency platforms and annexes, and the SSSA as one cross-linked knowledge graph.",
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
