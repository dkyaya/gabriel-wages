"""
gabriel_codify_pilot.py — bounded, auditable GABRIEL codify() pilot scaffold,
with an optional Harvard Proxy adapter for gabriel.codify().

Purpose: a safe, repeatable harness for small, explicitly-approved pilots that ask
gabriel.codify() to code short evidence-window excerpts (already built from this
project's own corpus text) against this project's wage-mechanism codebook.
See docs/analysis/gabriel_codify_full_codebook_pilot_design_2026-07-09.md for the
full design and docs/analysis/gabriel_codify_harvard_proxy_adapter_design_2026-07-09.md
for how the Harvard Proxy adapter is wired into gabriel.codify()'s response_fn hook.

SAFETY MODEL — read before use:
  - Defaults to dry-run. No network call, no gabriel.codify() invocation, no key read.
  - Live calls require --live AND an explicit --max-calls (hard-capped at 8 in code, raised
    from 4 on 2026-07-09 for the approved Texas/Ohio scale-up run of 8 remaining rows --
    see docs/analysis/gabriel_codify_texas_ohio_scaleup_preflight_2026-07-09.md; raising the
    cap requires a deliberate code change, not a CLI flag).
  - Credentials are read from the environment (optionally loaded from a git-ignored
    .env file via python-dotenv) ONLY inside the live-call code path. Presence is
    checked and logged as booleans only -- values are never printed, logged, or
    written to any output file.
  - Each selected row is coded with its OWN gabriel.codify() invocation (not one
    batched call for all rows), so a failure on row N does not obscure whether
    rows 1..N-1 succeeded, and the run can cleanly stop after the first nontrivial
    failure without discarding prior successes.
  - Every run writes to a fresh, timestamped directory under
    tmp/gabriel_codify_pilots/YYYY-MM-DD_HHMMSS/ and never overwrites a prior run.
  - Never modifies data/contracts.csv, data/city_coverage.csv, corpus/, or inbox/.
    Reads a pre-built evidence-window CSV only; does not ingest or fetch documents.
  - Does not import gabriel, dotenv, or read any credential, on the dry-run path.

Usage (safe, no network call):
  python scripts/gabriel_codify_pilot.py --dry-run --max-calls 4 \
      --windows docs/analysis/gabriel_codify_full_codebook_evidence_windows_2026-07-09.csv

Usage (live, requires HARVARD_SUBSCRIPTION_KEY, e.g. via a git-ignored .env file):
  python scripts/gabriel_codify_pilot.py --live --use-harvard-proxy --max-calls 4 \
      --windows docs/analysis/gabriel_codify_full_codebook_evidence_windows_2026-07-09.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WINDOWS_CSV = ROOT / "docs" / "analysis" / "gabriel_codify_full_codebook_evidence_windows_2026-07-09.csv"
PILOT_OUTPUT_ROOT = ROOT / "tmp" / "gabriel_codify_pilots"

# Hard ceiling. --max-calls above this is refused outright, regardless of what
# the caller passes -- raising this requires a deliberate code edit, not a flag.
# Raised 4 -> 8 on 2026-07-09 for the Texas/Ohio scale-up run, then 8 -> 10 on
# 2026-07-10 for the approved curated Massachusetts scale-up run (10 selected
# rows, one call each). See gabriel_codify_massachusetts_preflight_2026-07-09.md.
HARD_MAX_CALLS = 10

# Default (non-proxy) GABRIEL model; overridden to a Harvard-proxy-confirmed model
# when --use-harvard-proxy is passed (see HARVARD_PROXY_MODEL below).
MODEL = "gpt-5.4-mini"
REASONING_EFFORT = "low"
N_ROUNDS = 1  # skip codify's multi-round completion loop -- keeps call count exact

# codify() splits the codebook into batches of at most max_categories_per_call and
# splits each row's text into chunks of at most max_words_per_call words. Both are
# set generously above this pilot's actual codebook size (19) and window sizes
# (all under 700 words) so each selected row produces EXACTLY one live call.
MAX_CATEGORIES_PER_CALL = 19
MAX_WORDS_PER_CALL = 1500

# Harvard Proxy connection details. The base_url is not a secret -- it is already
# committed, unredacted, elsewhere in this repo (ingest/extract_spans.py,
# scripts/proxy_pilot_must_have_sources.py). Only the subscription key is a secret,
# and it is read from the environment exclusively inside _harvard_proxy_response_fn
# / _run_live, never printed or logged.
HARVARD_PROXY_BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
HARVARD_PROXY_MODEL = "gpt-5.4-nano"  # confirmed working against this proxy elsewhere in this repo

# ---------------------------------------------------------------------------
# Full refined 19-attribute wage-mechanism codebook (2026-07-09).
# ---------------------------------------------------------------------------
CATEGORIES = {
    "peer_comparator_wage_comparability": (
        "Explicit use of peer cities, comparable communities, external labor "
        "markets, comparator jurisdictions, or comparable bargaining units to "
        "justify wage levels, wage increases, or wage schedules. Positive "
        "examples: 'comparable communities', 'peer cities', 'market comparison', "
        "'competitive with surrounding municipalities'. Exclude internal equity "
        "only, or generic 'competitive wages' without an external comparator."
    ),
    "interest_arbitration_or_formal_impasse_backstop": (
        "Wage-setting or successor-contract settlement shaped by formal impasse "
        "institutions such as interest arbitration, statutory impasse "
        "arbitration, JLMC-type process, SERB conciliation, factfinding, "
        "mediation-to-award process, or bargaining in the shadow of formal "
        "impasse resolution. Positive examples: 'interest arbitration', "
        "'conciliation award', 'factfinder recommendation', 'impasse procedures "
        "for unresolved successor agreement', 'binding arbitration for contract "
        "terms'. Exclude ordinary grievance arbitration, discipline arbitration, "
        "or contract-interpretation arbitration."
    ),
    "grievance_or_contract_interpretation_arbitration": (
        "Arbitration used for grievances, discipline, contract interpretation, "
        "enforcement, or disputes under an existing agreement. Positive "
        "examples: 'grievance arbitration', 'arbitrator shall interpret this "
        "agreement', 'disciplinary arbitration'. Exclude interest arbitration or "
        "impasse arbitration over successor wage terms unless clearly described."
    ),
    "staffing_shortage_recruitment_retention": (
        "Explicit concern about vacancies, recruitment, retention, hiring, "
        "turnover, staffing shortages, labor supply, attrition, or inability to "
        "fill positions. Positive examples: 'recruitment and retention', "
        "'vacancies', 'hard to hire', 'staffing shortage'. Exclude routine "
        "staffing assignments without shortage/retention language."
    ),
    "minimum_staffing_or_continuous_coverage": (
        "Minimum staffing, required crew levels, continuous coverage, 24/7 "
        "service obligations, station coverage, mandatory coverage, or "
        "inability to defer service. Positive examples: 'minimum staffing', "
        "'two employees on duty at all times', '24-hour coverage', 'shall "
        "maintain staffing'. Exclude ordinary work schedules without a coverage "
        "constraint."
    ),
    "overtime_callback_holdover_mandatory_extra_work": (
        "Overtime, callback, holdover, mandatory overtime, court time, extra "
        "duty, detail work, standby/on-call, shift extension, or premium "
        "compensation for extra work demands. Positive examples: 'callback "
        "pay', 'holdover', 'mandatory overtime', 'standby pay'. Exclude base "
        "wage schedules alone."
    ),
    "classification_reclassification_or_grade_structure": (
        "Wage setting through classification systems, grades, steps, job "
        "titles, reclassification, compensation studies, wage schedules, or "
        "grade appeals. Positive examples: 'classification plan', 'Grade 12', "
        "'step schedule', 'reclassification', 'compensation study'. Exclude a "
        "one-off premium/differential without a classification structure."
    ),
    "training_certification_credential_premiums": (
        "Wage premiums, stipends, incentives, requirements, or career ladders "
        "linked to training, certifications, degrees, licenses, credentials, "
        "EMT/paramedic, EMD/E911, CDL, hoisting, water/wastewater, education, or "
        "specialist qualifications. Positive examples: 'certification pay', "
        "'education incentive', 'paramedic premium', 'CDL stipend'. Exclude "
        "generic training obligations without wage implication unless clearly "
        "tied to job requirements."
    ),
    "hazard_risk_stress_or_line_of_duty_rationale": (
        "Explicit wage or benefit language tied to hazard, risk, injury, "
        "stress, line-of-duty harm, dangerous conditions, public-safety "
        "exposure, or physical/psychological burden. Positive examples: 'line "
        "of duty injury', 'hazardous duty', 'risk', 'stress', 'danger'. Exclude "
        "generic sick leave/injury leave without a risk rationale."
    ),
    "premium_pay_differentials": (
        "Shift differentials, assignment differentials, specialty pay, "
        "longevity, night/weekend pay, holiday premiums, bilingual pay, "
        "paramedic pay, detail rates, or other add-ons beyond base wage. "
        "Positive examples: 'shift differential', 'longevity', 'premium pay', "
        "'special assignment pay'. Exclude base wage scales only."
    ),
    "benefits_total_compensation_or_pension": (
        "Health insurance, pension, retirement, deferred compensation, paid "
        "leave, total compensation, uniform allowance, equipment allowance, or "
        "other non-wage benefits that affect compensation. Positive examples: "
        "'health insurance contribution', 'pension', 'uniform allowance', "
        "'deferred compensation'. Exclude wage-only provisions."
    ),
    "subcontracting_outsourcing_or_volunteer_substitution": (
        "Contracting out, outsourcing, privatization, volunteer substitution, "
        "non-unit labor replacement, civilianization, or restrictions on "
        "replacing bargaining-unit work. Positive examples: 'contracting out', "
        "'subcontracting', 'volunteers shall not replace', 'civilianization'. "
        "Exclude management rights clauses that do not mention "
        "substitution/outsourcing."
    ),
    "management_rights_or_service_flexibility": (
        "Management rights to assign, schedule, transfer, reorganize, "
        "determine staffing, set operations, change methods, deploy personnel, "
        "or maintain service flexibility. Positive examples: 'management "
        "retains the right to assign', 'determine staffing', 'transfer "
        "employees'. Exclude union rights or grievance provisions alone."
    ),
    "no_strike_or_work_stoppage_constraint": (
        "No-strike, no-slowdown, no-lockout, essential-service continuity, or "
        "statutory work-stoppage constraints. Positive examples: 'no strike', "
        "'no slowdown', 'no work stoppage', 'no lockout'. Exclude generic "
        "discipline clauses."
    ),
    "civil_service_or_statutory_employment_channel": (
        "Civil-service provisions, statutory employment protections, "
        "meet-and-confer statutes, Chapter 174/142/146 references, Chapter "
        "4117/SERB references, appointment/promotion rules, or statutory "
        "channels structuring bargaining/wage-setting. Positive examples: "
        "'civil service', 'Chapter 174', 'Chapter 4117', 'meet and confer', "
        "'SERB'. Exclude generic city authority without a statutory/legal "
        "channel."
    ),
    "union_security_or_institutional_power": (
        "Union recognition, dues/agency checkoff, exclusive representation, "
        "release time, union access, bulletin boards, labor-management "
        "committees, bargaining rights, or institutional supports for union "
        "power. Positive examples: 'exclusive bargaining representative', "
        "'dues deduction', 'union leave', 'labor-management committee'. "
        "Exclude incidental mention of the union's name only."
    ),
    "budget_capacity_or_fiscal_constraint": (
        "Fiscal capacity, budget constraints, ability to pay, appropriations, "
        "tax limits, fiscal emergency, budgetary shortfall, or city financial "
        "condition used to shape wages. Positive examples: 'available funds', "
        "'budget constraints', 'ability to pay', 'appropriation'. Exclude "
        "routine payroll administration."
    ),
    "non_safety_wage_restraint_or_admin_channel": (
        "Evidence that non-safety wages are routed through administrative pay "
        "plans, classification systems, consultation rather than bargaining, "
        "weaker impasse pathways, delayed studies, pay-grade adjustments, or "
        "limited wage channels. Positive examples: 'consultation policy', "
        "'classification compensation plan', 'compensation study', 'not "
        "subject to collective bargaining', 'pay grade adjustment'. Exclude any "
        "non-safety clause unless it specifically shows wage-channel "
        "restraint/admin routing."
    ),
    "other": (
        "Relevant wage-mechanism evidence not captured above. Use sparingly "
        "and explain."
    ),
}

ADDITIONAL_INSTRUCTIONS = """\
You are coding short excerpts from public-sector labor agreements (collective
bargaining agreements, meet-and-confer agreements, or arbitration awards) for
the presence of specific wage-setting mechanisms. For EACH attribute below:

