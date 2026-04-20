"""
TCEQ OSSF Surface Spray Inspection Checklist — Streamlit App v3
----------------------------------------------------------------
HOW TO RUN:
  1. pip install streamlit anthropic
  2. export ANTHROPIC_API_KEY=your_key_here  (or set in Streamlit secrets)
  3. streamlit run tceq_checklist_v3.py

CHANGES IN v3:
  - Pass/Fail are now one-click buttons (no dropdown)
  - AI suggestions panel moved to sidebar (always visible, independent scroll)
  - Accepted suggestions show green checkmark + become unclickable (don't disappear)
  - Accepted violations chips are consistently styled
  - § symbol auto-prepended on manual code entry
  - Delayed formatting bug fixed (buttons trigger immediate rerun via callback)

INTEGRATION POINTS (marked TODO):
  - get_nov_context(): replace with NOV co-occurrence lookup
  - get_tac_text(): replace with TAC 30 vector DB / citation JSON lookup
"""

import streamlit as st
import anthropic

st.set_page_config(
    page_title="TCEQ OSSF Inspection Checklist",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container { padding-top: 1.25rem; padding-bottom: 1rem; }

/* Section headers */
.section-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.09em; color: #888;
    margin: 1.1rem 0 0.3rem; padding-bottom: 4px;
    border-bottom: 1px solid #f0f0f0;
}

/* Checklist item row states */
.item-fail {
    background: #fff0f0; border-radius: 6px;
    padding: 5px 8px; color: #c0392b; font-size: 0.85rem; line-height: 1.4;
}
.item-pass {
    color: #aaa; font-size: 0.85rem; line-height: 1.4;
    padding: 5px 0;
}
.item-neutral {
    font-size: 0.85rem; line-height: 1.4; padding: 5px 0;
}

