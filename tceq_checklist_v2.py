"""
TCEQ OSSF Surface Spray Inspection Checklist — Streamlit App v2
----------------------------------------------------------------
HOW TO RUN:
  1. pip install streamlit anthropic pandas
  2. export ANTHROPIC_API_KEY=your_key_here
  3. streamlit run tceq_checklist.py

ARCHITECTURE:
  - Inspector sets Region + Business Type (anchors the NOV dataset context)
  - Works through real OSSF checklist items, marking Pass / Fail / N/A
  - On any Fail: AI returns suggested TAC citations + reasoning grounded
    in NOV dataset patterns and TAC 30 Chapter 285 rules
  - Inspector accepts suggestions selectively or all at once
  - Inspector can also add codes manually
  - Accepted violations accumulate for downstream report generation

INTEGRATION POINTS (marked TODO):
  - get_nov_context(): replace with your NOV co-occurrence lookup
  - get_tac_text(): replace with your vector DB / citation JSON lookup
  - The Anthropic API call uses both as context — swap placeholders in
"""

import streamlit as st
import anthropic

st.set_page_config(
    page_title="TCEQ OSSF Inspection Checklist",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.block-container{padding-top:1.25rem;padding-bottom:1rem}
.section-label{font-size:0.68rem;font-weight:600;text-transform:uppercase;
    letter-spacing:0.08em;color:#888;margin:1rem 0 0.25rem}
.fail-item{background:#fff0f0;border-radius:6px;padding:4px 8px;margin:2px 0}
.rec-card{border:1px solid #e5e7eb;border-left:3px solid #1a73e8;
    border-radius:6px;padding:0.6rem 0.8rem;margin-bottom:0.5rem;background:#fff}
.rec-code{font-family:monospace;font-size:0.8rem;font-weight:600;color:#1a73e8}
.rec-conf-high{color:#c0392b;font-size:0.7rem;font-weight:600;margin-left:8px}
.rec-conf-med{color:#e67e22;font-size:0.7rem;font-weight:600;margin-left:8px}
.rec-reason{font-size:0.8rem;color:#555;margin-top:3px;line-height:1.5}
.accepted-chip{display:inline-block;background:#e8f5e9;color:#2e7d32;
    font-family:monospace;font-size:0.75rem;padding:3px 10px;
    border-radius:99px;margin:2px}
.divider{border:none;border-top:1px solid #f0f0f0;margin:1rem 0}
</style>
""", unsafe_allow_html=True)


# ── CHECKLIST DEFINITION (from OSSF Surface Spray checklist) ─────────────────

CHECKLIST = [
    {
        "section": "Site & Soil Conditions",
        "items": [
            {"id": "s1", "label": "Site and soil conditions consistent with submitted planning materials",
             "cites": ["285.31(a)", "285.30(b)(1)(A)(i)", "285.30(b)(1)(A)(ii)", "285.30(b)(1)(A)(iii)", "285.30(b)(1)(A)(iv)", "285.30(b)(1)(A)(v)"]},
            {"id": "s2", "label": "Setback distances meet minimum standards",
             "cites": ["285.91(10)", "285.30(b)(4)", "285.31(d)"]},
        ]
    },
    {
        "section": "Sewer Pipe",
        "items": [
            {"id": "p1", "label": "Proper type pipe from structure to disposal system (Cast Iron, Ductile Iron, Sch. 40, SDR 26)",
             "cites": ["285.32(a)(1)"]},
            {"id": "p2", "label": "Slope from sewer to tank at least 1/8 inch per foot",
             "cites": ["285.32(a)(3)"]},
            {"id": "p3", "label": "Two-way sanitary-type cleanout properly installed",
             "cites": ["285.32(a)(5)"]},
        ]
    },
    {
        "section": "Pretreatment",
        "items": [
            {"id": "pt1", "label": "Pretreatment installed if required (TCEQ approved list)",
             "cites": ["285.32(b)(1)(G)"]},
            {"id": "pt2", "label": "Grease interceptors installed if required (commercial)",
             "cites": ["285.34(d)"]},
            {"id": "pt3", "label": "Approved effluent filter in place if required",
             "cites": ["285.34(a)"]},
            {"id": "pt4", "label": "Inspection/clean out port & risers provided",
             "cites": ["285.38(c)"]},
            {"id": "pt5", "label": "Secondary restraint system provided",
             "cites": ["285.38(c)"]},
            {"id": "pt6", "label": "Riser permanently fastened to lid or cast into tank",
             "cites": ["285.38(e)"]},
            {"id": "pt7", "label": "Riser cap protected against unauthorized intrusions",
             "cites": ["285.38(e)"]},
        ]
    },
    {
        "section": "Aerobic Treatment Unit",
        "items": [
            {"id": "a1", "label": "Aerobic unit installed according to approved guidelines",
             "cites": ["285.32(c)(1)"]},
            {"id": "a2", "label": "Chlorinator properly installed with chlorine tablets in place",
             "cites": ["285.33(d)(2)(D)"]},
            {"id": "a3", "label": "Maintenance tag in place", "cites": []},
        ]
    },
    {
        "section": "Pump Tank",
        "items": [
            {"id": "tk1", "label": "Pump tank is approved concrete or other acceptable material & construction",
             "cites": []},
            {"id": "tk2", "label": "Sampling port provided in treated effluent line", "cites": []},
            {"id": "tk3", "label": "Check valve and/or anti-siphon device present when required",
             "cites": []},
            {"id": "tk4", "label": "Audible and visual high water alarm on separate circuit from pump",
             "cites": []},
            {"id": "tk5", "label": "Required reserve capacity present", "cites": []},
            {"id": "tk6", "label": "Electrical connections in approved junction boxes / wiring buried",
             "cites": []},
            {"id": "tk7", "label": "Disinfection equipment listed by NSF/ANSI Standard 46 or approved by executive director",
             "cites": ["285.33(d)(2)(D)"]},
            {"id": "tk8", "label": "All tanks installed on 4\" sand cushion / proper backfill used",
             "cites": ["285.32(b)(1)(F)", "285.32(b)(1)(G)", "285.34(b)"]},
        ]
    },
    {
        "section": "Application Area",
        "items": [
            {"id": "ap1", "label": "Low angle nozzles used / pressure is as required",
             "cites": ["285.33(d)(2)(G)(i)"]},
            {"id": "ap2", "label": "Acceptable area — nothing within 10 ft of sprinkler heads",
             "cites": ["285.33(d)(2)(A)"]},
            {"id": "ap3", "label": "Landscape plan is as designed", "cites": ["285.33(d)(2)(F)"]},
            {"id": "ap4", "label": "Distribution pipe, fittings, sprinkler heads & valve covers color coded purple",
             "cites": ["285.33(d)(2)(G)(iii)", "285.33(d)(2)(G)(iv)", "285.33(d)(2)(G)(v)"]},
            {"id": "ap5", "label": "Minimum required application area present", "cites": []},
        ]
    },
]

TCEQ_REGIONS = [
    "Region 01 – Abilene", "Region 02 – Amarillo", "Region 03 – Austin",
    "Region 04 – DFW Metroplex", "Region 05 – Beaumont", "Region 06 – El Paso",
    "Region 07 – Harlingen", "Region 08 – Lubbock", "Region 09 – Midland",
    "Region 10 – San Antonio", "Region 11 – Waco", "Region 12 – Houston",
    "Region 13 – San Angelo", "Region 14 – Tyler",
]

BUSINESS_TYPES = [
    "Residential (Single Family)", "Residential (Multi-Family)",
    "Commercial Facility", "Mobile Home Park", "School / Institutional",
    "Food Service Establishment", "Healthcare Facility", "Industrial",
]


# ── DATA INTEGRATION STUBS ────────────────────────────────────────────────────

def get_nov_context(item_ids: list[str], region: str, biz_type: str) -> str:
    """
    TODO: Replace with your actual NOV dataset co-occurrence lookup.

    Should query your precomputed co-occurrence matrix filtered by:
      - region (from facility context)
      - business type / NAICS cluster (from facility context)
      - the specific checklist items that failed (item_ids)

    Return a plain-text summary like:
      "In Region 4, commercial OSSF facilities with setback failures
       also had §285.34(a) violations in 71% of historical NOV cases."
    """
    return (
        f"[NOV DATASET CONTEXT PLACEHOLDER]\n"
        f"Region: {region} | Business type: {biz_type}\n"
        f"Failed items: {', '.join(item_ids)}\n\n"
        f"TODO: Insert co-occurrence statistics from your NOV dataset here.\n"
        f"Example: '§285.91(10) setback violations co-occur with §285.30(b)(4) "
        f"in 81% of similar Region 4 OSSF cases.'"
    )


def get_tac_text(citations: list[str]) -> str:
    """
    TODO: Replace with your actual TAC 30 text retrieval.

    Options:
      A) Prebuilt citation JSON: load a dict keyed by citation code,
         return the relevant rule text for each citation in the list.
      B) Vector DB query: retrieve the most relevant chunks from your
         ChromaDB / VectorShift knowledge base for these citations.

    Return the raw TAC text to be used as RAG context in the prompt.
    """
    if not citations:
        return "[No specific citations for this item]"
    return (
        f"[TAC 30 TEXT PLACEHOLDER for: {', '.join(citations)}]\n\n"
        f"TODO: Insert retrieved rule text from your TAC 30 knowledge base.\n"
        f"Example: '30 TAC §285.91(10): A person commits an offense if the "
        f"person fails to comply with the setback requirements...'"
    )


# ── AI SUGGESTION ENGINE ──────────────────────────────────────────────────────

def get_violation_suggestions(
    failed_items: list[dict],
    region: str,
    biz_type: str,
    already_accepted: list[str],
) -> str:
    """
    Calls Anthropic API with NOV context + TAC text to suggest
    applicable violation codes for the failed checklist items.
    """
    if not failed_items:
        return ""

    # Build context
    item_ids = [i["id"] for i in failed_items]
    all_cites = list({c for i in failed_items for c in i.get("cites", [])})
    nov_context = get_nov_context(item_ids, region, biz_type)
    tac_text = get_tac_text(all_cites)

    items_summary = "\n".join(
        f"- {i['label']} (checklist citations: {', '.join(i['cites']) if i['cites'] else 'none listed'})"
        for i in failed_items
    )

    already = f"Already accepted: {', '.join(already_accepted)}" if already_accepted else ""

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    prompt = f"""You are assisting a TCEQ field inspector using an OSSF (On-Site Sewage Facility) surface spray inspection checklist.

FACILITY CONTEXT:
- TCEQ Region: {region}
- Business Type: {biz_type}

FAILED CHECKLIST ITEMS:
{items_summary}

HISTORICAL NOV PATTERN DATA:
{nov_context}

RELEVANT TAC 30 RULE TEXT:
{tac_text}

{already}

Your task: Recommend the 2-4 most applicable TAC 30 violation citation codes for these failures.

For each citation, provide:
1. The citation code (e.g., 30 TAC §285.91(10))
2. Likelihood: HIGH or MODERATE
3. One sentence of plain-language reasoning grounded in the NOV pattern data or rule text above

Rules:
- Only cite sections that genuinely apply to the observed failures
- Do not hallucinate citations — only use codes from the checklist items or the TAC text provided
- Do not repeat already accepted citations
- Format each suggestion as: CODE | LIKELIHOOD | REASONING

Example format:
§285.91(10) | HIGH | Setback distance violations are the primary citation for this checklist item in Region 4 OSSF inspections, appearing in 81% of similar cases.
§285.30(b)(4) | MODERATE | Co-cited when the setback deficiency relates to the original planning submission — verify against permit file."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def parse_suggestions(raw: str) -> list[dict]:
    """Parse the structured suggestion output into a list of dicts."""
    suggestions = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            suggestions.append({
                "code": parts[0],
                "likelihood": parts[1].upper(),
                "reason": parts[2],
            })
    return suggestions


# ── SESSION STATE INIT ────────────────────────────────────────────────────────

if "results" not in st.session_state:
    st.session_state.results = {}  # item_id -> "pass" | "fail" | "na"
if "accepted" not in st.session_state:
    st.session_state.accepted = []
if "suggestions_cache" not in st.session_state:
    st.session_state.suggestions_cache = {}


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown("### TCEQ · OSSF Surface Spray Inspection Checklist", unsafe_allow_html=True)
st.markdown("""
<style>
h3 { white-space: nowrap; font-size: clamp(1rem, 2vw, 1.4rem) !important; }
</style>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.1, 1], gap="large")

# ── LEFT: Facility context + checklist ───────────────────────────────────────
with col_left:
    ctx1, ctx2 = st.columns(2)
    with ctx1:
        region = st.selectbox("TCEQ Region", ["— Select —"] + TCEQ_REGIONS)
    with ctx2:
        biz_type = st.selectbox("Business Type", ["— Select —"] + BUSINESS_TYPES)

    context_set = region != "— Select —" and biz_type != "— Select —"
    if not context_set:
        st.info("Select region and business type to enable AI suggestions.")

    st.divider()

    for section in CHECKLIST:
        st.markdown(f'<div class="section-label">{section["section"]}</div>',
                    unsafe_allow_html=True)
        for item in section["items"]:
            item_id = item["id"]
            current = st.session_state.results.get(item_id, "—")

            c1, c2 = st.columns([3, 1])
            with c1:
                label = item["label"]
                if current == "fail":
                    st.markdown(f'<div class="fail-item">❌ {label}</div>',
                                unsafe_allow_html=True)
                elif current == "pass":
                    st.markdown(f'<span style="color:#aaa;font-size:0.85rem">✓ {label}</span>',
                                unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="font-size:0.85rem">{label}</span>',
                                unsafe_allow_html=True)
            with c2:
                choice = st.selectbox(
                    label="",
                    options=["—", "Pass", "Fail", "N/A"],
                    index=["—", "Pass", "Fail", "N/A"].index(
                        {"pass": "Pass", "fail": "Fail", "na": "N/A"}.get(current, "—")
                    ),
                    key=f"sel_{item_id}",
                    label_visibility="collapsed",
                )
                mapped = {"Pass": "pass", "Fail": "fail", "N/A": "na"}.get(choice)
                if mapped:
                    st.session_state.results[item_id] = mapped
                elif item_id in st.session_state.results and choice == "—":
                    del st.session_state.results[item_id]

    # Summary
    fail_count = sum(1 for v in st.session_state.results.values() if v == "fail")
    pass_count = sum(1 for v in st.session_state.results.values() if v == "pass")
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Failures", fail_count)
    m2.metric("Passes", pass_count)
    m3.metric("Violations accepted", len(st.session_state.accepted))


# ── RIGHT: AI suggestions + accepted violations ───────────────────────────────
with col_right:
    failed_items = [
        item
        for section in CHECKLIST
        for item in section["items"]
        if st.session_state.results.get(item["id"]) == "fail"
    ]

    if not failed_items:
        st.markdown("#### AI Violation Suggestions")
        st.caption("Mark any checklist item as **Fail** to see suggested TAC citations.")

    else:
        st.markdown("#### AI Violation Suggestions")

        if not context_set:
            st.warning("Set Region and Business Type above to get context-aware suggestions.")
        else:
            cache_key = (
                tuple(i["id"] for i in failed_items),
                region,
                biz_type,
                tuple(sorted(st.session_state.accepted)),
            )

            if st.button("Get suggestions", type="primary"):
                with st.spinner("Retrieving violation suggestions..."):
                    raw = get_violation_suggestions(
                        failed_items, region, biz_type, st.session_state.accepted
                    )
                    st.session_state.suggestions_cache[cache_key] = parse_suggestions(raw)

            suggestions = st.session_state.suggestions_cache.get(cache_key, [])

            if suggestions:
                st.caption(f"Suggested violations for {len(failed_items)} failed item(s) · {region} · {biz_type}")

                new_accepts = []
                for s in suggestions:
                    if s["code"] in st.session_state.accepted:
                        continue
                    conf_class = "rec-conf-high" if "HIGH" in s["likelihood"] else "rec-conf-med"
                    st.markdown(
                        f'<div class="rec-card">'
                        f'<span class="rec-code">{s["code"]}</span>'
                        f'<span class="{conf_class}">{s["likelihood"]}</span>'
                        f'<div class="rec-reason">{s["reason"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if st.button(f"Accept {s['code']}", key=f"accept_{s['code']}"):
                        new_accepts.append(s["code"])

                if new_accepts:
                    st.session_state.accepted.extend(new_accepts)
                    st.rerun()

                all_codes = [s["code"] for s in suggestions
                             if s["code"] not in st.session_state.accepted]
                if all_codes and st.button("Accept all suggestions"):
                    st.session_state.accepted.extend(all_codes)
                    st.rerun()

        st.divider()

        # Accepted violations
        st.markdown("#### Accepted Violations")
        if st.session_state.accepted:
            chips = " ".join(
                f'<span class="accepted-chip">{c}</span>'
                for c in st.session_state.accepted
            )
            st.markdown(chips, unsafe_allow_html=True)

            remove = st.selectbox(
                "Remove a code",
                ["—"] + st.session_state.accepted,
                key="remove_sel"
            )
            if remove != "—":
                st.session_state.accepted.remove(remove)
                st.rerun()
        else:
            st.caption("No violations accepted yet.")

        st.divider()

        # Manual input
        st.markdown("#### Add Code Manually")
        manual_col1, manual_col2 = st.columns([3, 1])
        with manual_col1:
            manual_code = st.text_input(
                "Citation code",
                placeholder="e.g. §285.62(3)",
                label_visibility="collapsed"
            )
        with manual_col2:
            if st.button("Add") and manual_code.strip():
                if manual_code.strip() not in st.session_state.accepted:
                    st.session_state.accepted.append(manual_code.strip())
                st.rerun()
