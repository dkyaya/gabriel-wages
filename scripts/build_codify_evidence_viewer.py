"""
build_codify_evidence_viewer.py — build/append the durable GABRIEL codify
evidence layer and regenerate the local, PI-facing HTML excerpt browser.

Purpose: a safe, repeatable, offline transform. Reads an already-produced
codify pilot output CSV (e.g. docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv,
produced by scripts/gabriel_codify_pilot.py's --live run) and:

1. Writes/appends a durable, append-friendly evidence table
   (docs/analysis/gabriel_codify_evidence_layer.csv) with a stable
   evidence_id per row, plus plain-English label columns (state/city/
   occupation/source-role/attribute/evidence-status/grounding labels,
   a human-readable contract label derived from data/contracts.csv, and a
   short template-based "what this excerpt shows" explanation).
2. Regenerates a self-contained, static, PI-facing HTML excerpt browser with
   plain-English labels, an attribute glossary, cascading filters, and no
   external CDN/JS/CSS dependencies. Writes BOTH a dated archival copy and a
   stable ..._latest.html copy meant for sharing.

Label maps (state/occupation/source-role/attribute/etc.) are defined once in
this file and are NOT Texas/Ohio-specific -- they already include
Massachusetts, so a future MA codify run's output CSV can be fed through the
same pipeline without further code changes. See
docs/analysis/gabriel_codify_viewer_overhaul_plan_2026-07-09.md.

SAFETY MODEL:
  - No network calls of any kind. No gabriel import. No credential read.
  - Never edits data/contracts.csv, data/city_coverage.csv, or corpus/
    (data/contracts.csv is read ONLY, to derive human-readable contract
    labels -- never written to).
  - Only reads the codify output CSV given by --input (plus data/contracts.csv
    for labeling) and writes the files given by --evidence-out / --html-out /
    --html-latest-out.

Usage:
  python scripts/build_codify_evidence_viewer.py
  python scripts/build_codify_evidence_viewer.py --input <csv> --evidence-out <csv> --html-out <html> --html-latest-out <html>
"""

from __future__ import annotations

import argparse
import csv
import html as html_module
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "docs" / "analysis" / "gabriel_codify_full_codebook_outputs_2026-07-09.csv"
DEFAULT_EVIDENCE_OUT = ROOT / "docs" / "analysis" / "gabriel_codify_evidence_layer.csv"
DEFAULT_HTML_OUT = ROOT / "docs" / "analysis" / "gabriel_codify_excerpt_browser_2026-07-09.html"
DEFAULT_HTML_LATEST_OUT = ROOT / "docs" / "analysis" / "gabriel_codify_excerpt_browser_latest.html"
CONTRACTS_CSV = ROOT / "data" / "contracts.csv"

EVIDENCE_FIELDNAMES = [
    "evidence_id", "run_id", "run_date", "source_output_file", "contract_id", "state",
    "city", "occupation_class", "source_role", "attribute", "evidence_status", "excerpt",
    "excerpt_location", "source_file", "source_grounding_status", "raw_output_ref", "notes",
    # Plain-English / PI-facing additions (Task B/C/D):
    "state_label", "city_label", "occupation_label", "source_role_label", "contract_label",
    "attribute_label", "attribute_definition", "evidence_status_label", "source_grounding_label",
    "what_excerpt_shows",
]

ALLOWED_EVIDENCE_STATUS = {"present", "not_found", "unclear"}
ALLOWED_GROUNDING_STATUS = {"grounded", "unsupported", "unclear", "not_applicable"}

RUN_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")

# ---------------------------------------------------------------------------
# Plain-English label maps (Task B). Keys are lowercased for case-insensitive
# lookup, since data/contracts.csv and codify outputs use "TX"/"OH"/"MA" while
# these maps are written lowercase per the task spec. NOT Texas/Ohio-specific:
# Massachusetts is included now so a future MA codify run needs no code
# changes here.
# ---------------------------------------------------------------------------

STATE_LABELS = {
    "ma": "Massachusetts",
    "tx": "Texas",
    "oh": "Ohio",
}

OCCUPATION_LABELS = {
    "police": "Police",
    "fire": "Fire",
    "teacher": "Teachers / school employees",
    "sanitation": "Sanitation / solid waste",
    "clerical_admin": "Clerical / administrative",
    "public_works": "Public works / DPW",
    "transit": "Transit",
    "parks_rec": "Parks / recreation",
    "library": "Library",
    "nurse_health": "Health / EMS / nurse-health",
    "other": "Other / mixed municipal",
}

SOURCE_ROLE_LABELS = {
    "police": "Police",
    "fire": "Fire",
    "non_safety_general": "General non-safety",
    "budget_pay_plan": "Budget / pay plan",
    "legal_institutional": "Legal / institutional context",
    "source_discovery": "Source discovery",
    "other": "Other",
}

EVIDENCE_STATUS_LABELS = {
    "present": "Evidence found",
    "not_found": "No evidence found",
    "unclear": "Unclear",
}

SOURCE_GROUNDING_LABELS = {
    "grounded": "Verified in source text",
    "unsupported": "Not verified in source text",
    "unclear": "Verification unclear",
    "not_applicable": "Not applicable",
}

# source_type values from docs/schema.md's contracts.csv controlled vocabulary
# (cba, arbitration_award, factfinding), used only to build a short,
# non-invented descriptor inside contract_label.
SOURCE_TYPE_LABELS = {
    "cba": "collective bargaining agreement",
    "arbitration_award": "arbitration award",
    "factfinding": "fact-finding report",
}

