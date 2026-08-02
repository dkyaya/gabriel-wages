import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_remaining_municipality_span_extraction.py")
SPEC = importlib.util.spec_from_file_location("remaining_span", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_required_queue_and_lane_contract():
    rows = MODULE.read_csv(MODULE.INPUT / "span_extraction_ready_queue.csv")
    assert len(rows) == 2366
    assert len({row["extraction_id"] for row in rows}) == 2366
    assert {row["extraction_status"] for row in rows} == {"extracted_ok"}
    assert MODULE.LANES == {
        "span_extraction_lane_001": 474,
        "span_extraction_lane_002": 473,
        "span_extraction_lane_003": 473,
        "span_extraction_lane_004": 473,
        "span_extraction_lane_005": 473,
    }


def test_mixed_cola_mapping_retains_quant_and_qual():
    base = {
        "evidence_category": "mixed_quantitative_qualitative",
        "quant_span_types": "COLA_or_CPI_adjustment|percentage_raise",
        "qualitative_mechanism_span_types": "automatic_CPI_COLA_or_indexing",
        "exact_span_text": "Employees receive a 3% COLA indexed to CPI.",
        "source_family": "cba",
    }
    assert MODULE.mapped_categories(base) == [
        "quant_cpi_indexed_adjustment",
        "quant_percentage_raise_or_cola",
        "qual_cola_or_indexing_mechanism",
    ]


def test_conservative_safety_side_hinting():
    assert MODULE.safety_hint("Police officers receive $32.00 per hour.") == "police"
    assert MODULE.safety_hint("Firefighters receive a step increase.") == "fire"
    assert MODULE.safety_hint("Police and fire employees share a plan.") == "safety_combined"
    assert MODULE.safety_hint("Firefighters and clerical employees share a schedule.") == "mixed"
    assert MODULE.safety_hint("General employees receive a raise.") == "non_safety"
    assert MODULE.safety_hint("Municipal compensation language.") == "unclear"


def test_snippet_limit_uses_smaller_existing_standard():
    assert MODULE.MAX_SNIPPET == 800
    assert MODULE.MAX_SNIPPET < 1200


def test_nonbase_passage_keeps_component_and_mechanism_views():
    base = {
        "evidence_category": "non_base_compensation",
        "quant_span_types": "longevity_pay",
        "qualitative_mechanism_span_types": "",
        "exact_span_text": "Employees receive longevity pay.",
        "source_family": "cba",
    }
    assert MODULE.mapped_categories(base) == [
        "quant_longevity_or_service_pay",
        "qual_non_base_compensation_mechanism",
    ]
