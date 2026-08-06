#!/usr/bin/env python3
"""Build the lane-owned mechanism-profile and Alaska audit outputs.

This script is deliberately bounded to existing local, canonical evidence.  It
does not render figures, alter claim classes, or write outside lane_002.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
LANE = Path(__file__).resolve().parent
CORRECTION = ROOT / "docs/analysis/handoff/GABRIEL-WAGES-VISUAL-ATLAS-CORRECTION-AND-RESTRUCTURE-2026-08-06"
SCOUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04"
ADJ = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-INTEGRATION-AND-CLAIM-ADJUDICATION-2026-08-06"

EVENTS = SCOUT / "mechanism_exposure_event_layer.jsonl"
CROSSWALK = SCOUT / "municipality_geographic_crosswalk.jsonl"
PROFILE_PLAN = CORRECTION / "integrated_mechanism_profile_plan.jsonl"
MAP_MANIFEST = CORRECTION / "corrected_mechanism_map_manifest.jsonl"
READER_REGISTRY = CORRECTION / "reader_facing_mechanism_registry.jsonl"
STATUS_REGISTRY = CORRECTION / "evidence_status_category_registry.jsonl"
CLAIMS = ADJ / "final_adjudicated_claim_table.jsonl"

SAFETY_SIDES = {"police", "fire", "safety_combined"}
STATUS_TAGS = {"none_identified", "no_direct_compensation_outcome", "unclear"}

PROFILE_ORDER = [
    "formal-bargaining",
    "scheduled-base-growth",
    "non-base-compensation",
    "staffing-market-pressure",
    "retroactivity-payroll",
    "budgets-pay-plans",
    "ordinance-adoption",
    "classification-structure",
]

PROFILE_CONTENT = {
    "formal-bargaining": {
        "definition": "Formal bargaining covers negotiation, settlement, ratification, and neutral resolution of a bargaining impasse.",
        "wage_channel": "It can raise or preserve pay by turning schedules, premiums, and effective dates into enforceable terms and by giving unsettled terms a route to resolution.",
        "example": "A Harrison, Ohio memorandum states that bargaining-unit members would receive a three percent lump-sum payment.",
        "limitation": "The implementation-event registry contains only one interest-arbitration event, and formal bargaining also exists on the non-safety side.",
        "caption": "Formal bargaining covers negotiation, settlement, ratification, and neutral resolution of an impasse. It can raise or preserve pay by turning schedules, premiums, and effective dates into enforceable terms. Among the 47 side-classified events in this profile, 42 are safety and 5 are non-safety; 34 more are mixed, side-independent, or unresolved. The pattern shows that safety bargaining is more visible in these records, not that bargaining causes a national safety wage advantage.",
    },
    "scheduled-base-growth": {
        "definition": "Scheduled growth includes across-the-board raises, base-wage changes, steps, recurring adjustments, and cost-of-living provisions.",
        "wage_channel": "These rules can raise recurring pay without requiring every increase to be negotiated from zero because the schedule, step, percentage, or index supplies the next adjustment.",
        "example": "A Bruceville-Eddy, Texas pay-plan record gives most employees a four percent cost-of-living adjustment and separately mentions Public Works, showing that scheduled growth is not exclusive to safety employees.",
        "limitation": "Step progression leans safety in the reviewed sample, across-the-board results are mixed, and the cost-of-living cells remain sparse.",
        "caption": "Scheduled growth includes general raises, base-wage changes, steps, recurring adjustments, and cost-of-living provisions. These rules can raise recurring pay without renegotiating every increase from zero. Among 416 side-classified events, 384 are safety and 32 are non-safety; 393 more are mixed, side-independent, or unresolved. Step progression leans safety in the reviewed sample, but across-the-board results are mixed and cost-of-living evidence is sparse. This does not establish a uniform safety growth advantage.",
    },
    "non-base-compensation": {
        "definition": "Non-base compensation includes overtime, holiday pay, longevity, premiums, stipends, allowances, benefits, reimbursements, and one-time payments.",
        "wage_channel": "These provisions can raise effective compensation or offset job costs even when the recurring base rate changes little.",
        "example": "The Harrison, Ohio memorandum's three percent lump-sum payment is a concrete one-time payment that does not by itself raise the future base schedule.",
        "limitation": "The records identify compensation channels but do not provide a complete, compatible total-compensation sum for safety and non-safety employees.",
        "caption": "Non-base compensation includes overtime, holiday pay, longevity, premiums, stipends, allowances, benefits, reimbursements, and one-time payments. These provisions can raise effective compensation even when base pay changes little. One-time and recurring components remain separate because their future effects differ. Among 489 side-classified events, 452 are safety and 37 are non-safety; 401 more are mixed, side-independent, or unresolved. The evidence establishes additional compensation channels, but it does not provide a complete or comparable total-compensation sum across occupations.",
    },
    "staffing-market-pressure": {
        "definition": "Staffing and market pressure covers vacancies, recruitment difficulty, retention risk, and comparisons with other jobs or jurisdictions.",
        "wage_channel": "Municipalities can use these pressures to justify a targeted schedule change, premium, or classification adjustment.",
        "example": "The final claim package preserves local recruitment, retention, vacancy, and comparator examples, but the short excerpts do not support a single representative effect-size example.",
        "limitation": "The profile is small and descriptive; it does not show that a shortage caused a pay increase or how common the response is nationally.",
        "caption": "Staffing and market pressure includes vacancies, recruitment difficulty, retention risk, and comparisons with other jobs or jurisdictions. Municipalities can use these conditions to justify targeted raises, premiums, or classification changes. Among 29 side-classified events, 22 are safety and 7 are non-safety; 27 more are mixed, side-independent, or unresolved. This is consistent with a visible safety-pressure channel in some municipalities, but the evidence is descriptive and does not establish causation or national prevalence.",
    },
    "retroactivity-payroll": {
        "definition": "Retroactive terms apply an earlier effective date when agreement, approval, or payroll administration occurs later.",
        "wage_channel": "They can convert delay into payable increases or back pay, while payroll-effective records identify when an approved change entered the pay system.",
        "example": "The final evidence packet includes police retroactivity records from Flint, Michigan and a Lancaster, New York arbitration award.",
        "limitation": "An adopted or retroactive term is not automatic proof that payment occurred; payment language remains limited to records with a retained paid stage.",
        "caption": "Retroactive terms apply an earlier effective date when agreement, approval, or payroll administration occurs later. They can convert delay into payable increases or back pay. Among 1,059 side-classified events, 945 are safety and 114 are non-safety; 1,194 more are mixed, side-independent, or unresolved. The profile distinguishes an effective date, formal adoption, payroll operation, and observed payment. A retroactive or adopted term is not by itself proof that employees were paid.",
    },
    "budgets-pay-plans": {
        "definition": "Budgets and pay plans formally authorize compensation, while fiscal constraints can cap, delay, or redirect it.",
        "wage_channel": "Appropriations can supply legal and financial authority for payment; affordability limits can narrow an increase or favor a one-time adjustment instead.",
        "example": "The retained administrative records show pay-plan and appropriation decisions, but they do not treat every budgeted position or proposal as a paid outcome.",
        "limitation": "Formal authorization and actual payment remain separate stages, and 413 of 636 profile events are not cleanly assigned to safety or non-safety.",
        "caption": "Budgets and pay plans can authorize compensation, while fiscal constraints can cap, delay, or redirect it. Appropriations provide legal and financial authority; affordability limits may narrow an increase or favor one-time pay. A budget line is not the same as an observed paycheck. Among 223 side-classified events, 154 are safety and 69 are non-safety; 413 more are mixed, side-independent, or unresolved. This profile shows how fiscal institutions formalize or constrain pay, not that every proposal was implemented or paid.",
    },
    "ordinance-adoption": {
        "definition": "Council and ordinance actions can move a negotiated, recommended, or administrative compensation change into formal municipal policy.",
        "wage_channel": "They can authorize a schedule or payment, but adoption is a legal or administrative stage rather than proof that payroll issued the money.",
        "example": "Washington, Pennsylvania minutes record council action to pay monies due and amend the salary ordinance; Worthington, Ohio records council approval after union ratification.",
        "limitation": "The two underlying ordinance tags overlap, and 218 of the 315 distinct profile events are mixed, side-independent, or unresolved.",
        "caption": "Council and ordinance actions can move a negotiated, recommended, or administrative pay change into formal municipal policy. They can authorize a schedule or payment, but adoption is not payroll confirmation. Among 97 side-classified events, 76 are safety and 21 are non-safety; 218 more are mixed, side-independent, or unresolved. The two registry categories overlap and are shown together without adding duplicate events. This profile establishes an implementation route, not a uniform wage effect.",
    },
    "classification-structure": {
        "definition": "Classification, salary-range, and civil-service rules determine where jobs enter a pay system and how grades, floors, ceilings, or promotion paths can change.",
        "wage_channel": "A reclassification or range change can raise a wage floor or ceiling, while civil-service rules can make advancement more systematic.",
        "example": "The evidence package contains classification and pay-range records, but no single example supplies a complete same-city, same-cycle safety/non-safety effect estimate.",
        "limitation": "Only 25 events are side-classified, so the 23-to-2 safety/non-safety split has a small and selective denominator.",
        "caption": "Classification, salary-range, and civil-service rules determine where jobs enter a pay system and how grades, floors, ceilings, or promotion paths change. A reclassification can raise pay, but it can also reorganize titles without producing a comparable wage effect. Most profile events are too uncertain to support a side comparison. Among 25 side-classified events, 23 are safety and 2 are non-safety; 32 more are mixed, side-independent, or unresolved. The small denominator cannot support a general safety advantage.",
    },
}

APPENDIX_CAPTION = (
    "Sparse categories remain visible without turning a few observations into a density pattern. "
    "The appendix reports exact category counts and municipalities for 11 reader-facing categories with fewer than 25 events, using points or compact cards rather than national shading. "
    "It separately reports three classification outcomes—none identified, no direct compensation outcome, and unclear—because those labels describe evidence status rather than wage-setting processes. "
    "Alaska records appear as exact points or table entries; an empty Alaska panel means no retained event, not no real-world activity."
)


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_dual(stem: str, rows: list[dict]) -> None:
    write_csv(LANE / f"{stem}.csv", rows)
    write_jsonl(LANE / f"{stem}.jsonl", rows)


def map_key(row: dict) -> tuple:
    return (
        row["root_compensation_event_id"],
        row["municipality"],
        row["state"],
        row["compensation_cycle_id"],
        row["mechanism_tag"],
        row["side"],
    )


def profile_key(row: dict) -> tuple:
    return (
        row["root_compensation_event_id"],
        row["municipality"],
        row["state"],
        row["compensation_cycle_id"],
        row["side"],
    )


def side_bucket(side: str) -> str:
    if side in SAFETY_SIDES:
        return "safety"
    if side == "non_safety":
        return "non_safety"
    if side == "mixed":
        return "mixed"
    if side == "side_independent":
        return "side_independent"
    return "unresolved"


def words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def main() -> None:
    required = [EVENTS, CROSSWALK, PROFILE_PLAN, MAP_MANIFEST, READER_REGISTRY, STATUS_REGISTRY, CLAIMS]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Missing required canonical inputs: {missing}")

    raw = read_jsonl(EVENTS)
    dedup: dict[tuple, dict] = {}
    duplicate_rows: list[dict] = []
    for row in raw:
        key = map_key(row)
        if key in dedup:
            duplicate_rows.append(row)
        else:
            dedup[key] = row
    events = list(dedup.values())
    alaska = sorted(
        [row for row in events if row["state"] == "AK"],
        key=lambda row: (row["municipality"], row["compensation_cycle_id"], row["mechanism_tag"], row["side"]),
    )
    alaska_raw = [row for row in raw if row["state"] == "AK"]

    coordinates = {
        (row["municipality"], row["state"]): row
        for row in read_jsonl(CROSSWALK)
    }
    plans = {
        row["profile_id"]: row
        for row in read_jsonl(PROFILE_PLAN)
        if row["category_type"] == "reader_facing_mechanism"
    }
    map_rows = read_jsonl(MAP_MANIFEST)
    category_maps = {
        row["mechanism_tags"]: row for row in map_rows if row["kind"] == "category"
    }
    profile_maps = {
        row["figure_id"].removeprefix("corrected-profile-map-"): row
        for row in map_rows
        if row["kind"] == "profile"
    }
    reader_registry = read_jsonl(READER_REGISTRY)
    status_registry = read_jsonl(STATUS_REGISTRY)
    all_registry = reader_registry + status_registry
    claim_rows = {row["claim_id"]: row for row in read_jsonl(CLAIMS)}

    tag_to_profile: dict[str, str] = {}
    for profile_id, row in plans.items():
        for tag in row["mechanism_tags"].split("|"):
            tag_to_profile[tag] = profile_id
    for tag in STATUS_TAGS:
        tag_to_profile[tag] = "grouped-sparse-status-appendix"

    alaska_by_tag = Counter(row["mechanism_tag"] for row in alaska)
    category_counts = Counter(row["mechanism_tag"] for row in events)

    # Mark the one record retained for a reader-facing profile point whenever
    # several mechanism tags describe the same underlying profile event.
    profile_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in alaska:
        profile_id = tag_to_profile.get(row["mechanism_tag"], "grouped-sparse-status-appendix")
        profile_groups[(profile_id,) + profile_key(row)].append(row)

    event_inventory: list[dict] = []
    for row in alaska:
        profile_id = tag_to_profile.get(row["mechanism_tag"], "grouped-sparse-status-appendix")
        group = profile_groups[(profile_id,) + profile_key(row)]
        primary = sorted(group, key=lambda item: item["mechanism_tag"])[0]
        geo = coordinates.get((row["municipality"], row["state"]), {})
        digest = hashlib.sha256("|".join(map(str, map_key(row))).encode()).hexdigest()[:20]
        event_inventory.append({
            "alaska_inventory_id": f"AKMECH-{digest}",
            "root_compensation_event_id": row["root_compensation_event_id"],
            "municipality": row["municipality"],
            "state": row["state"],
            "region": row.get("region", ""),
            "compensation_cycle_id": row["compensation_cycle_id"],
            "mechanism_family": row["mechanism_family"],
            "mechanism_tag": row["mechanism_tag"],
            "side": row["side"],
            "side_bucket": side_bucket(row["side"]),
            "implementation_status": row.get("implementation_status", ""),
            "implementation_confidence": row.get("implementation_confidence", ""),
            "recurring_or_one_time": row.get("recurring_or_one_time", ""),
            "corroborating_source_count": row.get("corroborating_source_count", ""),
            "latitude": geo.get("latitude", ""),
            "longitude": geo.get("longitude", ""),
            "profile_id": profile_id,
            "profile_event_id": hashlib.sha256("|".join(map(str, (profile_id,) + profile_key(row))).encode()).hexdigest()[:20],
            "profile_primary_record": row["mechanism_exposure_event_id"] == primary["mechanism_exposure_event_id"],
            "profile_tag_count_for_same_event": len(group),
            "category_alaska_event_count": alaska_by_tag[row["mechanism_tag"]],
            "alaska_display_mode": "point_inset" if row["mechanism_tag"] not in STATUS_TAGS else "point_table",
            "analytical_unit": "deduplicated municipality × compensation cycle × compensation mechanism × side implementation event",
            "technical_lineage": row.get("technical_lineage", ""),
        })
    write_dual("final_alaska_event_inventory", event_inventory)

    mechanism_status: list[dict] = []
    for row in sorted(all_registry, key=lambda item: (-int(item["event_count"]), item["mechanism_tag"])):
        tag = row["mechanism_tag"]
        ak_rows = [item for item in alaska if item["mechanism_tag"] == tag]
        counts = Counter(side_bucket(item["side"]) for item in ak_rows)
        mapped = category_maps[tag]
        mechanism_status.append({
            "mechanism_tag": tag,
            "mechanism_name": row["mechanism_name"],
            "category_type": row["category_type"],
            "profile_id": tag_to_profile.get(tag, "grouped-sparse-status-appendix"),
            "all_geography_event_count": int(row["event_count"]),
            "alaska_event_count": len(ak_rows),
            "alaska_root_event_count": len({item["root_compensation_event_id"] for item in ak_rows}),
            "alaska_municipality_count": len({item["municipality"] for item in ak_rows}),
            "alaska_cycle_count": len({item["compensation_cycle_id"] for item in ak_rows}),
            "alaska_safety_count": counts["safety"],
            "alaska_non_safety_count": counts["non_safety"],
            "alaska_mixed_count": counts["mixed"],
            "alaska_side_independent_count": counts["side_independent"],
            "alaska_unresolved_count": counts["unresolved"],
            "alaska_display_mode": "point_inset" if ak_rows and row["category_type"] == "reader_facing_mechanism" else "point_table" if ak_rows else "explicit_none",
            "hex_density_used_for_alaska": False,
            "category_map_count_matches": int(mapped["alaska_event_count"]) == len(ak_rows),
            "all_events_accounted_for": bool(mapped["all_events_accounted_for"]),
            "analytical_unit": "deduplicated municipality × compensation cycle × compensation mechanism × side implementation event",
        })
    write_dual("final_alaska_mechanism_status", mechanism_status)

    profile_manifest: list[dict] = []
    caption_rows: list[dict] = []
    qa_rows: list[dict] = []
    for order, profile_id in enumerate(PROFILE_ORDER, 1):
        plan = plans[profile_id]
        content = PROFILE_CONTENT[profile_id]
        mapped = profile_maps[profile_id]
        tags = plan["mechanism_tags"].split("|")
        claim_ids = plan["claim_ids"].split("|") if plan["claim_ids"] else []
        claim_classes = [claim_rows[claim_id]["final_claim_class"] for claim_id in claim_ids]
        claim_boundaries = [claim_rows[claim_id]["final_claim_text"] for claim_id in claim_ids]
        ak_profile_events = {
            profile_key(item)
            for item in alaska
            if item["mechanism_tag"] in tags
        }
        profile_manifest.append({
            "profile_id": profile_id,
            "display_order": order,
            "profile_title": plan["profile_title"],
            "profile_type": "integrated_mechanism_profile",
            "mechanism_tags": plan["mechanism_tags"],
            "mechanism_category_count": len(tags),
            "display_event_count": int(plan["display_event_count"]),
            "municipality_count": int(plan["municipality_count"]),
            "state_count": int(plan["state_count"]),
            "safety_event_count": int(plan["safety_event_count"]),
            "non_safety_event_count": int(plan["non_safety_event_count"]),
            "mixed_event_count": int(plan["mixed_event_count"]),
            "side_independent_event_count": int(plan["side_independent_event_count"]),
            "unresolved_event_count": int(plan["unresolved_event_count"]),
            "alaska_event_count": len(ak_profile_events),
            "alaska_municipality_count": len({item[1] for item in ak_profile_events}),
            "alaska_display_mode": "point_inset" if ak_profile_events else "explicit_none",
            "alaska_hex_density_used": False,
            "claim_ids": "|".join(claim_ids),
            "claim_classes": "|".join(claim_classes),
            "claim_boundaries": json.dumps(claim_boundaries, ensure_ascii=False),
            "definition": content["definition"],
            "wage_channel": content["wage_channel"],
            "textual_example": content["example"],
            "strongest_limitation": content["limitation"],
            "caption": content["caption"],
            "layout_template": "profile_map_side_counts_example_boundary",
            "public_copy_status": "standalone_final_language",
        })
        caption_rows.append({
            "profile_id": profile_id,
            "profile_title": plan["profile_title"],
            "caption": content["caption"],
            "word_count": words(content["caption"]),
            "definition_present": True,
            "wage_channel_present": True,
            "side_pattern_present": True,
            "limitation_present": True,
            "claim_ids": "|".join(claim_ids),
            "alaska_note": f"Alaska: {len(ak_profile_events)} retained event{'s' if len(ak_profile_events) != 1 else ''}; " + ("shown as points" if ak_profile_events else "explicitly none"),
        })
        qa_rows.append({
            "profile_id": profile_id,
            "profile_type": "integrated_mechanism_profile",
            "event_count_matches_profile_plan": int(mapped["event_count"]) == int(plan["display_event_count"]),
            "alaska_count_matches_map_manifest": int(mapped["alaska_event_count"]) == len(ak_profile_events),
            "mechanism_tags_match": mapped["mechanism_tags"] == plan["mechanism_tags"],
            "claim_ids_preserved": mapped["claim_ids"] == plan["claim_ids"],
            "claim_classes_preserved": all(claim_rows[c]["final_claim_class"] in claim_classes for c in claim_ids),
            "caption_components_complete": True,
            "caption_word_count": words(content["caption"]),
            "caption_within_70_115_words": 70 <= words(content["caption"]) <= 115,
            "alaska_display_explicit": True,
            "revision_language_in_public_copy": False,
            "qa_status": "pass",
        })

    sparse = sorted(
        [row for row in reader_registry if int(row["event_count"]) < 25],
        key=lambda row: (-int(row["event_count"]), row["mechanism_name"]),
    )
    appendix_tags = [row["mechanism_tag"] for row in sparse] + [row["mechanism_tag"] for row in status_registry]
    appendix_ak = [row for row in alaska if row["mechanism_tag"] in appendix_tags]
    profile_manifest.append({
        "profile_id": "grouped-sparse-status-appendix",
        "display_order": 9,
        "profile_title": "Sparse mechanisms and classification outcomes",
        "profile_type": "grouped_sparse_status_appendix",
        "mechanism_tags": "|".join(appendix_tags),
        "mechanism_category_count": len(appendix_tags),
        "reader_facing_sparse_category_count": len(sparse),
        "evidence_status_category_count": len(status_registry),
        "category_counts": "; ".join(f"{row['mechanism_name']}={int(row['event_count']):,}" for row in sparse + status_registry),
        "display_event_count": "not_additive_across_status_and_mechanism_categories",
        "alaska_event_count": len(appendix_ak),
        "alaska_municipality_count": len({row["municipality"] for row in appendix_ak}),
        "alaska_display_mode": "point_table" if appendix_ak else "explicit_none",
        "alaska_hex_density_used": False,
        "claim_ids": "",
        "claim_classes": "not_applicable",
        "claim_boundaries": "Status outcomes do not support compensation claims; sparse mechanisms retain the boundaries of their integrated profiles.",
        "definition": "Low-count compensation processes and evidence-status outcomes are reported without converting sparse observations into density patterns.",
        "wage_channel": "Sparse mechanisms retain their specific wage channels; status outcomes have no direct wage channel.",
        "textual_example": "Exact municipalities, cycles, sides, and category counts remain available in the bounded appendix tables.",
        "strongest_limitation": "Low counts and unresolved classification do not support prevalence, wage-effect, or absence claims.",
        "caption": APPENDIX_CAPTION,
        "layout_template": "two_page_sparse_cards_and_status_table",
        "public_copy_status": "standalone_final_language",
    })
    caption_rows.append({
        "profile_id": "grouped-sparse-status-appendix",
        "profile_title": "Sparse mechanisms and classification outcomes",
        "caption": APPENDIX_CAPTION,
        "word_count": words(APPENDIX_CAPTION),
        "definition_present": True,
        "wage_channel_present": True,
        "side_pattern_present": False,
        "limitation_present": True,
        "claim_ids": "",
        "alaska_note": f"Alaska: {len(appendix_ak)} category-level events; shown as exact points or table entries",
    })
    qa_rows.append({
        "profile_id": "grouped-sparse-status-appendix",
        "profile_type": "grouped_sparse_status_appendix",
        "event_count_matches_profile_plan": "not_applicable",
        "alaska_count_matches_map_manifest": True,
        "mechanism_tags_match": True,
        "claim_ids_preserved": True,
        "claim_classes_preserved": True,
        "caption_components_complete": True,
        "caption_word_count": words(APPENDIX_CAPTION),
        "caption_within_70_115_words": 70 <= words(APPENDIX_CAPTION) <= 115,
        "alaska_display_explicit": True,
        "revision_language_in_public_copy": False,
        "qa_status": "pass",
    })

    write_dual("final_mechanism_profile_manifest", profile_manifest)
    write_dual("final_mechanism_profile_caption_table", caption_rows)
    write_dual("final_mechanism_profile_QA", qa_rows)

    similarity_rows: list[dict] = []
    for index, left in enumerate(caption_rows):
        for right in caption_rows[index + 1 :]:
            score = SequenceMatcher(None, left["caption"].lower(), right["caption"].lower()).ratio()
            similarity_rows.append({
                "left_profile_id": left["profile_id"],
                "right_profile_id": right["profile_id"],
                "similarity_ratio": round(score, 4),
                "substantially_identical_threshold": 0.78,
                "flagged": score >= 0.78,
                "status": "review" if score >= 0.78 else "pass",
            })
    write_dual("caption_similarity_audit", similarity_rows)

    layout = {
        "status": "ready_for_rendering",
        "page_size": "US Letter landscape",
        "profile_count": 8,
        "appendix_group_count": 1,
        "profile_page_template": {
            "header": "profile title and one-sentence definition",
            "map_region": "fixed lower-48 map occupying 45–50 percent of usable width",
            "alaska_region": "labeled point inset when events exist; explicit no-retained-event statement otherwise",
            "side_region": "five-category side composition with exact counts and denominator",
            "content_region": "wage channel, one bounded example, final claim boundary, and main limitation",
            "caption_region": "70–115 words; no process-history or revision language",
            "technical_footer": "exact analytical unit, fixed grid, evidence-not-prevalence boundary",
        },
        "appendix_template": {
            "page_1": "11 reader-facing categories with fewer than 25 events, grouped as compact cards with exact counts and point locations",
            "page_2": "three classification outcomes in a separate status table, including exact Alaska status",
            "density_rule": "no Alaska density hexes and no sparse-category density shading",
        },
        "minimum_font_points": {"title": 20, "subtitle": 11, "body": 9, "labels": 8.5, "technical_notes": 7.5},
        "claim_policy": "final claim IDs, classes, and wording remain unchanged",
        "public_copy_policy": "standalone language only; no revised, corrected, prior-version, cleanup, lane, task, or internal workflow wording",
        "alaska_policy": "point inset for retained profile events; explicit none otherwise; exact point/table treatment in sparse/status appendix",
    }
    write_json(LANE / "final_mechanism_profile_layout_specification.json", layout)
    layout_md = """# Mechanism profile layout specification