# Attribute label + plain-English definition (Task B) and a short
# attribute-specific clause used to build the "what this excerpt shows"
# explanation (Task D). Order matches the refined 19-attribute Harvard Proxy
# codebook and is preserved in the glossary / attribute filter.
ATTRIBUTE_INFO = {
    "peer_comparator_wage_comparability": {
        "label": "Peer / comparator wage comparison",
        "definition": (
            "Explicit use of peer cities, comparable communities, external labor markets, "
            "comparator jurisdictions, or comparable bargaining units to justify wage levels, "
            "increases, or schedules."
        ),
        "clause": (
            "it references another city, comparable community, or peer employer as a basis for "
            "wage levels, increases, or schedules -- not a generic claim of \"competitive wages\" alone"
        ),
    },
    "interest_arbitration_or_formal_impasse_backstop": {
        "label": "Interest arbitration / formal impasse backstop",
        "definition": (
            "Wage-setting or successor-contract settlement shaped by formal impasse institutions, "
            "such as interest arbitration, conciliation, factfinding, mediation-to-award processes, "
            "or bargaining in the shadow of formal impasse resolution. Excludes ordinary grievance "
            "arbitration."
        ),
        "clause": (
            "it describes a formal impasse-resolution process (such as interest arbitration, "
            "conciliation, or fact-finding) used to set or settle contract terms -- distinct from "
            "ordinary grievance arbitration"
        ),
    },
    "grievance_or_contract_interpretation_arbitration": {
        "label": "Grievance or contract-interpretation arbitration",
        "definition": (
            "Arbitration used for grievances, discipline, contract interpretation, enforcement, or "
            "disputes under an existing agreement. Excludes interest arbitration over successor "
            "contract terms."
        ),
        "clause": (
            "it describes resolving disputes, discipline, or interpretation issues under an "
            "already-existing agreement -- not the process for setting new contract terms"
        ),
    },
    "staffing_shortage_recruitment_retention": {
        "label": "Staffing shortage, recruitment, or retention",
        "definition": (
            "Explicit concern about vacancies, recruitment, retention, hiring, turnover, staffing "
            "shortages, labor supply, attrition, or inability to fill positions."
        ),
        "clause": "it references vacancies, recruitment, retention, hiring, turnover, or staffing shortages",
    },
    "minimum_staffing_or_continuous_coverage": {
        "label": "Minimum staffing / continuous coverage",
        "definition": (
            "Minimum staffing, required crew levels, continuous coverage, 24/7 service obligations, "
            "station coverage, mandatory coverage, or inability to defer service."
        ),
        "clause": "it describes a minimum staffing level, required crew size, or continuous/24-7 coverage obligation",
    },
    "overtime_callback_holdover_mandatory_extra_work": {
        "label": "Overtime, callback, holdover, or mandatory extra work",
        "definition": (
            "Overtime, callback, holdover, mandatory overtime, court time, extra duty, standby/"
            "on-call, shift extension, or premium compensation for extra work demands."
        ),
        "clause": "it describes overtime, callback, holdover, mandatory extra duty, or standby/on-call pay",
    },
    "classification_reclassification_or_grade_structure": {
        "label": "Classification, reclassification, or wage-grade structure",
        "definition": (
            "Wage setting through classification systems, grades, steps, job titles, "
            "reclassification, compensation studies, wage schedules, or grade appeals."
        ),
        "clause": (
            "it describes how wages are set through job classifications, grades, steps, or a "
            "compensation study -- an internal wage-structure mechanism, not a comparison to peer "
            "or external employers"
        ),
    },
    "training_certification_credential_premiums": {
        "label": "Training, certification, credential, or education premiums",
        "definition": (
            "Wage premiums, stipends, incentives, requirements, or career ladders linked to "
            "training, certifications, degrees, licenses, credentials, or specialist "
            "qualifications."
        ),
        "clause": "it describes a wage premium, stipend, or incentive tied to training, certification, a credential, or a specialist qualification",
    },
    "hazard_risk_stress_or_line_of_duty_rationale": {
        "label": "Hazard, risk, stress, or line-of-duty rationale",
        "definition": (
            "Explicit wage or benefit language tied to hazard, risk, injury, stress, line-of-duty "
            "harm, dangerous conditions, public-safety exposure, or physical/psychological burden."
        ),
        "clause": "it ties wage or benefit language explicitly to hazard, risk, injury, stress, or line-of-duty harm",
    },
    "premium_pay_differentials": {
        "label": "Premium pay / differentials",
        "definition": (
            "Shift differentials, assignment differentials, specialty pay, longevity, night/weekend "
            "pay, holiday premiums, bilingual pay, paramedic pay, detail rates, or other add-ons "
            "beyond base wage."
        ),
        "clause": "it describes a shift differential, specialty pay, longevity pay, or another add-on beyond the base wage",
    },
    "benefits_total_compensation_or_pension": {
        "label": "Benefits, total compensation, or pension",
        "definition": (
            "Health insurance, pension, retirement, deferred compensation, paid leave, uniform "
            "allowance, equipment allowance, or non-wage benefits that affect compensation."
        ),
        "clause": "it describes health insurance, pension, retirement, paid leave, or another non-wage benefit that affects total compensation",
    },
    "subcontracting_outsourcing_or_volunteer_substitution": {
        "label": "Subcontracting, outsourcing, or substitution",
        "definition": (
            "Contracting out, outsourcing, privatization, volunteer substitution, non-unit labor "
            "replacement, civilianization, or restrictions on replacing bargaining-unit work."
        ),
        "clause": "it describes contracting out, outsourcing, privatization, or restrictions on replacing bargaining-unit work with non-unit labor",
    },
    "management_rights_or_service_flexibility": {
        "label": "Management rights / service flexibility",
        "definition": (
            "Management rights to assign, schedule, transfer, reorganize, determine staffing, set "
            "operations, change methods, deploy personnel, or maintain service flexibility."
        ),
        "clause": "it describes management's right to assign, schedule, transfer, or otherwise direct staffing and operations",
    },
    "no_strike_or_work_stoppage_constraint": {
        "label": "No-strike / work-stoppage constraint",
        "definition": (
            "No-strike, no-slowdown, no-lockout, essential-service continuity, or statutory "
            "work-stoppage constraints."
        ),
        "clause": "it describes a no-strike, no-slowdown, or no-lockout commitment, or another work-stoppage constraint",
    },
    "civil_service_or_statutory_employment_channel": {
        "label": "Civil-service or statutory employment channel",
        "definition": (
            "Civil-service provisions, statutory employment protections, meet-and-confer statutes, "
            "Chapter 174/142/146 references, Chapter 4117/SERB references, appointment/promotion "
            "rules, or statutory channels structuring bargaining or wage-setting."
        ),
        "clause": "it references a civil-service provision, a meet-and-confer or collective-bargaining statute, or another statutory channel structuring bargaining or wage-setting",
    },
    "union_security_or_institutional_power": {
        "label": "Union security / institutional power",
        "definition": (
            "Union recognition, dues or agency checkoff, exclusive representation, release time, "
            "union access, bulletin boards, labor-management committees, bargaining rights, or "
            "institutional supports for union power."
        ),
        "clause": "it describes union recognition, dues checkoff, exclusive representation, or another institutional support for union standing",
    },
    "budget_capacity_or_fiscal_constraint": {
        "label": "Budget capacity / fiscal constraint",
        "definition": (
            "Fiscal capacity, budget constraints, ability to pay, appropriations, tax limits, "
            "fiscal emergency, budgetary shortfall, or city financial condition used to shape "
            "wages."
        ),
        "clause": "it references budget constraints, appropriations, ability to pay, or the city's fiscal condition as a factor shaping wages",
    },
    "non_safety_wage_restraint_or_admin_channel": {
        "label": "Non-safety wage restraint / administrative channel",
        "definition": (
            "Evidence that non-safety wages are routed through administrative pay plans, "
            "classification systems, consultation rather than bargaining, weaker impasse "
            "pathways, delayed studies, pay-grade adjustments, or limited wage channels."
        ),
        "clause": "it shows non-safety wages being routed through an administrative pay plan, classification system, or consultation process rather than ordinary collective bargaining",
    },
    "other": {
        "label": "Other wage-mechanism evidence",
        "definition": (
            "Relevant wage-mechanism evidence not captured by the other attributes. Use "
            "sparingly."
        ),
        "clause": "it is relevant wage-mechanism evidence that did not fit the other listed attributes",
    },
}