GLOBAL CODING RULES
- Use source text only.
- Do not infer causal effects.
- Do not infer institutional mechanisms from outside legal knowledge unless
  the source text explicitly references them.
- Do not mark interest_arbitration_or_formal_impasse_backstop present for
  ordinary grievance arbitration -- that belongs under
  grievance_or_contract_interpretation_arbitration instead.
- Do not mark peer_comparator_wage_comparability present for generic
  "competitive wages" unless a peer/external comparator is explicit.
- Use not_found when evidence is absent.
- Use unclear when the text is suggestive but not enough.
- Keep excerpts short. Avoid long copied passages.
- Preserve exact wording for excerpts -- copy verbatim, do not paraphrase.
- Attribute evidence to the source window only; this window is a compact
  reassembly of previously-identified passages from one bargaining document,
  not the full document -- do not assume missing context implies absence.

For EACH attribute, report:
1. evidence_status: "present", "not_found", or "unclear".
2. If present or unclear, a SHORT VERBATIM SPAN (under 40 words) copied
   EXACTLY from the excerpt text. Never invent or infer text not literally
   present in the excerpt.
3. excerpt_location if identifiable from the text (e.g. an article/section
   reference visible in the window).
4. confidence: "high", "medium", "low", or "not_applicable" (use
   not_applicable only when evidence_status is not_found).