/* Suggestion cards */
.rec-card {
    border: 1px solid #e5e7eb; border-left: 3px solid #1a73e8;
    border-radius: 6px; padding: 0.55rem 0.75rem;
    margin-bottom: 0.4rem; background: #fff;
}
.rec-card-accepted {
    border: 1px solid #c8e6c9; border-left: 3px solid #2e7d32;
    border-radius: 6px; padding: 0.55rem 0.75rem;
    margin-bottom: 0.4rem; background: #f1f8f1;
}
.rec-code { font-family: monospace; font-size: 0.8rem; font-weight: 600; color: #1a73e8; }
.rec-code-accepted { font-family: monospace; font-size: 0.8rem; font-weight: 600; color: #2e7d32; }
.rec-conf-high { color: #c0392b; font-size: 0.7rem; font-weight: 600; margin-left: 8px; }
.rec-conf-med  { color: #e67e22; font-size: 0.7rem; font-weight: 600; margin-left: 8px; }
.rec-reason { font-size: 0.78rem; color: #555; margin-top: 3px; line-height: 1.45; }
.rec-accepted-label { font-size: 0.75rem; color: #2e7d32; font-weight: 600; margin-top: 4px; }

/* Accepted violation chips — single consistent style */
.chip-wrap { display: flex; flex-wrap: wrap; gap: 5px; margin: 6px 0; }
.accepted-chip {
    display: inline-block; background: #e8f5e9; color: #2e7d32;
    font-family: monospace; font-size: 0.75rem;
    padding: 4px 10px; border-radius: 99px;
    border: 1px solid #c8e6c9;
}
</style>
""", unsafe_allow_html=True)


# ── CHECKLIST DATA ────────────────────────────────────────────────────────────

CHECKLIST = [
    {
        "section": "Site & Soil Conditions",
        "items": [
            {"id": "s1",
             "label": "Site and soil conditions consistent with submitted planning materials",
             "cites": ["285.31(a)", "285.30(b)(1)(A)(i)", "285.30(b)(1)(A)(ii)",
                       "285.30(b)(1)(A)(iii)", "285.30(b)(1)(A)(iv)", "285.30(b)(1)(A)(v)"]},
            {"id": "s2",
             "label": "Setback distances meet minimum standards",
             "cites": ["285.91(10)", "285.30(b)(4)", "285.31(d)"]},
        ]
    },
    {
        "section": "Sewer Pipe",
        "items": [
            {"id": "p1",
             "label": "Proper type pipe from structure to disposal system (Cast Iron, Ductile Iron, Sch. 40, SDR 26)",
             "cites": ["285.32(a)(1)"]},
            {"id": "p2",
             "label": "Slope from sewer to tank at least 1/8 inch per foot",
             "cites": ["285.32(a)(3)"]},
            {"id": "p3",
             "label": "Two-way sanitary-type cleanout properly installed",
             "cites": ["285.32(a)(5)"]},
        ]
    },
    {
        "section": "Pretreatment",
        "items": [
            {"id": "pt1",
             "label": "Pretreatment installed if required (TCEQ approved list)",
             "cites": ["285.32(b)(1)(G)"]},
            {"id": "pt2",
             "label": "Grease interceptors installed if required (commercial)",
             "cites": ["285.34(d)"]},
            {"id": "pt3",
             "label": "Approved effluent filter in place if required",
             "cites": ["285.34(a)"]},
            {"id": "pt4",
             "label": "Inspection/clean out port & risers provided",
             "cites": ["285.38(c)"]},
            {"id": "pt5",
             "label": "Secondary restraint system provided",
             "cites": ["285.38(c)"]},
            {"id": "pt6",
             "label": "Riser permanently fastened to lid or cast into tank",
             "cites": ["285.38(e)"]},
            {"id": "pt7",
             "label": "Riser cap protected against unauthorized intrusions",
             "cites": ["285.38(e)"]},
        ]
    },
    {
        "section": "Aerobic Treatment Unit",
        "items": [
            {"id": "a1",
             "label": "Aerobic unit installed according to approved guidelines",
             "cites": ["285.32(c)(1)"]},
            {"id": "a2",
             "label": "Chlorinator properly installed with chlorine tablets in place",
             "cites": ["285.33(d)(2)(D)"]},
            {"id": "a3",
             "label": "Maintenance tag in place",
             "cites": []},
        ]
    },
    {
        "section": "Pump Tank",
        "items": [
            {"id": "tk1",
             "label": "Pump tank is approved concrete or other acceptable material & construction",
             "cites": []},
            {"id": "tk2",
             "label": "Sampling port provided in treated effluent line",
             "cites": []},
            {"id": "tk3",
             "label": "Check valve and/or anti-siphon device present when required",
             "cites": []},
            {"id": "tk4",
             "label": "Audible and visual high water alarm on separate circuit from pump",
             "cites": []},
            {"id": "tk5",
             "label": "Required reserve capacity present",
             "cites": []},
            {"id": "tk6",
             "label": "Electrical connections in approved junction boxes / wiring buried",
             "cites": []},
            {"id": "tk7",
             "label": "Disinfection equipment listed by NSF/ANSI Standard 46 or approved by executive director",
             "cites": ["285.33(d)(2)(D)"]},
            {"id": "tk8",
             "label": 'All tanks installed on 4" sand cushion / proper backfill used',
             "cites": ["285.32(b)(1)(F)", "285.32(b)(1)(G)", "285.34(b)"]},
        ]
    },
    {
        "section": "Application Area",
        "items": [
            {"id": "ap1",
             "label": "Low angle nozzles used / pressure is as required",
             "cites": ["285.33(d)(2)(G)(i)"]},
            {"id": "ap2",
             "label": "Acceptable area — nothing within 10 ft of sprinkler heads",
             "cites": ["285.33(d)(2)(A)"]},
            {"id": "ap3",
             "label": "Landscape plan is as designed",
             "cites": ["285.33(d)(2)(F)"]},
            {"id": "ap4",
             "label": "Distribution pipe, fittings, sprinkler heads & valve covers color coded purple",
             "cites": ["285.33(d)(2)(G)(iii)", "285.33(d)(2)(G)(iv)", "285.33(d)(2)(G)(v)"]},
            {"id": "ap5",
             "label": "Minimum required application area present",
             "cites": []},
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

def get_nov_context(item_ids: list, region: str, biz_type: str) -> str:
    """
    TODO: Replace with NOV dataset co-occurrence lookup.
    Filter by region + business type + failed item IDs.
    Return plain-text summary of historical co-occurrence patterns.
    """
    return (
        f"[NOV DATASET CONTEXT PLACEHOLDER]\n"
        f"Region: {region} | Business type: {biz_type}\n"
        f"Failed items: {', '.join(item_ids)}\n\n"
        f"TODO: Insert co-occurrence statistics from your NOV dataset here.\n"
        f"Example: '§285.91(10) setback violations co-occur with §285.30(b)(4) "
        f"in 81% of similar Region 4 OSSF cases.'"
    )


def get_tac_text(citations: list) -> str:
    """
    TODO: Replace with TAC 30 text retrieval (citation JSON or vector DB).
    Return the actual rule text for the given citation codes.
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

def get_violation_suggestions(failed_items: list, region: str, biz_type: str) -> str:
    """Calls Anthropic API with NOV + TAC context to suggest applicable citations."""
    item_ids = [i["id"] for i in failed_items]
    all_cites = list({c for i in failed_items for c in i.get("cites", [])})
    nov_context = get_nov_context(item_ids, region, biz_type)
    tac_text = get_tac_text(all_cites)

    items_summary = "\n".join(
        f"- {i['label']} (checklist citations: {', '.join(i['cites']) if i['cites'] else 'none listed'})"
        for i in failed_items
    )

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    prompt = f"""You are assisting a TCEQ field inspector using an OSSF surface spray inspection checklist.

FACILITY CONTEXT:
- TCEQ Region: {region}
- Business Type: {biz_type}

FAILED CHECKLIST ITEMS:
{items_summary}

HISTORICAL NOV PATTERN DATA:
{nov_context}

RELEVANT TAC 30 RULE TEXT:
{tac_text}

Recommend the 2-4 most applicable TAC 30 violation citation codes for these failures.

For each citation provide:
1. The citation code (e.g., §285.91(10))
2. Likelihood: HIGH or MODERATE
3. One sentence of plain-language reasoning grounded in the NOV pattern data or rule text

Rules:
- Only cite sections that genuinely apply to the observed failures
- Do not hallucinate citations — only use codes supported by the context above
- Format strictly as: CODE | LIKELIHOOD | REASONING

Example:
§285.91(10) | HIGH | Setback distance violations are the primary citation for this checklist item, appearing in 81% of similar Region 4 cases."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def parse_suggestions(raw: str) -> list:
    """Parse pipe-delimited suggestion output into list of dicts."""
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


# ── SESSION STATE ─────────────────────────────────────────────────────────────

if "results" not in st.session_state:
    st.session_state.results = {}        # item_id -> "pass" | "fail"
if "accepted" not in st.session_state:
    st.session_state.accepted = []       # list of accepted citation strings
if "suggestions_cache" not in st.session_state:
    st.session_state.suggestions_cache = {}  # cache_key -> list of suggestion dicts


# ── CALLBACKS ─────────────────────────────────────────────────────────────────

def set_result(item_id, value):
    """Set pass/fail for a checklist item. Runs before rerun so state is immediate."""
    st.session_state.results[item_id] = value


def accept_suggestion(code):
    """Add a single suggestion code to accepted list."""
    if code not in st.session_state.accepted:
        st.session_state.accepted.append(code)


def accept_all_suggestions(codes):
    """Accept all suggestion codes not already accepted."""
    for code in codes:
        if code not in st.session_state.accepted:
            st.session_state.accepted.append(code)


def remove_accepted(code):
    """Remove a code from accepted list."""
    if code in st.session_state.accepted:
        st.session_state.accepted.remove(code)


# ── SIDEBAR: AI SUGGESTIONS + ACCEPTED VIOLATIONS ────────────────────────────

with st.sidebar:
    st.markdown("### AI Violation Suggestions")

    region = st.selectbox("TCEQ Region", ["— Select —"] + TCEQ_REGIONS)
    biz_type = st.selectbox("Business Type", ["— Select —"] + BUSINESS_TYPES)
    context_set = region != "— Select —" and biz_type != "— Select —"

    st.divider()

    failed_items = [
        item
        for section in CHECKLIST
        for item in section["items"]
        if st.session_state.results.get(item["id"]) == "fail"
    ]

    if not failed_items:
        st.caption("Mark any checklist item as **Fail** to see suggested TAC citations.")

    else:
        if not context_set:
            st.warning("Select Region and Business Type above to enable suggestions.")
        else:
            # Cache key excludes accepted list so suggestions persist after individual accepts
            cache_key = (
                tuple(i["id"] for i in failed_items),
                region,
                biz_type,
            )

            if st.button("Get suggestions", type="primary", use_container_width=True):
                with st.spinner("Retrieving violation suggestions..."):
                    raw = get_violation_suggestions(failed_items, region, biz_type)
                    st.session_state.suggestions_cache[cache_key] = parse_suggestions(raw)

            suggestions = st.session_state.suggestions_cache.get(cache_key, [])

            if suggestions:
                st.caption(
                    f"{len(failed_items)} failed item(s) · {region.split('–')[0].strip()} · {biz_type}"
                )

                all_unaccepted = [s["code"] for s in suggestions
                                  if s["code"] not in st.session_state.accepted]

                for s in suggestions:
                    is_accepted = s["code"] in st.session_state.accepted
                    conf_class = "rec-conf-high" if "HIGH" in s["likelihood"] else "rec-conf-med"

                    if is_accepted:
                        st.markdown(
                            f'<div class="rec-card-accepted">'
                            f'<span class="rec-code-accepted">{s["code"]}</span>'
                            f'<div class="rec-accepted-label">✓ Accepted</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div class="rec-card">'
                            f'<span class="rec-code">{s["code"]}</span>'
                            f'<span class="{conf_class}">{s["likelihood"]}</span>'
                            f'<div class="rec-reason">{s["reason"]}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        st.button(
                            f"Accept {s['code']}",
                            key=f"accept_{s['code']}",
                            on_click=accept_suggestion,
                            args=(s["code"],),
                            use_container_width=True,
                        )

                if all_unaccepted:
                    st.button(
                        "Accept all",
                        key="accept_all",
                        on_click=accept_all_suggestions,
                        args=(all_unaccepted,),
                        use_container_width=True,
                    )

    st.divider()

    # ── Accepted violations ───────────────────────────────────────────────────
    st.markdown("**Accepted Violations**")

    if st.session_state.accepted:
        chips_html = '<div class="chip-wrap">' + "".join(
            f'<span class="accepted-chip">{c}</span>'
            for c in st.session_state.accepted
        ) + "</div>"
        st.markdown(chips_html, unsafe_allow_html=True)

        remove_choice = st.selectbox(
            "Remove a code",
            ["—"] + st.session_state.accepted,
            key="remove_sel",
            label_visibility="collapsed",
        )
        if remove_choice != "—":
            remove_accepted(remove_choice)
            st.rerun()
    else:
        st.caption("No violations accepted yet.")

    st.divider()

    # ── Manual entry ──────────────────────────────────────────────────────────
    st.markdown("**Add Code Manually**")
    mc1, mc2 = st.columns([3, 1])
    with mc1:
        manual_input = st.text_input(
            "Code",
            placeholder="285.62(3)",
            label_visibility="collapsed",
            key="manual_code_input",
        )
    with mc2:
        if st.button("Add", key="manual_add"):
            code = manual_input.strip()
            if code:
                if not code.startswith("§"):
                    code = "§" + code
                if code not in st.session_state.accepted:
                    st.session_state.accepted.append(code)
                st.rerun()


# ── MAIN: CHECKLIST ───────────────────────────────────────────────────────────

st.header("TCEQ · OSSF Surface Spray Inspection Checklist")

# Summary metrics
fail_count = sum(1 for v in st.session_state.results.values() if v == "fail")
pass_count = sum(1 for v in st.session_state.results.values() if v == "pass")
m1, m2, m3 = st.columns(3)
m1.metric("Failures", fail_count)
m2.metric("Passes", pass_count)
m3.metric("Violations accepted", len(st.session_state.accepted))

st.divider()

for section in CHECKLIST:
    st.markdown(
        f'<div class="section-label">{section["section"]}</div>',
        unsafe_allow_html=True
    )

    for item in section["items"]:
        item_id = item["id"]
        result = st.session_state.results.get(item_id)
        label = item["label"]

        c_label, c_pass, c_fail = st.columns([5, 1, 1])

        with c_label:
            if result == "fail":
                st.markdown(f'<div class="item-fail">❌ {label}</div>',
                            unsafe_allow_html=True)
            elif result == "pass":
                st.markdown(f'<div class="item-pass">✓ {label}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="item-neutral">{label}</div>',
                            unsafe_allow_html=True)

        with c_pass:
            st.button(
                "✓ Pass" if result == "pass" else "Pass",
                key=f"pass_{item_id}",
                type="primary" if result == "pass" else "secondary",
                disabled=(result == "pass"),
                on_click=set_result,
                args=(item_id, "pass"),
                use_container_width=True,
            )

        with c_fail:
            st.button(
                "✗ Fail" if result == "fail" else "Fail",
                key=f"fail_{item_id}",
                type="primary" if result == "fail" else "secondary",
                disabled=(result == "fail"),
                on_click=set_result,
                args=(item_id, "fail"),
                use_container_width=True,
            )