NOT_FOUND_EXPLANATION = "No excerpt was returned for this attribute in the selected source window."


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                    help="Codify pilot output CSV to read (contract_id x attribute rows).")
    p.add_argument("--evidence-out", type=Path, default=DEFAULT_EVIDENCE_OUT,
                    help="Durable evidence-layer CSV to write/append.")
    p.add_argument("--html-out", type=Path, default=DEFAULT_HTML_OUT,
                    help="Dated archival static HTML excerpt browser to write.")
    p.add_argument("--html-latest-out", type=Path, default=DEFAULT_HTML_LATEST_OUT,
                    help="Stable 'latest' static HTML excerpt browser to write (for sharing).")
    return p.parse_args()


def _read_input_rows(path: Path) -> list[dict]:
    if not path.exists():
        print(f"ERROR: input CSV not found: {path}")
        sys.exit(1)
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _run_date_from_run_id(run_id: str) -> str:
    m = RUN_DATE_RE.match(run_id or "")
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return "unknown-date"


def _source_file_for_contract(contract_id: str, evidence_windows_csvs: list[Path]) -> str:
    """Best-effort lookup of the underlying corpus source_file for a contract_id,
    by checking any evidence-window CSVs already present in docs/analysis/."""
    for path in evidence_windows_csvs:
        if not path.exists():
            continue
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if row.get("contract_id") == contract_id and row.get("source_file"):
                    return row["source_file"]
    return ""


def _load_contracts_metadata(contracts_csv: Path) -> dict[str, dict]:
    """Read-only lookup of data/contracts.csv, keyed by obs_id (contract_id).
    Used ONLY to build human-readable contract labels (Task C) -- never
    written to."""
    metadata: dict[str, dict] = {}
    if not contracts_csv.exists():
        return metadata
    with contracts_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            obs_id = row.get("obs_id")
            if obs_id:
                metadata[obs_id] = row
    return metadata


def _cycle_years(cycle_start: str, cycle_end: str) -> str:
    start_year = (cycle_start or "")[:4]
    end_year = (cycle_end or "")[:4]
    if start_year and end_year and start_year != end_year:
        return f"{start_year}–{end_year}"
    return start_year or end_year or ""


def _label(mapping: dict[str, str], key: str) -> str:
    if not key:
        return ""
    found = mapping.get(key) or mapping.get(key.lower())
    return found if found else key


def _contract_label(contract_id: str, contracts_meta: dict[str, dict],
                     fallback_city: str, fallback_occ: str) -> str:
    """Conservative, data-derived contract label (Task C). Never invents a
    title -- only composes fields that are actually present in
    data/contracts.csv. Falls back to a generic 'City Occupation --
    contract_id' label if the contract isn't found there (e.g. before a
    future MA codify run's contracts have been cross-checked)."""
    meta = contracts_meta.get(contract_id)
    occ_display = _label(OCCUPATION_LABELS, fallback_occ)
    city_display = fallback_city or ""
    if not meta:
        return f"{city_display} {occ_display} — {contract_id}".strip()

    city_name = meta.get("city_name") or city_display
    occ_display = _label(OCCUPATION_LABELS, meta.get("occupation_class") or fallback_occ)
    bargaining_unit = (meta.get("bargaining_unit_name") or "").strip()
    source_type_display = SOURCE_TYPE_LABELS.get(meta.get("source_type", ""), meta.get("source_type", ""))
    years = _cycle_years(meta.get("cycle_start", ""), meta.get("cycle_end", ""))

    descriptor_parts = [p for p in [bargaining_unit, source_type_display] if p]
    descriptor = " ".join(descriptor_parts) if descriptor_parts else contract_id
    label = f"{city_name} {occ_display} — {descriptor}"
    if years:
        label += f", {years}"
    return label


def _what_excerpt_shows(attribute: str, evidence_status: str) -> str:
    """Template-based, non-causal explanation (Task D). No model call."""
    if evidence_status != "present":
        return NOT_FOUND_EXPLANATION
    info = ATTRIBUTE_INFO.get(attribute)
    if not info:
        return "This excerpt was coded under this attribute based on the source text."
    return f"This excerpt was coded as evidence of {info['label']} because {info['clause']}."


