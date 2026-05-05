"""
TCEQ Public Drinking Water System Inspection Checklist — Streamlit App v5
--------------------------------------------------------------------------
HOW TO RUN:
  1. pip install streamlit anthropic
  2. Place tac30_chapter290.json in the same folder as this script
  3. Set ANTHROPIC_API_KEY in Streamlit secrets or environment
  4. streamlit run tceq_checklist_v5.py

CHANGES FROM v4:
  - Checklist updated to Chapter 290 (Public Drinking Water) from Chapter 285 (OSSF)
  - tac30_chapter290.json knowledge base wired into get_tac_text()
  - Checklist sections: Source, Treatment, Storage, Distribution,
    Monitoring & Sampling, Records & Reporting, Operations & Staffing
  - All citation codes updated to Chapter 290 references

INTEGRATION POINTS:
  - get_nov_context(): still a placeholder — replace with NOV co-occurrence lookup
  - get_tac_text(): FULLY WIRED to tac30_chapter290.json — no changes needed
"""

import os
import json
import streamlit as st
import anthropic

st.set_page_config(
    page_title="TCEQ Drinking Water Inspection Checklist",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container { padding-top: 1.25rem; padding-bottom: 1rem; }

.section-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.09em; color: #888;
    margin: 1.1rem 0 0.3rem; padding-bottom: 4px;
    border-bottom: 1px solid #f0f0f0;
}
.item-fail {
    background: #fff0f0; border-radius: 6px;
    padding: 5px 8px; color: #c0392b; font-size: 0.85rem; line-height: 1.4;
}
.item-pass {
    color: #aaa; font-size: 0.85rem; line-height: 1.4; padding: 5px 0;
}
.item-neutral {
    font-size: 0.85rem; line-height: 1.4; padding: 5px 0;
}
.predict-box {
    background: #f3f0ff; border: 1px solid #d0c4f7;
    border-left: 3px solid #7c3aed;
    border-radius: 6px; padding: 0.65rem 0.85rem; margin-bottom: 0.5rem;
}
.predict-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.07em; color: #7c3aed; margin-bottom: 4px;
}
.predict-text { font-size: 0.8rem; color: #333; line-height: 1.5; }
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
.chip-wrap { display: flex; flex-wrap: wrap; gap: 5px; margin: 6px 0; }
.accepted-chip {
    display: inline-block; background: #e8f5e9; color: #2e7d32;
    font-family: monospace; font-size: 0.75rem;
    padding: 4px 10px; border-radius: 99px;
    border: 1px solid #c8e6c9;
}
.layer-label {
    font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; margin-bottom: 6px;
}
.layer-1 { color: #7c3aed; }
.layer-2 { color: #1a73e8; }
.kb-badge {
    display: inline-block; background: #e8f5e9; color: #2e7d32;
    font-size: 0.65rem; font-weight: 600; padding: 2px 7px;
    border-radius: 99px; border: 1px solid #c8e6c9; margin-left: 6px;
}
</style>
""", unsafe_allow_html=True)


# ── KNOWLEDGE BASE: TAC 30 Chapter 290 ───────────────────────────────────────

@st.cache_resource
def load_knowledge_base():
    """
    Load TAC 30 Chapter 290 citation JSON.
    Cached so it only reads from disk once per session.
    """
    kb_path = os.path.join(os.path.dirname(__file__), "tac30_chapter290.json")
    if not os.path.exists(kb_path):
        st.error(
            "Knowledge base file not found: tac30_chapter290.json\n"
            "Make sure it is in the same folder as this script."
        )
        return {}
    with open(kb_path, encoding="utf-8") as f:
        return json.load(f)

TAC_290 = load_knowledge_base()


# ── CHECKLIST DEFINITION: Chapter 290 Public Drinking Water ──────────────────

CHECKLIST = [
    {
        "section": "Water Source",
        "items": [
            {"id": "src1",
             "label": "Water source quality meets commission drinking water standards",
             "cites": ["290.41(a)"]},
            {"id": "src2",
             "label": "Source supply capacity meets maximum daily demand requirements",
             "cites": ["290.41(b)", "290.45"]},
            {"id": "src3",
             "label": "Drought contingency plan current and reported as required",
             "cites": ["290.41(b)(1)"]},
            {"id": "src4",
             "label": "Groundwater source protected from surface water contamination",
             "cites": ["290.41(c)"]},
        ]
    },
    {
        "section": "Treatment",
        "items": [
            {"id": "trt1",
             "label": "Treatment plant capacity exceeds maximum daily demand",
             "cites": ["290.42(a)(1)"]},
            {"id": "trt2",
             "label": "Plant located away from flood-prone or seepage areas; accessible by all-weather road",
             "cites": ["290.42(a)(1)", "290.42(a)(3)"]},
            {"id": "trt3",
             "label": "Disinfection facilities provided and operational",
             "cites": ["290.42(b)(1)"]},
            {"id": "trt4",
             "label": "Disinfectant residuals meet minimum levels before entering distribution system",
             "cites": ["290.110(b)(2)"]},
            {"id": "trt5",
             "label": "Disinfectant residuals do not exceed maximum residual disinfectant levels (MRDLs)",
             "cites": ["290.110(b)"]},
            {"id": "trt6",
             "label": "Surface water treatment meets turbidity and CT requirements",
             "cites": ["290.111"]},
        ]
    },
    {
        "section": "Storage",
        "items": [
            {"id": "sto1",
             "label": "Storage capacity meets minimum requirements per §290.45",
             "cites": ["290.43(a)", "290.45"]},
            {"id": "sto2",
             "label": "Storage tanks meet minimum setback distances from sewage facilities",
             "cites": ["290.43(b)(1)"]},
            {"id": "sto3",
             "label": "Storage tanks properly sealed, vented, and protected from contamination",
             "cites": ["290.43(c)"]},
            {"id": "sto4",
             "label": "No underground storage within 50 ft of sanitary sewer or septic tank",
             "cites": ["290.43(b)(3)"]},
        ]
    },
    {
        "section": "Distribution",
        "items": [
            {"id": "dis1",
             "label": "Distribution system materials comply with AWWA/ANSI/NSF standards",
             "cites": ["290.44(a)(1)", "290.44(a)(2)"]},
            {"id": "dis2",
             "label": "No pipe previously used for non-drinking water purposes in system",
             "cites": ["290.44(a)(3)"]},
            {"id": "dis3",
             "label": "Water mains installed at required depth (minimum 24 inches below surface)",
             "cites": ["290.44(a)(4)"]},
            {"id": "dis4",
             "label": "System maintains positive pressure (minimum 35 psi) throughout distribution",
             "cites": ["290.46(s)"]},
            {"id": "dis5",
             "label": "Cross-connection control program in place; no unprotected cross-connections",
             "cites": ["290.46(j)"]},
        ]
    },
    {
        "section": "Monitoring & Sampling",
        "items": [
            {"id": "mon1",
             "label": "Microbiological samples collected and submitted per required schedule",
             "cites": ["290.46(b)", "290.109"]},
            {"id": "mon2",
             "label": "Chemical samples submitted as directed by executive director",
             "cites": ["290.46(c)"]},
            {"id": "mon3",
             "label": "Disinfectant residual monitored daily at entry point and in distribution",
             "cites": ["290.46(d)", "290.110"]},
            {"id": "mon4",
             "label": "Lead and copper samples collected from required tap locations",
             "cites": ["290.117(c)", "290.115(f)(1)"]},
            {"id": "mon5",
             "label": "Up-to-date monitoring plan maintained at treatment plant and central location",
             "cites": ["290.121(a)"]},
            {"id": "mon6",
             "label": "Monitoring plan identifies all sampling locations, frequencies, and laboratories",
             "cites": ["290.121(b)"]},
        ]
    },
    {
        "section": "Records & Reporting",
        "items": [
            {"id": "rec1",
             "label": "All test, measurement, and analysis results submitted to executive director within 10 days",
             "cites": ["290.102(g)"]},
            {"id": "rec2",
             "label": "Records retained for required periods and available for inspection",
             "cites": ["290.46(m)"]},
            {"id": "rec3",
             "label": "Public notification issued for any MCL, MRDL, or treatment technique violation",
             "cites": ["290.122(a)"]},
            {"id": "rec4",
             "label": "Consumer confidence report (CCR) prepared and distributed annually",
             "cites": ["290.272", "290.274"]},
            {"id": "rec5",
             "label": "CCR contains all required health information and contaminant data",
             "cites": ["290.272", "290.273"]},
        ]
    },
    {
        "section": "Operations & Staffing",
        "items": [
            {"id": "ops1",
             "label": "Certified operator on staff meeting requirements for system classification",
             "cites": ["290.46(e)"]},
            {"id": "ops2",
             "label": "Operator maintains required contact hours and certification renewals",
             "cites": ["290.46(e)"]},
            {"id": "ops3",
             "label": "System allows entry to TCEQ members and agents for inspection",
             "cites": ["290.46(a)"]},
            {"id": "ops4",
             "label": "Emergency response plan current and approved by executive director",
             "cites": ["290.46(l)"]},
            {"id": "ops5",
             "label": "Facility constructed per approved plans; material changes reported to TCEQ",
             "cites": ["290.39(c)"]},
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
    "Community Water System (CWS)",
    "Non-Transient Non-Community (NTNC)",
    "Transient Non-Community (TNC)",
    "Municipal / City System",
    "Utility District (MUD / WCID)",
    "Mobile Home Park",
    "School / Institutional",
    "Food Service / Commercial",
]


# ── DATA INTEGRATION ──────────────────────────────────────────────────────────

@st.cache_resource
def load_nov_data():
    path = os.path.join(os.path.dirname(__file__), "nov_cooccurrence.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

NOV_DATA = load_nov_data()

REGION_MAP = {
    "Region 01": "REGION_01", "Region 02": "REGION_02",
    "Region 03": "REGION_03", "Region 04": "REGION_04",
    "Region 05": "REGION_05", "Region 06": "REGION_06",
    "Region 07": "REGION_07", "Region 08": "REGION_08",
    "Region 09": "REGION_09", "Region 10": "REGION_10",
    "Region 11": "REGION_11", "Region 12": "REGION_12",
    "Region 13": "REGION_13", "Region 14": "REGION_14",
    "Region 15": "REGION_15", "Region 16": "REGION_16",
}

BIZ_MAP = {
    "Community Water System (CWS)":        "PUBLIC_WATER",
    "Non-Transient Non-Community (NTNC)":  "PUBLIC_WATER",
    "Transient Non-Community (TNC)":       "PUBLIC_WATER",
    "Municipal / City System":             "CITY_GOVERNMENT",
    "Utility District (MUD / WCID)":       "PUBLIC_WATER",
    "Mobile Home Park":                    "MOBILE_HOME_PARK",
    "School / Institutional":              "INSTITUTIONAL",
    "Food Service / Commercial":           "FOOD_SERVICE",
}

def get_nov_context(item_ids: list, region: str, biz_type: str) -> str:
    if not NOV_DATA:
        return "[NOV dataset not loaded]"

    region_key = REGION_MAP.get(region.split("–")[0].strip())
    biz_key = BIZ_MAP.get(biz_type, "OTHER")

    # Collect all citation codes from the failed checklist items
    all_cites = []
    for section in CHECKLIST:
        for item in section["items"]:
            if item["id"] in item_ids:
                all_cites.extend(item.get("cites", []))

    if not all_cites:
        return "[No citations mapped to failed items]"

    lines = []
    seen_co = set()

    for cite in all_cites:
        base = cite.replace("§", "").strip().split("(")[0]
        full = cite.replace("§", "").strip()

        # Try region-specific first, fall back to global
        entry = None
        if region_key and region_key in NOV_DATA.get("by_region", {}):
            entry = NOV_DATA["by_region"][region_key].get(full) or \
                    NOV_DATA["by_region"][region_key].get(base)
        if not entry:
            entry = NOV_DATA.get("global", {}).get(full) or \
                    NOV_DATA.get("global", {}).get(base)

        if not entry:
            continue

        total = entry["total_novs"]
        for co in entry["co_occurs"]:
            co_cite = co["citation"]
            if co_cite in seen_co:
                continue
            seen_co.add(co_cite)
            pct = int(co["rate"] * 100)
            ctx = f"Region {region_key}" if region_key else "statewide"
            lines.append(
                f"- §{cite} violations co-occur with §{co_cite} in "
                f"{pct}% of {ctx} NOV cases (out of {total} historical NOVs)."
            )

    if not lines:
        return f"[No co-occurrence data found for these citations in {region}]"

    return "\n".join(lines)


def get_tac_text(citations: list) -> str:
    """
    Retrieves TAC 30 Chapter 290 rule text for the given citation codes.
    Looks up the base section number (e.g. '290.109' from '290.109(d)(4)(B)')
    in the loaded JSON knowledge base.

    FULLY WIRED — no changes needed here.
    """
    if not citations:
        return "[No citations specified for this item]"

    results = []
    for cite in citations:
        # Normalize: strip §, spaces, subsection e.g. "290.109(d)(4)(B)" -> "290.109"
        base = cite.replace("§", "").strip().split("(")[0].strip()

        text = TAC_290.get(base)
        if text:
            results.append(f"30 TAC §{cite} (from §{base}):\n{text}")
        else:
            results.append(
                f"30 TAC §{cite}: [Section §{base} not found in knowledge base. "
                f"Available sections: {', '.join(sorted(TAC_290.keys())[:10])}...]"
            )

    return "\n\n---\n\n".join(results)


# ── LAYER 1: PREDICTIVE LLM ───────────────────────────────────────────────────

def run_prediction(failed_items: list, region: str, biz_type: str) -> str:
    """
    LAYER 1 — Predictive element.
    Uses LLM to predict likely additional violation areas based on
    facility profile and observed failures, simulating NOV co-occurrence
    pattern matching.
    """
    items_summary = "\n".join(f"- {i['label']}" for i in failed_items)
    nov_context = get_nov_context(
        [i["id"] for i in failed_items], region, biz_type
    )

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": f"""
You are a predictive model trained on TCEQ public drinking water system enforcement data.

FACILITY PROFILE:
- TCEQ Region: {region}
- System Type: {biz_type}

OBSERVED FAILURES (from field inspection checklist):
{items_summary}

HISTORICAL PATTERN DATA:
{nov_context}

Based on this facility profile and observed failures, predict which additional
violation areas are most likely to also be present, even if not yet confirmed.

For each predicted area:
1. Name the violation area
2. Explain in one sentence why this profile predicts it
3. Rate likelihood: HIGH or MODERATE

Format strictly as:
AREA | LIKELIHOOD | REASONING

Example:
Recordkeeping deficiencies | HIGH | Systems with monitoring failures in Region 4 show recordkeeping violations in 74% of NOV cases, suggesting systemic non-compliance.
"""}]
    )
    return response.content[0].text


def parse_predictions(raw: str) -> list:
    predictions = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            predictions.append({
                "area": parts[0],
                "likelihood": parts[1].upper(),
                "reason": parts[2],
            })
    return predictions


# ── LAYER 2: RAG CITATION GENERATOR ──────────────────────────────────────────

def run_rag(failed_items: list, predictions: list, region: str, biz_type: str) -> str:
    """
    LAYER 2 — RAG citation generator.
    Takes Layer 1 predictions + confirmed failures, retrieves TAC 30
    Chapter 290 rule text from knowledge base, generates specific
    grounded citation recommendations.
    """
    all_cites = list({c for i in failed_items for c in i.get("cites", [])})
    tac_text = get_tac_text(all_cites)

    items_summary = "\n".join(
        f"- {i['label']} (citations: {', '.join(i['cites']) if i['cites'] else 'none listed'})"
        for i in failed_items
    )

    predictions_summary = "\n".join(
        f"- {p['area']} ({p['likelihood']}): {p['reason']}"
        for p in predictions
    ) if predictions else "No predictions available."

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": f"""
You are a regulatory citation assistant for TCEQ public drinking water enforcement.

FACILITY CONTEXT:
- TCEQ Region: {region}
- System Type: {biz_type}

CONFIRMED FAILED CHECKLIST ITEMS:
{items_summary}

PREDICTED ADDITIONAL VIOLATION AREAS (from predictive layer):
{predictions_summary}

RETRIEVED TAC 30 CHAPTER 290 REGULATORY TEXT:
{tac_text}

Using the confirmed failures AND predicted areas, recommend the 3-5 most
applicable TAC 30 Chapter 290 citation codes.

Rules:
- Only cite sections supported by the regulatory text provided above
- Do not hallucinate citations not present in the text
- Note if a citation is driven by confirmed failure vs prediction
- Include the subsection where applicable (e.g. §290.46(m) not just §290.46)

Format strictly as:
CODE | HIGH or MODERATE | REASONING

Example:
§290.46(m) | HIGH | Confirmed recordkeeping failure directly triggers this citation — records must be retained and available for inspection under §290.46(m).
§290.109 | MODERATE | Predicted microbial risk pattern — verify most recent bacteriological sample submissions before citing.
"""}]
    )
    return response.content[0].text


def parse_suggestions(raw: str) -> list:
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
    st.session_state.results = {}
if "accepted" not in st.session_state:
    st.session_state.accepted = []
if "prediction_cache" not in st.session_state:
    st.session_state.prediction_cache = {}
if "suggestions_cache" not in st.session_state:
    st.session_state.suggestions_cache = {}


# ── CALLBACKS ─────────────────────────────────────────────────────────────────

def set_result(item_id, value):
    st.session_state.results[item_id] = value

def accept_suggestion(code):
    if code not in st.session_state.accepted:
        st.session_state.accepted.append(code)

def accept_all_suggestions(codes):
    for code in codes:
        if code not in st.session_state.accepted:
            st.session_state.accepted.append(code)

def remove_accepted(code):
    if code in st.session_state.accepted:
        st.session_state.accepted.remove(code)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Knowledge base status indicator
    kb_status = f"{len(TAC_290)} sections loaded" if TAC_290 else "NOT LOADED"
    kb_color = "#2e7d32" if TAC_290 else "#c0392b"
    st.markdown(
        f'<div style="font-size:0.7rem;color:{kb_color};margin-bottom:8px">'
        f'📚 Knowledge base: {kb_status}</div>',
        unsafe_allow_html=True
    )

    st.markdown("### AI Violation Suggestions")

    region = st.selectbox("TCEQ Region", ["— Select —"] + TCEQ_REGIONS)
    biz_type = st.selectbox("System Type", ["— Select —"] + BUSINESS_TYPES)
    context_set = region != "— Select —" and biz_type != "— Select —"

    st.divider()

    failed_items = [
        item
        for section in CHECKLIST
        for item in section["items"]
        if st.session_state.results.get(item["id"]) == "fail"
    ]

    if not failed_items:
        st.caption("Mark any checklist item as **Fail** to see suggestions.")
    else:
        if not context_set:
            st.warning("Select Region and System Type above to enable suggestions.")
        else:
            cache_key = (
                tuple(i["id"] for i in failed_items),
                region,
                biz_type,
            )

            if st.button("Get suggestions", type="primary", use_container_width=True):
                with st.spinner("Layer 1: Predicting violation patterns..."):
                    raw_pred = run_prediction(failed_items, region, biz_type)
                    predictions = parse_predictions(raw_pred)
                    st.session_state.prediction_cache[cache_key] = predictions

                with st.spinner("Layer 2: Retrieving citation guidance..."):
                    raw_sugg = run_rag(failed_items, predictions, region, biz_type)
                    st.session_state.suggestions_cache[cache_key] = parse_suggestions(raw_sugg)

            predictions = st.session_state.prediction_cache.get(cache_key, [])
            suggestions = st.session_state.suggestions_cache.get(cache_key, [])

            # Layer 1 output
            if predictions:
                st.markdown('<div class="layer-label layer-1">⬡ Layer 1 · Predictive</div>',
                            unsafe_allow_html=True)
                for p in predictions:
                    conf_color = "#c0392b" if "HIGH" in p["likelihood"] else "#e67e22"
                    st.markdown(
                        f'<div class="predict-box">'
                        f'<div class="predict-label">{p["area"]}'
                        f' <span style="color:{conf_color}">{p["likelihood"]}</span></div>'
                        f'<div class="predict-text">{p["reason"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                st.divider()

            # Layer 2 output
            if suggestions:
                st.markdown(
                    '<div class="layer-label layer-2">⬡ Layer 2 · RAG Citations'
                    '<span class="kb-badge">TAC 290</span></div>',
                    unsafe_allow_html=True
                )
                st.caption(
                    f"{len(failed_items)} failure(s) · "
                    f"{region.split('–')[0].strip()} · {biz_type}"
                )

                all_unaccepted = [s["code"] for s in suggestions
                                  if s["code"] not in st.session_state.accepted]

                for i, s in enumerate(suggestions):
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
                            key=f"accept_{s['code']}_{i}",
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

    # Accepted violations
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

    # Manual entry
    st.markdown("**Add Code Manually**")
    mc1, mc2 = st.columns([3, 1])
    with mc1:
        manual_input = st.text_input(
            "Code",
            placeholder="290.46(m)",
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

st.header("TCEQ · Public Drinking Water System Inspection Checklist")

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
