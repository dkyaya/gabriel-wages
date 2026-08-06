#!/usr/bin/env python3
"""Promote the final native-text atlas without disturbing archived reports."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/dashboard/data"


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    reports_path = DATA / "reports_index.json"
    report_payload = json.loads(reports_path.read_text())
    reports = report_payload["reports"]
    final_id = "gabriel-wages-visual-atlas-final-2026-08-06"

    for report in reports:
        if report.get("id") == "gabriel-wages-visual-atlas-revised-2026-08-06":
            report["current"] = False
            report["historical"] = True
            report["tags"] = [tag for tag in report.get("tags", []) if tag != "current"]

    reports = [report for report in reports if report.get("id") != final_id]
    reports.insert(0, {
        "id": final_id,
        "title": "Gabriel Wages Visual Atlas",
        "report_type": "Primary project and handoff visual atlas",
        "date": "2026-08-06",
        "checkpoint": "Native-text publication; 60 pages; complete page-render and theme QA",
        "summary": "A visual-first summary of the municipal compensation mechanisms, evidence, final claim boundaries, methodology, and project-wide limitations.",
        "tags": ["current", "handoff", "visual atlas", "native text", "PDF"],
        "current": True,
        "historical": False,
        "href": "gabriel-wages/reports/gabriel_wages_visual_atlas_final_2026-08-06/",
        "link_label": "Open atlas",
        "secondary_href": "gabriel-wages/reports/gabriel_wages_visual_atlas_final_2026-08-06/gabriel_wages_visual_atlas_final_2026-08-06.pdf",
        "secondary_link_label": "Open PDF",
        "scope_metrics": [
            {"label": "integrated profiles", "value": 8},
            {"label": "claims", "value": 14},
            {"label": "PDF pages", "value": 60},
        ],
    })
    report_payload["reports"] = reports
    write_json(reports_path, report_payload)

    phase_path = DATA / "project_phase_summary.json"
    phase = json.loads(phase_path.read_text())
    phase.update({
        "current_phase": "Final visual atlas complete; source-library streaming split-volume packaging is next",
        "final_visual_atlas_current_stage": "Final visual atlas complete",
        "final_visual_atlas_next_stage": "Source-library streaming split-volume packaging",
        "final_visual_atlas_page": "/gabriel-wages/reports/gabriel_wages_visual_atlas_final_2026-08-06/",
        "final_visual_atlas_pdf": "/gabriel-wages/reports/gabriel_wages_visual_atlas_final_2026-08-06/gabriel_wages_visual_atlas_final_2026-08-06.pdf",
        "final_visual_atlas_page_count": 60,
        "final_visual_atlas_native_text_pdf": True,
        "final_visual_atlas_reader_guide_consolidated": True,
        "final_visual_atlas_alaska_validated": True,
        "final_visual_atlas_cross_mechanism_section_removed": True,
        "final_visual_atlas_claim_matrix_redesigned": True,
        "final_visual_atlas_page_render_qa_passed": True,
        "final_visual_atlas_theme_qa_passed": True,
        "final_visual_atlas_prior_versions_preserved": True,
        "source_library_packaging_started": False,
        "source_library_no_full_copy_policy_active": True,
    })
    write_json(phase_path, phase)


if __name__ == "__main__":
    main()