def build_evidence_rows(input_rows: list[dict], contracts_meta: dict[str, dict]) -> list[dict]:
    docs_dir = ROOT / "docs" / "analysis"
    evidence_window_csvs = sorted(docs_dir.glob("*evidence_windows*.csv"))
    source_file_cache: dict[str, str] = {}

    sequence_counters: dict[tuple[str, str], int] = {}
    evidence_rows: list[dict] = []

    for row in input_rows:
        evidence_status = (row.get("evidence_status") or "").strip()
        if evidence_status not in ALLOWED_EVIDENCE_STATUS:
            # Keep only present/not_found/unclear semantics; anything else is
            # coerced to not_found rather than silently dropped or invented.
            evidence_status = "not_found"

        contract_id = row.get("contract_id", "")
        attribute = row.get("attribute", "")
        run_id = row.get("run_id", "")
        run_date = _run_date_from_run_id(run_id)
        state = row.get("state", "")
        city = row.get("city", "")
        occupation_class = row.get("occupation_class", "")
        source_role = row.get("source_role", "")

        key = (contract_id, attribute)
        seq = sequence_counters.get(key, 0)
        sequence_counters[key] = seq + 1
        evidence_id = f"codify_{run_date.replace('-', '')}_{contract_id}_{attribute}_{seq}"

        if contract_id not in source_file_cache:
            source_file_cache[contract_id] = _source_file_for_contract(contract_id, evidence_window_csvs)

        grounding = (row.get("source_grounding_status") or "").strip()
        if grounding not in ALLOWED_GROUNDING_STATUS:
            grounding = "not_applicable"

        excerpt = row.get("excerpt", "") if evidence_status == "present" else ""
        if excerpt is None:
            excerpt = ""

        attr_info = ATTRIBUTE_INFO.get(attribute, {})

        evidence_rows.append({
            "evidence_id": evidence_id,
            "run_id": run_id,
            "run_date": run_date,
            "source_output_file": "",  # filled in by write_evidence_csv
            "contract_id": contract_id,
            "state": state,
            "city": city,
            "occupation_class": occupation_class,
            "source_role": source_role,
            "attribute": attribute,
            "evidence_status": evidence_status,
            "excerpt": excerpt,
            "excerpt_location": row.get("excerpt_location", "") or "",
            "source_file": source_file_cache.get(contract_id, ""),
            "source_grounding_status": grounding,
            "raw_output_ref": row.get("raw_output_ref", "") or "",
            "notes": row.get("notes", "") or "",
            "state_label": _label(STATE_LABELS, state),
            "city_label": city,
            "occupation_label": _label(OCCUPATION_LABELS, occupation_class),
            "source_role_label": _label(SOURCE_ROLE_LABELS, source_role),
            "contract_label": _contract_label(contract_id, contracts_meta, city, occupation_class),
            "attribute_label": attr_info.get("label", attribute),
            "attribute_definition": attr_info.get("definition", ""),
            "evidence_status_label": _label(EVIDENCE_STATUS_LABELS, evidence_status),
            "source_grounding_label": _label(SOURCE_GROUNDING_LABELS, grounding),
            "what_excerpt_shows": _what_excerpt_shows(attribute, evidence_status),
        })
    return evidence_rows