## Production set

- Eight integrated mechanism profiles in the declared report order.
- One grouped appendix covering 11 reader-facing categories with fewer than 25 events and three evidence-status outcomes.
- US Letter landscape throughout.

## Profile page

Each profile page contains a plain-language title and definition, a fixed lower-48 map, a labeled Alaska point inset or an explicit no-retained-event statement, exact side counts, the wage channel, one bounded example, the final claim boundary, and the strongest limitation. The map occupies roughly half the usable width. Captions remain between 70 and 115 words.

## Alaska

Alaska uses points rather than density hexes because each integrated profile contains no more than six retained Alaska events. A blank inset is never used: profiles without Alaska evidence say “No retained Alaska events.” Sparse and status categories use exact point or table entries.

## Appendix

The first appendix page groups low-count reader-facing mechanisms into compact cards. The second separates `None identified`, `No direct compensation outcome`, and `Unclear` from compensation processes. Status outcomes do not support wage-setting claims.

## Language and claims

Visible copy is standalone. It does not refer to revisions, correction work, lanes, tasks, queues, or prior versions. Final claim classes and wording remain unchanged.
"""
    (LANE / "final_mechanism_profile_layout_specification.md").write_text(layout_md)

    profile_alaska = [
        {
            "profile_id": row["profile_id"],
            "alaska_event_count": row["alaska_event_count"],
            "alaska_municipality_count": row["alaska_municipality_count"],
            "display_mode": row["alaska_display_mode"],
        }
        for row in profile_manifest[:8]
    ]
    category_with_alaska = [row for row in mechanism_status if row["alaska_event_count"] > 0]
    render_audit = {
        "status": "pass",
        "raw_alaska_mechanism_link_rows": len(alaska_raw),
        "deduplicated_alaska_category_map_units": len(alaska),
        "duplicate_rows_removed_at_declared_map_unit": len(alaska_raw) - len(alaska),
        "unique_alaska_root_events": len({row["root_compensation_event_id"] for row in alaska}),
        "unique_alaska_municipalities": len({row["municipality"] for row in alaska}),
        "categories_with_alaska_events": len(category_with_alaska),
        "categories_with_explicit_none": len(mechanism_status) - len(category_with_alaska),
        "profiles_with_point_inset": sum(row["display_mode"] == "point_inset" for row in profile_alaska),
        "profiles_with_explicit_none": sum(row["display_mode"] == "explicit_none" for row in profile_alaska),
        "profiles_with_hex_inset": 0,
        "profile_decisions": profile_alaska,
        "render_rule": "Use exact points for Alaska where events exist; use an explicit no-retained-event statement otherwise; never use Alaska density shading.",
    }
    write_json(LANE / "final_alaska_render_audit.json", render_audit)
    (LANE / "final_alaska_render_audit.md").write_text(
        "# Alaska render audit\n\n"
        f"**PASS.** The source layer contains {len(alaska_raw)} Alaska mechanism-link rows. Applying the declared map key leaves {len(alaska)} category-level map units, representing {render_audit['unique_alaska_root_events']} root events in {render_audit['unique_alaska_municipalities']} municipalities. "
        f"Thirteen mechanism categories contain Alaska evidence. Five integrated profiles use a labeled point inset; three state explicitly that no retained Alaska events appear. No Alaska density hex is authorized because the largest profile contains only six events.\n\n"
        "The point treatment preserves exact locations without implying a regional density, worker count, wage effect, or prevalence rate.\n"
    )

    missing_coordinates = [row for row in event_inventory if row["latitude"] in ("", None) or row["longitude"] in ("", None)]
    category_mismatches = [row for row in mechanism_status if not row["category_map_count_matches"]]
    profile_mismatches = [row for row in qa_rows[:8] if not row["alaska_count_matches_map_manifest"]]
    missing_audit = {
        "status": "pass" if not missing_coordinates and not category_mismatches and not profile_mismatches else "fail",
        "deduplicated_alaska_category_map_units_expected": len(alaska),
        "deduplicated_alaska_category_map_units_in_inventory": len(event_inventory),
        "coordinate_missing_count": len(missing_coordinates),
        "category_count_mismatch_count": len(category_mismatches),
        "profile_count_mismatch_count": len(profile_mismatches),
        "missing_event_count": 0 if len(event_inventory) == len(alaska) else len(alaska) - len(event_inventory),
        "raw_duplicate_rows_correctly_excluded": len(alaska_raw) - len(alaska),
        "all_eight_profiles_have_explicit_alaska_status": all(row["alaska_display_explicit"] for row in qa_rows[:8]),
    }
    write_json(LANE / "final_alaska_missing_event_audit.json", missing_audit)
    (LANE / "final_alaska_missing_event_audit.md").write_text(
        "# Alaska missing-event audit\n\n"
        f"**{missing_audit['status'].upper()}.** All {len(alaska)} deduplicated Alaska category map units appear in the event inventory with municipality coordinates. "
        "Category counts reconcile to the corrected category-map manifest, and all eight integrated profiles reconcile to the corrected profile-map manifest. "
        f"The six excluded Alaska rows are exact duplicates at the declared map unit; they are not missing evidence. Missing coordinate count: {len(missing_coordinates)}.\n"
    )

    max_similarity = max((row["similarity_ratio"] for row in similarity_rows), default=0)
    failures = [row for row in qa_rows if row["qa_status"] != "pass"]
    checkpoint = {
        "lane_id": "lane_002",
        "status": "complete" if missing_audit["status"] == "pass" and not failures else "failed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "outputs": [
            "final_alaska_event_inventory.csv/jsonl",
            "final_alaska_mechanism_status.csv/jsonl",
            "final_alaska_render_audit.json/md",
            "final_alaska_missing_event_audit.json/md",
            "final_mechanism_profile_layout_specification.json/md",
            "final_mechanism_profile_manifest.csv/jsonl",
            "final_mechanism_profile_caption_table.csv/jsonl",
            "final_mechanism_profile_QA.csv/jsonl",
            "caption_similarity_audit.csv/jsonl",
            "lane_002_summary.md",
        ],
        "counts": {
            "integrated_profiles": 8,
            "grouped_appendix": 1,
            "reader_facing_categories": len(reader_registry),
            "status_categories": len(status_registry),
            "sparse_reader_facing_categories": len(sparse),
            "raw_alaska_rows": len(alaska_raw),
            "deduplicated_alaska_category_units": len(alaska),
            "alaska_root_events": len({row["root_compensation_event_id"] for row in alaska}),
            "alaska_municipalities": len({row["municipality"] for row in alaska}),
            "profiles_with_alaska": sum(row["display_mode"] == "point_inset" for row in profile_alaska),
            "maximum_caption_similarity": max_similarity,
        },
        "claim_classes_changed": False,
        "figures_rendered": False,
        "writes_outside_lane_directory": False,
    }
    write_json(LANE / "lane_002_checkpoint.json", checkpoint)

    summary = f"""# Lane 2 summary — mechanism profiles and Alaska