5. A one-sentence caveat/note if the match is partial, fragmentary, or
   uncertain; otherwise leave it blank.
"""


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Default mode. No network call.")
    mode.add_argument("--live", action="store_true", help="Make real gabriel.codify() calls. Requires --max-calls.")
    p.add_argument(
        "--max-calls", type=int, default=None,
        help=f"Number of rows to code. Required with --live. Hard-capped at {HARD_MAX_CALLS}.",
    )
    p.add_argument(
        "--windows", "--windows-csv", dest="windows_csv", type=Path, default=DEFAULT_WINDOWS_CSV,
        help="Evidence-window CSV to read.",
    )
    p.add_argument("--contract-id", type=str, default=None, help="Optional: restrict to one contract_id.")
    p.add_argument(
        "--use-harvard-proxy", action="store_true",
        help="Route gabriel.codify() through the Harvard Proxy via a response_fn adapter "
             "(HARVARD_SUBSCRIPTION_KEY, loaded from the environment or a git-ignored .env file). "
             "No effect in --dry-run mode.",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Mechanism-label contamination check (added 2026-07-10).
#
# Why this exists: the Texas/Ohio scale-up run (2026-07-09) assembled evidence
# windows by joining excerpts under headers like
#   "--- Arbitration / impasse backstop (legacy code -- may be interest OR
#   grievance arbitration; distinguish from text) [char 1792] ---"
# For oh_cleveland_fire_2025, the underlying passage under that heading was
# unreadable OCR table-of-contents garbage, and the model echoed the header
# text itself back as its "evidence" for interest_arbitration_or_formal_
# impasse_backstop -- a false positive that happened to pass a naive
# substring-of-window_text grounding check, because the header WAS literally
# in window_text (this project put it there). See
# docs/analysis/gabriel_codify_texas_ohio_scaleup_audit_2026-07-09.md.
#
# The window_text sent to codify() must therefore contain ONLY genuine
# source-document text plus neutral, keyword-free location separators (e.g.
# "--- Excerpt 1 [page 48] ---"). Mechanism/codebook vocabulary belongs in the
# CATEGORIES dict and ADDITIONAL_INSTRUCTIONS above -- never in the window
# body itself, where it becomes something the model can "find" regardless of
# whether the underlying source document actually supports it.
#
# This script does not build window_text itself (it is assembled upstream by
# a window-construction script/CSV and read here via --windows), so this is a
# read-time guardrail: it scans every row's window_text for the codebook's own
# attribute names (verbatim, from CATEGORIES) plus a couple of generic tells
# ("Mechanism", "Arbitration / impasse") and refuses to proceed -- in BOTH
# dry-run and live mode -- if any are found. Fail-safe, not warn-and-continue:
# a window that already contains this project's own mechanism vocabulary is
# not safe to send, dry-run or live, until the window-construction step is
# fixed.
GENERIC_CONTAMINATION_STRINGS = ["Mechanism", "Arbitration / impasse"]

# "other" is deliberately excluded: it is a real CATEGORIES key (the catch-all
# attribute), but as a bare substring it matches ordinary English prose
# ("other municipality", "other conditions of employment", ...) constantly,
# producing false positives on every real window. Every other attribute key is
# a multi-word, underscore-joined string that would never occur in genuine
# source-document text by coincidence, so this exclusion does not meaningfully
# weaken the check.
_CONTAMINATION_EXEMPT_KEYS = {"other"}


def _contamination_patterns() -> list[str]:
    keys = [k for k in CATEGORIES.keys() if k not in _CONTAMINATION_EXEMPT_KEYS]
    return keys + GENERIC_CONTAMINATION_STRINGS


def _check_window_contamination(rows: list[dict]) -> None:
    patterns = _contamination_patterns()
    violations: list[tuple[str, str]] = []
    for row in rows:
        window_text = row.get("window_text", "") or ""
        lowered = window_text.lower()
        for pat in patterns:
            if pat.lower() in lowered:
                violations.append((row.get("contract_id", "<unknown>"), pat))
    if violations:
        print("ERROR: mechanism-label contamination detected in evidence-window text.")
        print("The window body must contain only source-document text and neutral")
        print("location separators -- never codebook/mechanism vocabulary. Fix the")
        print("window-construction step (or the --windows CSV) before proceeding.")
        for contract_id, pat in violations:
            print(f"  {contract_id}: contains {pat!r}")
        sys.exit(1)


def _read_windows(path: Path, contract_id: str | None) -> list[dict]:
    if not path.exists():
        print(f"ERROR: windows CSV not found: {path}")
        sys.exit(1)
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if contract_id:
        rows = [r for r in rows if r["contract_id"] == contract_id]
    _check_window_contamination(rows)
    return rows


def _make_output_dir() -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = PILOT_OUTPUT_ROOT / ts
    out_dir.mkdir(parents=True, exist_ok=False)
    return out_dir


def _write_run_config(out_dir: Path, args: argparse.Namespace, selected: list[dict],
                       live_attempted: bool, reason_not_attempted: str | None,
                       model_used: str | None = None) -> None:
    config = {
        "run_timestamp": datetime.now().isoformat(),
        "function": "gabriel.codify",
        "column_name": "window_text",
        "save_dir": str(out_dir / "gabriel_save_dir"),
        "model": model_used or MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "n_rounds": N_ROUNDS,
        "max_categories_per_call": MAX_CATEGORIES_PER_CALL,
        "max_words_per_call": MAX_WORDS_PER_CALL,
        "max_calls_allowed": HARD_MAX_CALLS,
        "max_calls_requested": args.max_calls,
        "use_harvard_proxy": bool(getattr(args, "use_harvard_proxy", False)),
        "harvard_proxy_base_url": HARVARD_PROXY_BASE_URL if getattr(args, "use_harvard_proxy", False) else None,
        "selected_contract_ids": [r["contract_id"] for r in selected],
        "n_attributes": len(CATEGORIES),
        "categories": CATEGORIES,
        "live_run_attempted": live_attempted,
        "live_run_reason_not_attempted": reason_not_attempted,
    }
    with (out_dir / "run_config.json").open("w") as f:
        json.dump(config, f, indent=2)
    with (out_dir / "run_config.json").open() as f:
        json.load(f)  # parse back immediately


def _write_selected_windows(out_dir: Path, selected: list[dict]) -> None:
    if not selected:
        return
    fieldnames = list(selected[0].keys())
    path = out_dir / "selected_windows.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in selected:
            w.writerow(r)
    with path.open(newline="") as f:
        list(csv.DictReader(f))  # parse back immediately


def _write_prompt_preview(out_dir: Path, selected: list[dict], model_used: str) -> None:
    lines = [
        "# GABRIEL Codify Pilot Prompt Preview (script-generated)",
        "",
        f"Model: `{model_used}` | Attributes: {len(CATEGORIES)} | n_rounds={N_ROUNDS} | "
        f"max_categories_per_call={MAX_CATEGORIES_PER_CALL} | max_words_per_call={MAX_WORDS_PER_CALL}",
        "",
        "## Categories (full codebook)",
        "```python",
        json.dumps(CATEGORIES, indent=2),
        "```",
        "",
        "## additional_instructions",
        "```text",
        ADDITIONAL_INSTRUCTIONS,
        "```",
        "",
        "## Selected windows",
        "",
    ]
    for r in selected:
        lines.append(f"### {r['contract_id']} ({r.get('window_id', '')})")
        lines.append(f"- state/city/occupation_class: {r.get('state')}/{r.get('city')}/{r.get('occupation_class')}")
        lines.append(f"- source_file: {r.get('source_file')}")
        lines.append(f"- chars: {r.get('window_char_count', r.get('window_token_or_char_count'))}")
        lines.append("")
    (out_dir / "prompt_preview.md").write_text("\n".join(lines))


def _credential_status() -> dict:
    import os
    return {
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "OPENAI_BASE_URL": bool(os.environ.get("OPENAI_BASE_URL")),
        "HARVARD_SUBSCRIPTION_KEY": bool(os.environ.get("HARVARD_SUBSCRIPTION_KEY")),
    }


def _run_dry(out_dir: Path, selected: list[dict], args: argparse.Namespace) -> None:
    model_used = HARVARD_PROXY_MODEL if args.use_harvard_proxy else MODEL
    _write_selected_windows(out_dir, selected)
    _write_prompt_preview(out_dir, selected, model_used)
    _write_run_config(out_dir, args=args, selected=selected,
                       live_attempted=False, reason_not_attempted="--dry-run passed (or --live not requested).",
                       model_used=model_used)
    log = [
        "GABRIEL codify pilot -- dry run log",
        f"Run timestamp: {datetime.now().isoformat()}",
        f"Rows selected: {len(selected)}",
        f"use_harvard_proxy: {args.use_harvard_proxy}",
        "NO NETWORK CALL WAS MADE. NO CREDENTIAL WAS READ.",
        f"Outputs written to: {out_dir}",
    ]
    (out_dir / "dry_run_log.txt").write_text("\n".join(log) + "\n")
    print("Dry run complete. See", out_dir)


def _make_harvard_proxy_response_fn(subscription_key: str, out_dir: Path):
    """Build a gabriel.codify()-compatible `response_fn` that routes each
    per-window coding prompt through the Harvard Proxy. See
    docs/analysis/gabriel_codify_harvard_proxy_adapter_design_2026-07-09.md
    for the source-level trace confirming this hook's contract."""
    from openai import OpenAI

    client = OpenAI(
        api_key=subscription_key,
        base_url=HARVARD_PROXY_BASE_URL,
        default_headers={"Ocp-Apim-Subscription-Key": subscription_key},
    )

    HERE = ROOT / "scripts"
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    try:
        from log_api_spend import log_usage  # noqa: E402
    except Exception:
        log_usage = None  # non-fatal: usage logging is best-effort

    async def harvard_proxy_response_fn(prompt, *, model=None, reasoning_effort=None,
                                         json_mode=False, n=1, timeout=None,
                                         use_dummy=False, **kwargs):
        def _call():
            create_kwargs = dict(
                model=model or HARVARD_PROXY_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            if reasoning_effort:
                create_kwargs["reasoning_effort"] = reasoning_effort
            if json_mode:
                create_kwargs["response_format"] = {"type": "json_object"}
            return client.chat.completions.create(**create_kwargs)

        response = await asyncio.to_thread(_call)
        if log_usage is not None:
            try:
                log_usage(response, "gabriel_codify_pilot.py (harvard_proxy)", model or HARVARD_PROXY_MODEL)
            except Exception:
                pass  # usage logging must never break the pilot
        content = response.choices[0].message.content or ""
        return ([content], None, [content])

    return harvard_proxy_response_fn


def _run_live(out_dir: Path, selected: list[dict], max_calls: int, args: argparse.Namespace) -> None:
    creds = _credential_status()
    response_fn = None
    model_used = MODEL

    if args.use_harvard_proxy:
        if not creds["HARVARD_SUBSCRIPTION_KEY"]:
            # Only reached if HARVARD_SUBSCRIPTION_KEY isn't already in the shell
            # environment -- try loading a git-ignored .env file (never printed).
            try:
                from dotenv import load_dotenv
                load_dotenv()
                creds = _credential_status()
            except Exception:
                pass
        if not creds["HARVARD_SUBSCRIPTION_KEY"]:
            reason = (
                "--use-harvard-proxy was passed but HARVARD_SUBSCRIPTION_KEY is not "
                "set (checked presence only, no values read; also tried loading a "
                ".env file via python-dotenv). Refusing live call; falling back to "
                "dry-run outputs."
            )
            print("ERROR:", reason)
            _run_dry(out_dir, selected, args)
            return
        import os
        subscription_key = os.environ["HARVARD_SUBSCRIPTION_KEY"]
        response_fn = _make_harvard_proxy_response_fn(subscription_key, out_dir)
        model_used = HARVARD_PROXY_MODEL
    elif not (creds["OPENAI_API_KEY"] or creds["HARVARD_SUBSCRIPTION_KEY"]):
        reason = (
            "No usable credential present (checked OPENAI_API_KEY and "
            "HARVARD_SUBSCRIPTION_KEY presence only, no values read) and "
            "--use-harvard-proxy was not passed. Refusing live call; falling "
            "back to dry-run outputs."
        )
        print("ERROR:", reason)
        _run_dry(out_dir, selected, args)
        return

    try:
        import gabriel
    except Exception as e:  # pragma: no cover - environment dependent
        print(f"ERROR: failed to import gabriel: {e}")
        _write_run_config(out_dir, args=args, selected=selected,
                           live_attempted=False, reason_not_attempted=f"gabriel import failed: {e}",
                           model_used=model_used)
        return

    import pandas as pd

    rows = selected[:max_calls]
    _write_selected_windows(out_dir, rows)

    all_results = []
    errors = []
    raw_records = []
    calls_succeeded = 0
    log_lines = [f"Live run at {datetime.now().isoformat()}", f"use_harvard_proxy: {args.use_harvard_proxy}",
                 f"model: {model_used}", f"rows requested: {len(rows)}", ""]

    # Each selected row gets its OWN gabriel.codify() invocation (not one batched
    # call for all rows) so a failure on row N is isolated from rows 1..N-1, and
    # the run can stop cleanly after the first nontrivial failure.
    for i, row in enumerate(rows, 1):
        contract_id = row["contract_id"]
        one_row_df = pd.DataFrame([row])
        row_save_dir = out_dir / "gabriel_save_dir" / contract_id
        print(f"  [{i}/{len(rows)}] {contract_id}: calling gabriel.codify() ...")
        try:
            codify_kwargs = dict(
                df=one_row_df,
                column_name="window_text",
                save_dir=str(row_save_dir),
                categories=CATEGORIES,
                additional_instructions=ADDITIONAL_INSTRUCTIONS,
                model=model_used,
                reasoning_effort=REASONING_EFFORT,
                n_rounds=N_ROUNDS,
                max_categories_per_call=MAX_CATEGORIES_PER_CALL,
                max_words_per_call=MAX_WORDS_PER_CALL,
                n_parallels=1,
            )
            if response_fn is not None:
                codify_kwargs["response_fn"] = response_fn
            # gabriel.codify is an async def function -- it must be awaited (via
            # asyncio.run in this synchronous script), not called directly, or it
            # just returns an un-run coroutine object.
            result_df = asyncio.run(gabriel.codify(**codify_kwargs))
            # codify() returns the input df's columns (already including
            # contract_id, since one_row_df carries the full evidence-window
            # row) plus one new column per coded category -- no need to insert.
            if "contract_id" not in result_df.columns:
                result_df.insert(0, "contract_id", contract_id)
            all_results.append(result_df)
            raw_records.append({"contract_id": contract_id, "row": row, "result": result_df.to_dict(orient="records")})
            calls_succeeded += 1
            log_lines.append(f"[{i}] {contract_id}: SUCCESS")
        except Exception as e:
            errors.append({"contract_id": contract_id, "error": str(e), "type": type(e).__name__})
            log_lines.append(f"[{i}] {contract_id}: ERROR — {type(e).__name__}: {e}")
            print(f"ERROR: live call failed on {contract_id}: {e}")
            print("Stopping per no-retry / stop-on-first-failure policy.")
            break

    if errors:
        with (out_dir / "errors.jsonl").open("w") as f:
            for err in errors:
                f.write(json.dumps(err) + "\n")

    if raw_records:
        with (out_dir / "raw_outputs.jsonl").open("w") as f:
            for rec in raw_records:
                f.write(json.dumps(rec, default=str) + "\n")

    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        combined.to_csv(out_dir / "parsed_outputs.csv", index=False)

    log_lines.append("")
    log_lines.append(f"Calls attempted: {calls_succeeded + len(errors)} | succeeded: {calls_succeeded} | failed: {len(errors)}")
    (out_dir / "live_run_log.txt").write_text("\n".join(log_lines) + "\n")
    print("\n".join(log_lines))

    _write_run_config(out_dir, args=args, selected=selected, live_attempted=True, reason_not_attempted=None,
                       model_used=model_used)
    print("Live run complete. See", out_dir)


def main() -> None:
    args = _parse_args()

    if args.live:
        if args.max_calls is None:
            print("ERROR: --live requires an explicit --max-calls.")
            sys.exit(1)
        if args.max_calls > HARD_MAX_CALLS:
            print(f"ERROR: --max-calls {args.max_calls} exceeds the hard cap of {HARD_MAX_CALLS}.")
            sys.exit(1)

    selected = _read_windows(args.windows_csv, args.contract_id)
    if not selected:
        print("ERROR: no rows selected from", args.windows_csv)
        sys.exit(1)

    out_dir = _make_output_dir()

    if args.live:
        _run_live(out_dir, selected, max_calls=args.max_calls, args=args)
    else:
        _run_dry(out_dir, selected, args)


if __name__ == "__main__":
    main()