def write_evidence_csv(rows: list[dict], out_path: Path, input_path: Path) -> list[dict]:
    # source_output_file is recorded relative to the repo root for portability.
    try:
        rel_input = str(input_path.resolve().relative_to(ROOT))
    except ValueError:
        rel_input = str(input_path)
    for r in rows:
        r["source_output_file"] = rel_input

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EVIDENCE_FIELDNAMES)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Parse back immediately and validate.
    with out_path.open(newline="") as f:
        parsed = list(csv.DictReader(f))

    assert len(parsed) == len(rows), "row count mismatch after write/reparse"
    seen_ids = set()
    for i, row in enumerate(parsed):
        if set(row.keys()) != set(EVIDENCE_FIELDNAMES):
            raise ValueError(f"row {i} column mismatch: {set(row.keys())}")
        if row["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
            raise ValueError(f"row {i} bad evidence_status: {row['evidence_status']!r}")
        if row["source_grounding_status"] not in ALLOWED_GROUNDING_STATUS:
            raise ValueError(f"row {i} bad source_grounding_status: {row['source_grounding_status']!r}")
        if row["evidence_status"] == "present" and not row["excerpt"].strip():
            raise ValueError(f"row {i} ({row['evidence_id']}) is present but has a blank excerpt")
        eid = row["evidence_id"]
        if eid in seen_ids:
            raise ValueError(f"duplicate evidence_id: {eid!r}")
        seen_ids.add(eid)

    return parsed


# ---------------------------------------------------------------------------
# HTML browser generation (Task E)
# ---------------------------------------------------------------------------

def build_html_doc(rows: list[dict]) -> str:
    data_json = json.dumps(rows, ensure_ascii=False)
    attributes_json = json.dumps(
        [{"code": code, "label": info["label"], "definition": info["definition"]}
         for code, info in ATTRIBUTE_INFO.items()],
        ensure_ascii=False,
    )
    total = len(rows)
    present = sum(1 for r in rows if r["evidence_status"] == "present")
    not_found = total - present
    verified_present = sum(
        1 for r in rows if r["evidence_status"] == "present" and r["source_grounding_status"] == "grounded"
    )

    return HTML_TEMPLATE.format(
        data_json=data_json,
        attributes_json=attributes_json,
        total=total,
        present=present,
        not_found=not_found,
        verified_present=verified_present,
    )


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Wage-Mechanism Evidence Browser</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --bg: #0f1216; --panel: #171b21; --panel2: #1e2430; --text: #e8ecf1; --muted: #9aa5b1;
    --accent: #4fc3f7; --present: #2e7d32; --present-bg: #163a1a; --absent: #6b7280;
    --border: #2a3140; --mark: #ffd54f; --mark-text: #241c00; --warn-bg: #3a2a12; --warn-text: #ffcf86;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #f5f7fa; --panel: #ffffff; --panel2: #eef1f6; --text: #1a1f27; --muted: #5b6472;
      --accent: #0277bd; --present: #2e7d32; --present-bg: #e3f4e5; --absent: #9aa5b1;
      --border: #d7dde5; --mark: #ffe082; --mark-text: #241c00; --warn-bg: #fff3e0; --warn-text: #8a4b00;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.5;
  }}
  header {{ padding: 16px 20px; border-bottom: 1px solid var(--border); background: var(--panel); }}
  header h1 {{ margin: 0 0 4px 0; font-size: 21px; }}
  header p.subtitle {{ margin: 0; color: var(--muted); font-size: 13px; }}
  .warning-banner {{
    margin-top: 10px; background: var(--warn-bg); color: var(--warn-text); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 12px; font-size: 13px; font-weight: 600;
  }}
  details.howto {{ margin-top: 10px; background: var(--panel2); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; }}
  details.howto summary {{ cursor: pointer; font-weight: 600; font-size: 13px; }}
  details.howto ul {{ margin: 8px 0 4px 18px; font-size: 13px; color: var(--muted); }}
  details.howto li {{ margin-bottom: 4px; }}

  .layout {{ display: flex; gap: 0; min-height: calc(100vh - 150px); }}
  .sidebar {{
    width: 300px; flex-shrink: 0; padding: 16px; border-right: 1px solid var(--border);
    background: var(--panel); overflow-y: auto; max-height: calc(100vh - 150px);
  }}
  .sidebar h2 {{ font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 14px 0 6px; }}
  .sidebar h2:first-child {{ margin-top: 0; }}
  .sidebar label {{ display: block; font-size: 13px; margin-bottom: 8px; }}
  .sidebar select, .sidebar input[type="text"] {{
    width: 100%; padding: 6px 8px; margin-top: 3px; background: var(--panel2); color: var(--text);
    border: 1px solid var(--border); border-radius: 6px; font-size: 13px;
  }}
  .sidebar .checkbox-row {{ display: flex; align-items: center; gap: 6px; font-size: 13px; margin-bottom: 8px; }}
  .sidebar .checkbox-row input {{ margin: 0; }}
  .counts {{ background: var(--panel2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; font-size: 13px; }}
  .counts div {{ display: flex; justify-content: space-between; padding: 2px 0; }}
  .counts .num {{ font-weight: 700; }}
  button.reset {{ margin-top: 10px; width: 100%; padding: 7px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--panel2); color: var(--text); cursor: pointer; font-size: 12px; }}
  button.reset:hover {{ border-color: var(--accent); }}

  details.glossary {{ margin-top: 8px; }}
  details.glossary summary {{ cursor: pointer; font-size: 13px; font-weight: 600; padding: 4px 0; }}
  .glossary-item {{ margin: 8px 0; padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
  .glossary-item .g-label {{ font-size: 12.5px; font-weight: 700; color: var(--accent); }}
  .glossary-item .g-def {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}

  .main {{ flex: 1; padding: 16px 20px; overflow-y: auto; max-height: calc(100vh - 150px); }}
  .viewmode-tabs {{ display: flex; gap: 8px; margin-bottom: 14px; }}
  .viewmode-tabs button {{
    padding: 6px 14px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel);
    color: var(--text); cursor: pointer; font-size: 13px;
  }}
  .viewmode-tabs button.active {{ background: var(--accent); color: #001018; border-color: var(--accent); font-weight: 700; }}

  .nav-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }}
  .nav-row button {{
    padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border); background: var(--panel);
    color: var(--text); cursor: pointer; font-size: 13px;
  }}
  .nav-row button:disabled {{ opacity: .4; cursor: default; }}
  .nav-row .position {{ font-size: 13px; color: var(--muted); }}

  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 18px;
    margin-bottom: 14px;
  }}
  .card .attr-badge {{
    display: inline-block; background: var(--accent); color: #001018; font-weight: 700; font-size: 13px;
    padding: 4px 12px; border-radius: 999px; margin-bottom: 10px; letter-spacing: .01em;
  }}
  .card .status-badge {{ display: inline-block; font-size: 11.5px; padding: 2px 9px; border-radius: 999px; margin-left: 8px; font-weight: 600; }}
  .card .status-present {{ background: var(--present-bg); color: var(--present); }}
  .card .status-not_found {{ background: transparent; color: var(--absent); border: 1px solid var(--border); }}
  .card .verify-badge {{ display: inline-block; font-size: 11.5px; padding: 2px 9px; border-radius: 999px; margin-left: 6px; border: 1px solid var(--accent); color: var(--accent); }}
  .card h3.contract-title {{ margin: 6px 0 2px; font-size: 16px; }}
  .card .place-line {{ font-size: 12.5px; color: var(--muted); margin-bottom: 10px; }}
  .card .excerpt {{ font-size: 15.5px; margin: 12px 0; padding: 10px 12px; background: var(--panel2); border-radius: 8px; border-left: 3px solid var(--accent); }}
  .card .excerpt mark {{ background: var(--mark); color: var(--mark-text); padding: 1px 3px; border-radius: 3px; }}
  .card .excerpt.empty {{ color: var(--muted); font-style: italic; background: transparent; border-left-color: var(--border); }}
  .card .explain {{ font-size: 13.5px; color: var(--text); background: transparent; margin: 8px 0; }}
  .card .explain b {{ color: var(--muted); font-weight: 600; }}
  .card .causal-note {{ font-size: 12px; color: var(--muted); font-style: italic; margin: 4px 0 10px; }}
  .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 6px 16px; font-size: 12.5px; color: var(--muted); margin-top: 10px; }}
  .meta-grid b {{ color: var(--text); }}
  .card .notes {{ margin-top: 8px; font-size: 12.5px; color: var(--muted); }}
  .card .copy-row {{ display: flex; gap: 8px; margin: 10px 0; }}
  .card .copy-row button {{
    padding: 5px 12px; font-size: 12px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--panel2); color: var(--text); cursor: pointer;
  }}
  .card .copy-row button:hover {{ border-color: var(--accent); }}
  .card .copy-row button.copied {{ border-color: var(--present); color: var(--present); }}
  details.tech {{ margin-top: 10px; border-top: 1px solid var(--border); padding-top: 8px; }}
  details.tech summary {{ cursor: pointer; font-size: 11.5px; color: var(--muted); }}
  details.tech .tech-grid {{ margin-top: 8px; font-size: 11.5px; color: var(--muted); display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 4px 14px; }}
  details.tech code {{ color: var(--text); }}

  table.evidence-table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
  table.evidence-table th, table.evidence-table td {{ border: 1px solid var(--border); padding: 6px 8px; text-align: left; vertical-align: top; }}
  table.evidence-table th {{ background: var(--panel2); position: sticky; top: 0; }}
  table.evidence-table tr:hover {{ background: var(--panel2); }}
  .pill {{ display: inline-block; font-size: 11px; padding: 1px 7px; border-radius: 999px; }}
  .pill.present {{ background: var(--present-bg); color: var(--present); }}
  .pill.not_found {{ background: transparent; color: var(--absent); border: 1px solid var(--border); }}

  .empty-state {{ color: var(--muted); padding: 40px; text-align: center; }}
  ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 6px; }}
</style>
</head>
<body>

<header>
  <h1>Wage-Mechanism Evidence Browser</h1>
  <p class="subtitle">A source-grounded evidence browser for this project's public-safety wage-mechanism research. Local, static, self-contained -- no server, no external libraries, no network calls.</p>
  <div class="warning-banner">These excerpts show evidence that a wage-setting mechanism is discussed in the source text. They do not, by themselves, prove any wage or causal effect.</div>
  <details class="howto">
    <summary>How to use this viewer</summary>
    <ul>
      <li><b>Filters (left sidebar)</b> narrow the evidence shown. Filters cascade: choosing a state narrows the city list, choosing a city narrows the contract list, and so on. Options that would produce zero results are removed automatically.</li>
      <li>The <b>attribute (mechanism)</b> filter defaults to showing only mechanisms with evidence found in the current selection. Toggle "Show mechanisms with no evidence" to see the full list.</li>
      <li>By default only <b>evidence found</b> rows are shown; toggle "Show 'no evidence found' rows" to include absence rows too.</li>
      <li>Switch between <b>Cards</b> (one piece of evidence at a time, with Prev/Next navigation) and <b>Table</b> (compact, all filtered rows at once).</li>
      <li>Highlighted (<mark>yellow</mark>) text inside a card is the exact verbatim excerpt identified in the source document.</li>
      <li><b>"Verified in source text"</b> means the excerpt was checked and really does appear in the underlying source window -- a text-integrity check, not a judgment about what the excerpt means or proves.</li>
      <li>Use the <b>attribute glossary</b> in the sidebar to see plain-English definitions for every mechanism.</li>
      <li>Each card has <b>Copy excerpt</b> and <b>Copy citation</b> buttons, and a "Technical details" section with the underlying IDs/codes for anyone who needs them.</li>
    </ul>
  </details>