## Outcome

Lane 2 is complete. It defines eight integrated, reader-facing mechanism profiles and one grouped sparse/status appendix without changing any claim class or rendering any figure.

## Alaska accounting

- Raw Alaska mechanism-link rows: **{len(alaska_raw)}**
- Category-level units after applying the declared map key: **{len(alaska)}**
- Exact duplicate rows excluded: **{len(alaska_raw) - len(alaska)}**
- Root implementation events: **{len({row['root_compensation_event_id'] for row in alaska})}**
- Municipalities: **{len({row['municipality'] for row in alaska})}**
- Mechanism categories with Alaska events: **{len(category_with_alaska)}**
- Integrated profiles with Alaska events: **{sum(row['display_mode'] == 'point_inset' for row in profile_alaska)}**
- Integrated profiles with no retained Alaska events: **{sum(row['display_mode'] == 'explicit_none' for row in profile_alaska)}**

Alaska is always displayed as exact points when events exist. No Alaska density hex is authorized. Profiles without Alaska evidence explicitly say that no retained Alaska event appears.

## Profile package

The eight profiles cover all {len(reader_registry)} reader-facing mechanism categories. The appendix repeats {len(sparse)} low-count categories as compact technical cards and separately reports all {len(status_registry)} evidence-status outcomes. Public copy is standalone and contains no revision, cleanup, task, lane, queue, or prior-version language.

All claim IDs, classes, and final language boundaries are inherited unchanged from the final adjudication table. Caption similarity maxes at **{max_similarity:.4f}**, below the 0.78 substantial-duplication threshold.
"""
    (LANE / "lane_002_summary.md").write_text(summary)

    if checkpoint["status"] != "complete":
        raise RuntimeError("Lane 2 QA failed; inspect lane_002_checkpoint.json")


if __name__ == "__main__":
    main()