</header>

<div class="layout">
  <aside class="sidebar">
    <h2>Filters</h2>
    <label>State
      <select id="f-state"><option value="">All states</option></select>
    </label>
    <label>City
      <select id="f-city"><option value="">All cities</option></select>
    </label>
    <label>Contract / source
      <select id="f-contract"><option value="">All contracts</option></select>
    </label>
    <label>Occupation
      <select id="f-occ"><option value="">All occupations</option></select>
    </label>
    <label>Source role
      <select id="f-role"><option value="">All source roles</option></select>
    </label>
    <label>Mechanism (attribute)
      <select id="f-attr"><option value="">All mechanisms</option></select>
    </label>
    <div class="checkbox-row">
      <input type="checkbox" id="f-showallattrs">
      <label for="f-showallattrs" style="margin:0;">Show mechanisms with no evidence</label>
    </div>
    <label>Evidence status
      <select id="f-status"><option value="">All</option></select>
    </label>
    <label>Source verification
      <select id="f-ground"><option value="">All</option></select>
    </label>
    <label>Search excerpt / notes
      <input type="text" id="f-search" placeholder="e.g. arbitration, uniform allowance">
    </label>
    <div class="checkbox-row">
      <input type="checkbox" id="f-shownotfound">
      <label for="f-shownotfound" style="margin:0;">Show "no evidence found" rows</label>
    </div>
    <button class="reset" id="reset-filters">Reset filters</button>

    <h2>Counts</h2>
    <div class="counts">
      <div><span>Total rows</span><span class="num" id="c-total">{total}</span></div>
      <div><span>Evidence found</span><span class="num" id="c-present">{present}</span></div>
      <div><span>No evidence found</span><span class="num" id="c-notfound">{not_found}</span></div>
      <div><span>Verified present</span><span class="num" id="c-verified">{verified_present}</span></div>
      <div><span>Currently shown</span><span class="num" id="c-selected">0</span></div>
    </div>

    <h2>Mechanism glossary</h2>
    <details class="glossary">
      <summary>Show all 19 mechanism definitions</summary>
      <div id="glossary-list"></div>
    </details>
  </aside>

  <main class="main">
    <div class="viewmode-tabs">
      <button id="tab-cards" class="active">Cards</button>
      <button id="tab-table">Table</button>
    </div>

    <div id="cards-view">
      <div class="nav-row">
        <button id="nav-prev">&larr; Prev</button>
        <span class="position" id="nav-position">0 / 0</span>
        <button id="nav-next">Next &rarr;</button>
      </div>
      <div id="card-container"><div class="empty-state">No rows match the current filters.</div></div>
    </div>

    <div id="table-view" style="display:none;">
      <div style="overflow-x:auto;">
        <table class="evidence-table" id="evidence-table">
          <thead>
            <tr>
              <th>State</th><th>City</th><th>Contract</th><th>Occupation</th>
              <th>Mechanism</th><th>Status</th><th>Excerpt</th><th>Verification</th>
            </tr>
          </thead>
          <tbody id="table-body"></tbody>
        </table>
      </div>
    </div>
  </main>
</div>

<script>
const EVIDENCE = {data_json};
const ATTRIBUTES = {attributes_json};
const ATTR_INFO = {{}};
ATTRIBUTES.forEach(a => {{ ATTR_INFO[a.code] = a; }});

let filtered = [];
let cardIndex = 0;

function esc(s) {{
  if (s === undefined || s === null) return "";
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}}

function highlightExcerpt(text) {{
  if (!text) return "";
  return "<mark>" + esc(text) + "</mark>";
}}

function currentSelections() {{
  return {{
    state: document.getElementById("f-state").value,
    city: document.getElementById("f-city").value,
    contract: document.getElementById("f-contract").value,
    occ: document.getElementById("f-occ").value,
    role: document.getElementById("f-role").value,
    attr: document.getElementById("f-attr").value,
    status: document.getElementById("f-status").value,
    ground: document.getElementById("f-ground").value,
    search: document.getElementById("f-search").value.trim().toLowerCase(),
    showNotFound: document.getElementById("f-shownotfound").checked,
    showAllAttrs: document.getElementById("f-showallattrs").checked,
  }};
}}

// Faceted / cascading filters: for each dropdown, its OPTIONS are computed
// from rows matching every OTHER currently-selected filter (not itself), so
// picking a state narrows city options, picking a city narrows contract
// options, and so on -- in any order, symmetrically.
function rowsMatchingExcept(sel, exceptKey) {{
  return EVIDENCE.filter(r => {{
    if (exceptKey !== "state" && sel.state && r.state !== sel.state) return false;
    if (exceptKey !== "city" && sel.city && r.city !== sel.city) return false;
    if (exceptKey !== "contract" && sel.contract && r.contract_id !== sel.contract) return false;
    if (exceptKey !== "occ" && sel.occ && r.occupation_class !== sel.occ) return false;
    if (exceptKey !== "role" && sel.role && r.source_role !== sel.role) return false;
    if (exceptKey !== "attr" && sel.attr && r.attribute !== sel.attr) return false;
    return true;
  }});
}}

function rebuildSelectOptions(id, key, rows, labelKey, currentValue) {{
  const sel = document.getElementById(id);
  const seen = new Map();
  rows.forEach(r => {{
    const v = r[key];
    if (v !== undefined && v !== null && v !== "" && !seen.has(v)) {{
      seen.set(v, r[labelKey] || v);
    }}
  }});
  const entries = Array.from(seen.entries()).sort((a, b) => a[1].localeCompare(b[1]));
  const placeholder = sel.options[0]; // keep the "All ..." option
  sel.innerHTML = "";
  sel.appendChild(placeholder);
  entries.forEach(([value, label]) => {{
    const opt = document.createElement("option");
    opt.value = value; opt.textContent = label;
    sel.appendChild(opt);
  }});
  // Preserve the current selection only if it is still a valid option.
  if (currentValue && seen.has(currentValue)) {{
    sel.value = currentValue;
  }} else {{
    sel.value = "";
  }}
}}

function rebuildAttributeOptions(sel) {{
  const rows = rowsMatchingExcept(sel, "attr");
  const attrSelect = document.getElementById("f-attr");
  const presentAttrs = new Set(rows.filter(r => r.evidence_status === "present").map(r => r.attribute));
  const allAttrsInScope = new Set(rows.map(r => r.attribute));
  const pool = sel.showAllAttrs ? allAttrsInScope : presentAttrs;

  const entries = ATTRIBUTES
    .filter(a => pool.has(a.code))
    .map(a => [a.code, a.label])
    .sort((a, b) => a[1].localeCompare(b[1]));

  const placeholder = attrSelect.options[0];
  attrSelect.innerHTML = "";
  attrSelect.appendChild(placeholder);
  entries.forEach(([code, label]) => {{
    const opt = document.createElement("option");
    opt.value = code; opt.textContent = label;
    attrSelect.appendChild(opt);
  }});
  if (sel.attr && pool.has(sel.attr)) {{
    attrSelect.value = sel.attr;
  }} else {{
    attrSelect.value = "";
  }}
}}

function rebuildCascadingFilters() {{
  const sel = currentSelections();
  rebuildSelectOptions("f-state", "state", rowsMatchingExcept(sel, "state"), "state_label", sel.state);
  rebuildSelectOptions("f-city", "city", rowsMatchingExcept(sel, "city"), "city_label", sel.city);
  rebuildSelectOptions("f-contract", "contract_id", rowsMatchingExcept(sel, "contract"), "contract_label", sel.contract);
  rebuildSelectOptions("f-occ", "occupation_class", rowsMatchingExcept(sel, "occ"), "occupation_label", sel.occ);
  rebuildSelectOptions("f-role", "source_role", rowsMatchingExcept(sel, "role"), "source_role_label", sel.role);
  rebuildAttributeOptions(sel);
}}

function applyFilters() {{
  rebuildCascadingFilters();
  const sel = currentSelections();

  filtered = EVIDENCE.filter(r => {{
    if (sel.state && r.state !== sel.state) return false;
    if (sel.city && r.city !== sel.city) return false;
    if (sel.contract && r.contract_id !== sel.contract) return false;
    if (sel.occ && r.occupation_class !== sel.occ) return false;
    if (sel.role && r.source_role !== sel.role) return false;
    if (sel.attr && r.attribute !== sel.attr) return false;
    if (sel.status && r.evidence_status !== sel.status) return false;
    if (sel.ground && r.source_grounding_status !== sel.ground) return false;
    if (!sel.status && !sel.showNotFound && r.evidence_status === "not_found") return false;
    if (sel.search) {{
      const hay = ((r.excerpt || "") + " " + (r.notes || "") + " " + (r.what_excerpt_shows || "")).toLowerCase();
      if (!hay.includes(sel.search)) return false;
    }}
    return true;
  }});

  // Default sort: state -> city -> contract -> attribute (plain-English labels).
  filtered.sort((a, b) => {{
    return (a.state_label || "").localeCompare(b.state_label || "")
      || (a.city_label || "").localeCompare(b.city_label || "")
      || (a.contract_label || "").localeCompare(b.contract_label || "")
      || (a.attribute_label || "").localeCompare(b.attribute_label || "");
  }});

  document.getElementById("c-selected").textContent = filtered.length;
  cardIndex = 0;
  renderCards();
  renderTable();
}}

function copyToClipboard(text, btn) {{
  function markCopied() {{
    if (!btn) return;
    const original = btn.textContent;
    btn.textContent = "Copied";
    btn.classList.add("copied");
    setTimeout(() => {{ btn.textContent = original; btn.classList.remove("copied"); }}, 1400);
  }}
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(text).then(markCopied).catch(() => fallbackCopy(text, markCopied));
  }} else {{
    fallbackCopy(text, markCopied);
  }}
}}

function fallbackCopy(text, onDone) {{
  // Works over file:// where navigator.clipboard may be restricted.
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try {{ document.execCommand("copy"); }} catch (e) {{ /* no-op */ }}
  document.body.removeChild(ta);
  if (onDone) onDone();
}}

function renderCards() {{
  const container = document.getElementById("card-container");
  const posEl = document.getElementById("nav-position");
  if (!filtered.length) {{
    container.innerHTML = "<div class='empty-state'>No rows match the current filters.</div>";
    posEl.textContent = "0 / 0";
    document.getElementById("nav-prev").disabled = true;
    document.getElementById("nav-next").disabled = true;
    return;
  }}
  if (cardIndex < 0) cardIndex = filtered.length - 1;
  if (cardIndex >= filtered.length) cardIndex = 0;
  const r = filtered[cardIndex];
  posEl.textContent = (cardIndex + 1) + " / " + filtered.length;
  document.getElementById("nav-prev").disabled = filtered.length <= 1;
  document.getElementById("nav-next").disabled = filtered.length <= 1;

  const isPresent = r.evidence_status === "present";
  const excerptHtml = isPresent && r.excerpt
    ? "<div class='excerpt'>" + highlightExcerpt(r.excerpt) + "</div>"
    : "<div class='excerpt empty'>No excerpt (no evidence found for this mechanism in this source window).</div>";

  const attrDef = (ATTR_INFO[r.attribute] || {{}}).definition || r.attribute_definition || "";

  const citation = r.contract_label + " \\u2014 " + r.attribute_label
    + (r.excerpt ? (": \\u201c" + r.excerpt + "\\u201d") : "")
    + " (source: " + (r.source_file || "n/a") + (r.excerpt_location ? ", " + r.excerpt_location : "") + ")"
    + " [" + r.source_grounding_label + "]";

  container.innerHTML = `
    <div class="card">
      <span class="attr-badge">${{esc(r.attribute_label)}}</span>
      <span class="status-badge status-${{esc(r.evidence_status)}}">${{esc(r.evidence_status_label)}}</span>
      ${{isPresent ? "<span class='verify-badge'>" + esc(r.source_grounding_label) + "</span>" : ""}}
      <h3 class="contract-title">${{esc(r.contract_label)}}</h3>
      <div class="place-line">${{esc(r.state_label)}} &middot; ${{esc(r.city_label)}} &middot; ${{esc(r.occupation_label)}} &middot; ${{esc(r.source_role_label)}} source</div>
      <div class="explain"><b>Mechanism definition:</b> ${{esc(attrDef)}}</div>
      ${{excerptHtml}}
      <div class="explain"><b>What this excerpt shows:</b> ${{esc(r.what_excerpt_shows)}}</div>
      ${{isPresent ? "<div class='causal-note'>Reminder: this shows the mechanism is discussed in the source text -- it does not by itself establish a wage or causal effect.</div>" : ""}}
      ${{isPresent ? `<div class="copy-row">
        <button class="copy-excerpt-btn">Copy excerpt</button>
        <button class="copy-citation-btn">Copy citation</button>
      </div>` : ""}}
      <div class="meta-grid">
        <div><b>Source file</b><br>${{esc(r.source_file) || "&mdash;"}}</div>
        <div><b>Excerpt location</b><br>${{esc(r.excerpt_location) || "&mdash;"}}</div>
      </div>
      ${{r.notes ? "<div class='notes'><b>Notes:</b> " + esc(r.notes) + "</div>" : ""}}
      <details class="tech">
        <summary>Technical details</summary>
        <div class="tech-grid">
          <div>contract_id: <code>${{esc(r.contract_id)}}</code></div>
          <div>attribute: <code>${{esc(r.attribute)}}</code></div>
          <div>evidence_status: <code>${{esc(r.evidence_status)}}</code></div>
          <div>source_grounding_status: <code>${{esc(r.source_grounding_status)}}</code></div>
          <div>evidence_id: <code>${{esc(r.evidence_id)}}</code></div>
          <div>run: <code>${{esc(r.run_id)}}</code> (${{esc(r.run_date)}})</div>
        </div>
      </details>
    </div>
  `;

  const copyExcerptBtn = container.querySelector(".copy-excerpt-btn");
  if (copyExcerptBtn) {{
    copyExcerptBtn.addEventListener("click", () => copyToClipboard(r.excerpt || "", copyExcerptBtn));
  }}
  const copyCitationBtn = container.querySelector(".copy-citation-btn");
  if (copyCitationBtn) {{
    copyCitationBtn.addEventListener("click", () => copyToClipboard(citation, copyCitationBtn));
  }}
}}

function renderTable() {{
  const tbody = document.getElementById("table-body");
  if (!filtered.length) {{
    tbody.innerHTML = "<tr><td colspan='8' class='empty-state'>No rows match the current filters.</td></tr>";
    return;
  }}
  tbody.innerHTML = filtered.map(r => `
    <tr>
      <td>${{esc(r.state_label)}}</td>
      <td>${{esc(r.city_label)}}</td>
      <td>${{esc(r.contract_label)}}</td>
      <td>${{esc(r.occupation_label)}}</td>
      <td>${{esc(r.attribute_label)}}</td>
      <td><span class="pill ${{esc(r.evidence_status)}}">${{esc(r.evidence_status_label)}}</span></td>
      <td>${{esc((r.excerpt || "").slice(0, 140))}}${{(r.excerpt || "").length > 140 ? "&hellip;" : ""}}</td>
      <td>${{esc(r.source_grounding_label)}}</td>
    </tr>
  `).join("");
}}

function renderGlossary() {{
  const el = document.getElementById("glossary-list");
  el.innerHTML = ATTRIBUTES.map(a => `
    <div class="glossary-item">
      <div class="g-label">${{esc(a.label)}}</div>
      <div class="g-def">${{esc(a.definition)}}</div>
    </div>
  `).join("");
}}

document.querySelectorAll(".sidebar select, #f-search, #f-shownotfound, #f-showallattrs").forEach(el => {{
  el.addEventListener("input", applyFilters);
  el.addEventListener("change", applyFilters);
}});

document.getElementById("reset-filters").addEventListener("click", () => {{
  document.querySelectorAll(".sidebar select").forEach(s => s.value = "");
  document.getElementById("f-search").value = "";
  document.getElementById("f-shownotfound").checked = false;
  document.getElementById("f-showallattrs").checked = false;
  applyFilters();
}});

document.getElementById("nav-prev").addEventListener("click", () => {{ cardIndex--; renderCards(); }});
document.getElementById("nav-next").addEventListener("click", () => {{ cardIndex++; renderCards(); }});

document.getElementById("tab-cards").addEventListener("click", () => {{
  document.getElementById("tab-cards").classList.add("active");
  document.getElementById("tab-table").classList.remove("active");
  document.getElementById("cards-view").style.display = "";
  document.getElementById("table-view").style.display = "none";
}});
document.getElementById("tab-table").addEventListener("click", () => {{
  document.getElementById("tab-table").classList.add("active");
  document.getElementById("tab-cards").classList.remove("active");
  document.getElementById("table-view").style.display = "";
  document.getElementById("cards-view").style.display = "none";
}});

renderGlossary();
applyFilters();
</script>
</body>
</html>
"""


def main() -> None:
    args = _parse_args()
    input_rows = _read_input_rows(args.input)
    contracts_meta = _load_contracts_metadata(CONTRACTS_CSV)
    evidence_rows_raw = build_evidence_rows(input_rows, contracts_meta)
    parsed = write_evidence_csv(evidence_rows_raw, args.evidence_out, args.input)

    html_doc = build_html_doc(parsed)
    for out_path in (args.html_out, args.html_latest_out):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_doc, encoding="utf-8")

    present = sum(1 for r in parsed if r["evidence_status"] == "present")
    not_found = len(parsed) - present
    verified_present = sum(
        1 for r in parsed if r["evidence_status"] == "present" and r["source_grounding_status"] == "grounded"
    )
    contracts_labeled = sum(1 for r in parsed if r["contract_id"] in contracts_meta)

    print("Codify evidence layer + viewer build summary")
    print(f"  input rows read:          {len(input_rows)}")
    print(f"  evidence rows written:    {len(parsed)}")
    print(f"  present (evidence found): {present}")
    print(f"  not_found:                {not_found}")
    print(f"  verified present:         {verified_present}")
    print(f"  rows with contract label from data/contracts.csv: {contracts_labeled}/{len(parsed)}")
    print(f"  evidence CSV:             {args.evidence_out}")
    print(f"  dated html browser:       {args.html_out}")
    print(f"  latest html browser:      {args.html_latest_out}")


if __name__ == "__main__":
    main()
