#!/usr/bin/env python3
"""Regression tests for deterministic four-lane targeted scouting dry prep."""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


runner = load("four_lane_prep", ROOT / "scripts/run_targeted_scouting_four_lane_prep_dry_run.py")
dashboard = load("dashboard_builder_four_lane", ROOT / "scripts/build_dashboard_data.py")


class InputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = runner.verify_inputs()
        cls.decision = runner.read_json(runner.INPUT_DIR / "provisional_claim_review_636_decision.json")
        cls.registry = runner.read_json(runner.INPUT_DIR / "provisional_claim_review_claim_registry_summary.json")

    def test_all_17_immutable_hashes_pass(self): self.assertEqual(self.audit["immutable_input_count"], 17)
    def test_hash_inventory_complete(self): self.assertEqual(set(self.audit["input_hashes"]), set(runner.EXPECTED_HASHES))
    def test_predecessor_decision_allows_prep(self): self.assertEqual(self.decision["decision"], "provisional_claim_review_completed_targeted_scouting_restart_recommended")
    def test_valid_scope_preserved(self): self.assertEqual(self.decision["valid_summary_rows"], 636)
    def test_excluded_scope_preserved(self): self.assertEqual(self.decision["excluded_quarantine_rows"], 7)
    def test_quantitative_lane_not_analyzed(self): self.assertEqual(self.decision["quantitative_rows_preserved_not_analyzed"], 862)
    def test_claim_registry_35(self): self.assertEqual(self.registry["claim_rows"], 35)
    def test_global_readiness_input_false(self): self.assertFalse(self.decision["global_analysis_readiness"])
    def test_city_coverage_hash_pinned(self): self.assertIn("data/city_coverage.csv", runner.EXPECTED_HASHES)
    def test_prior_candidate_hash_pinned(self): self.assertIn("docs/analysis/national_scout_candidate_queue_2026-07-20.csv", runner.EXPECTED_HASHES)
    def test_national_coverage_hash_pinned(self): self.assertIn("docs/analysis/national_scout_coverage_municipality_2026-07-20.csv", runner.EXPECTED_HASHES)


class QueueContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = runner.OUTPUT_DIR
        cls.master = runner.read_csv(cls.out / "targeted_scouting_four_lane_master_queue.csv")
        cls.lanes = {lane: [row for row in cls.master if row["lane_id"] == lane] for lane in runner.LANE_CONFIG}
        cls.summary = runner.read_json(cls.out / "targeted_scouting_four_lane_master_queue_summary.json")

    def test_master_exactly_2000(self): self.assertEqual(len(self.master), 2000)
    def test_exactly_four_lanes(self): self.assertEqual(set(self.lanes), set(runner.LANE_CONFIG))
    def test_each_lane_exactly_500(self): self.assertEqual({lane: len(rows) for lane, rows in self.lanes.items()}, {lane: 500 for lane in runner.LANE_CONFIG})
    def test_each_lane_within_cap(self): self.assertTrue(all(len(rows) <= 500 for rows in self.lanes.values()))
    def test_required_fields_exact(self): self.assertTrue(all(set(row) == set(runner.QUEUE_FIELDS) for row in self.master))
    def test_required_values_complete(self):
        optional = {"known_counterpart_id", "known_counterpart_unit_type"}
        self.assertTrue(all(all(row[field] for field in runner.QUEUE_FIELDS if field not in optional) for row in self.master))
    def test_target_ids_unique(self): self.assertEqual(len({row["scout_target_id"] for row in self.master}), 2000)
    def test_lane_ranks_complete(self):
        for rows in self.lanes.values(): self.assertEqual({int(row["target_rank"]) for row in rows}, set(range(1, 501)))
    def test_all_dry_validated(self): self.assertTrue(all(row["dry_run_status"] == "validated_no_call" for row in self.master))
    def test_all_live_not_started(self): self.assertTrue(all(row["live_run_status"] == "not_started" for row in self.master))
    def test_all_candidate_only_notes(self): self.assertTrue(all("candidate" in row["notes"] for row in self.master))
    def test_no_url_column(self): self.assertNotIn("source_url", runner.QUEUE_FIELDS)
    def test_no_url_payload(self): self.assertFalse(any("http://" in json.dumps(row).casefold() or "https://" in json.dumps(row).casefold() for row in self.master))
    def test_prior_seen_populated(self): self.assertTrue(all(row["prior_seen_status"] for row in self.master))
    def test_mechanism_populated(self): self.assertTrue(all(row["target_mechanism_family"] for row in self.master))
    def test_no_weak_padding(self): self.assertEqual(self.summary["weak_padding_rows"], 0)
    def test_high_quality_count(self): self.assertEqual(self.summary["high_quality_target_rows"], 2000)
    def test_duplicate_risk_counts(self): self.assertEqual(self.summary["duplicate_risk_counts"], {"low": 1828, "medium": 172})
    def test_prior_seen_count_reconciles(self): self.assertEqual(sum(self.summary["prior_seen_status_counts"].values()), 2000)
    def test_tier_counts_reconcile(self): self.assertEqual(sum(self.summary["match_priority_tier_counts"].values()), 2000)
    def test_upstream_duplicate_records_canonicalized(self): self.assertEqual(self.summary["upstream_duplicate_municipality_records_canonicalized"], 121)
    def test_upstream_duplicate_key_count(self): self.assertEqual(self.summary["upstream_duplicate_municipality_keys"], 86)
    def test_no_exact_duplicate_key(self):
        keys = [(r["state"], r["municipality"].casefold(), r["target_unit_type"], r["target_mechanism_family"], r["expected_contract_or_document_period"]) for r in self.master]
        self.assertEqual(len(keys), len(set(keys)))


class LaneDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        master = runner.read_csv(runner.OUTPUT_DIR / "targeted_scouting_four_lane_master_queue.csv")
        cls.lanes = {lane: [row for row in master if row["lane_id"] == lane] for lane in runner.LANE_CONFIG}

    def test_lane_1_primary_mechanism(self): self.assertTrue(all(r["target_mechanism_family"] == "non_safety_constraint_signal" for r in self.lanes["lane_1"]))
    def test_lane_1_targets_non_safety(self): self.assertTrue(all(r["target_unit_type"] == "non_safety_comparator" for r in self.lanes["lane_1"]))
    def test_lane_1_has_known_counterpart(self): self.assertTrue(all(r["known_counterpart_id"] for r in self.lanes["lane_1"]))
    def test_lane_1_all_tier_1(self): self.assertTrue(all(r["match_priority_tier"].startswith("tier_1") for r in self.lanes["lane_1"]))
    def test_lane_1_contains_core_cycle_gaps(self): self.assertGreaterEqual(sum(r["match_priority_tier"] == "tier_1_core_known_safety_cycle_gap" for r in self.lanes["lane_1"]), 1)
    def test_lane_2_primary_mechanism(self): self.assertTrue(all(r["target_mechanism_family"] == "strike_or_no_strike_constraint" for r in self.lanes["lane_2"]))
    def test_lane_2_bargaining_secondary(self): self.assertTrue(all("bargaining_power_signal" in r["secondary_mechanism_families"] for r in self.lanes["lane_2"]))
    def test_lane_3_primary_mechanism(self): self.assertTrue(all(r["target_mechanism_family"] == "fiscal_constraint_signal" for r in self.lanes["lane_3"]))
    def test_lane_3_non_safety_parity_gap(self):
        for row in self.lanes["lane_3"]:
            self.assertIn("non_safety_constraint_signal", row["secondary_mechanism_families"]); self.assertIn("parity_or_internal_equity_signal", row["secondary_mechanism_families"]); self.assertIn("gap_narrowing_signal", row["secondary_mechanism_families"])
    def test_lane_4_primary_mechanism(self): self.assertTrue(all(r["target_mechanism_family"] == "market_or_comparability_pressure" for r in self.lanes["lane_4"]))
    def test_lane_4_safety_rank_implementation(self):
        for row in self.lanes["lane_4"]:
            self.assertIn("safety_advantage_signal", row["secondary_mechanism_families"]); self.assertIn("rank_or_specialization_premium", row["secondary_mechanism_families"]); self.assertIn("implementation_or_retroactivity_advantage", row["secondary_mechanism_families"])
    def test_discovery_lanes_previously_unseen(self): self.assertTrue(all(r["prior_seen_status"] == "not_seen_in_consolidated_prior_scout_or_candidate_ledgers" for lane in ("lane_2", "lane_3", "lane_4") for r in self.lanes[lane]))
    def test_discovery_lanes_population_at_least_10000(self):
        for lane in ("lane_2", "lane_3", "lane_4"):
            for row in self.lanes[lane]: self.assertGreaterEqual(int(row["notes"].split("population=")[1].split(";")[0]), 10000)
    def test_discovery_municipalities_disjoint(self):
        rows = [r for lane in ("lane_2", "lane_3", "lane_4") for r in self.lanes[lane]]
        self.assertEqual(len(rows), len({(r["state"], r["municipality"].casefold()) for r in rows}))


class DuplicateAvoidanceFixtureTests(unittest.TestCase):
    def fixture(self, index: int, municipality: str | None = None, population: int = 20000) -> dict[str, str]:
        return {
            "state": "ZZ", "municipality": municipality or f"City {index:04d}",
            "municipality_id": f"fixture_{index:04d}", "population": str(population),
            "scout_coverage_status": "not_scouted", "queue_status": "not_scouted",
            "already_in_corpus": "no", "candidate_rows_total": "0",
        }

    def test_duplicate_same_name_government_is_canonicalized(self):
        rows = [self.fixture(i) for i in range(1500)]
        rows.append(self.fixture(9999, municipality="City 0000", population=25000))
        lanes = runner.build_discovery_lanes(rows, set())
        combined = [r for values in lanes.values() for r in values]
        self.assertEqual(len(combined), 1500)
        self.assertEqual(len({(r["state"], r["municipality"].casefold()) for r in combined}), 1500)

    def test_insufficient_pool_refuses_padding(self):
        with self.assertRaisesRegex(RuntimeError, "refusing weak padding"):
            runner.build_discovery_lanes([self.fixture(i) for i in range(1499)], set())

    def test_started_live_status_rejected(self):
        master = runner.read_csv(runner.OUTPUT_DIR / "targeted_scouting_four_lane_master_queue.csv")
        lanes = {lane: [copy.deepcopy(r) for r in master if r["lane_id"] == lane] for lane in runner.LANE_CONFIG}
        lanes["lane_2"][0]["live_run_status"] = "started"
        with self.assertRaisesRegex(RuntimeError, "dry/live state"):
            runner.validate_queue(lanes)

    def test_wrong_lane_mechanism_rejected(self):
        master = runner.read_csv(runner.OUTPUT_DIR / "targeted_scouting_four_lane_master_queue.csv")
        lanes = {lane: [copy.deepcopy(r) for r in master if r["lane_id"] == lane] for lane in runner.LANE_CONFIG}
        lanes["lane_3"][0]["target_mechanism_family"] = "market_or_comparability_pressure"
        with self.assertRaisesRegex(RuntimeError, "mechanism assignment"):
            runner.validate_queue(lanes)

    def test_missing_required_field_rejected(self):
        master = runner.read_csv(runner.OUTPUT_DIR / "targeted_scouting_four_lane_master_queue.csv")
        lanes = {lane: [copy.deepcopy(r) for r in master if r["lane_id"] == lane] for lane in runner.LANE_CONFIG}
        lanes["lane_4"][0]["prior_seen_status"] = ""
        with self.assertRaisesRegex(RuntimeError, "missing or extra"):
            runner.validate_queue(lanes)


class MaterializedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = runner.OUTPUT_DIR
        cls.decision = runner.read_json(cls.out / "targeted_scouting_four_lane_prep_decision.json")
        cls.invariants = runner.read_json(cls.out / "targeted_scouting_four_lane_prep_invariant_checks.json")

    def test_outputs_complete(self): self.assertTrue(runner.completed(self.out))
    def test_decision_exact(self): self.assertEqual(self.decision["decision"], runner.DECISION)
    def test_lane_1_live_ready(self): self.assertTrue(self.decision["lane_1_live_ready_next"])
    def test_no_lane_repair(self): self.assertEqual(self.decision["lanes_requiring_repair"], [])
    def test_prep_only(self): self.assertTrue(self.decision["prep_and_dry_run_only"])
    def test_no_live_runs(self): self.assertEqual(self.decision["live_hosted_search_runs"], 0)
    def test_no_model_calls(self): self.assertEqual(self.decision["model_or_api_calls"], 0)
    def test_global_readiness_false(self): self.assertFalse(self.decision["global_analysis_readiness"])
    def test_invariants_pass(self): self.assertTrue(self.invariants["all_invariants_passed"])
    def test_four_lockfiles_exist_and_hash(self):
        for lane in runner.LANE_CONFIG:
            lock = runner.read_json(self.out / "lane_lockfiles" / f"targeted_scouting_{lane}.lock.json")
            queue = self.out / f"targeted_scouting_{lane}_queue_500.csv"
            self.assertEqual(lock["queue_sha256"], runner.sha256(queue)); self.assertEqual(lock["live_run_status"], "not_started")
    def test_worker_prompts_exist(self):
        for lane in runner.LANE_CONFIG: self.assertTrue((self.out / "worker_prompts" / f"targeted_scouting_{lane}_live_prompt.md").is_file())
    def test_worker_prompts_preserve_phase_boundaries(self):
        for lane in runner.LANE_CONFIG:
            text = (self.out / "worker_prompts" / f"targeted_scouting_{lane}_live_prompt.md").read_text()
            for phrase in ("scouting is not verification", "Do not download documents", "Do not verify sources", "Keep global analysis readiness false"):
                self.assertIn(phrase, text)
    def test_future_prompt_lane_1_only(self):
        text = (self.out / "next_targeted_scouting_lane_1_live_prompt.md").read_text()
        self.assertIn("Do not start Lanes 2–4", text); self.assertIn("separate future task", text)
    def test_stagger_plan_sequential(self):
        text = (self.out / "targeted_scouting_four_lane_staggered_execution_plan.md").read_text()
        self.assertIn("60–90 minutes", text); self.assertIn("Never run more than one lane concurrently", text)
    def test_api_plan_no_automation(self):
        text = (self.out / "targeted_scouting_four_lane_api_protection_plan.md").read_text()
        self.assertIn("do not automate starts", text); self.assertIn("One live lane at a time", text)
    def test_no_raw_payload_files(self):
        names = [p.name.casefold() for p in self.out.rglob("*") if p.is_file()]
        self.assertFalse(any("raw_prompt" in name or "raw_response" in name for name in names))
    def test_runner_has_no_network_or_model_client(self):
        source = Path(runner.__file__).read_text()
        for token in ("requests.get(", "requests.post(", "urlopen(", "direct_sdk_batch(", "load_subscription_key(", "openai."):
            self.assertNotIn(token, source)
    def test_partial_outputs_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=runner.ANALYSIS_ROOT) as tmp:
            path = Path(tmp); (path / "partial.txt").write_text("partial")
            with self.assertRaisesRegex(RuntimeError, "partial outputs"):
                runner.output_guard(path, True)
    def test_resume_hashes_stable(self):
        before = {str(p.relative_to(self.out)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.rglob("*") if p.is_file()}
        self.assertTrue(runner.completed(self.out))
        after = {str(p.relative_to(self.out)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
    def test_stress_inventory_matches_report(self):
        inventory = runner.read_json(self.out / "targeted_scouting_four_lane_prep_regression_test_inventory.json")
        report = (self.out / "targeted_scouting_four_lane_prep_stress_test_report.md").read_text()
        self.assertIn(f"{inventory['failure_mode_count']}/{inventory['failure_mode_count']} passed", report)


class DashboardTests(unittest.TestCase):
    def test_dashboard_gate_passes(self):
        completed, decision = dashboard.targeted_scouting_four_lane_prep_status()
        self.assertTrue(completed); self.assertEqual(decision["master_queue_rows"], 2000)
    def test_dashboard_lane_1_ready(self):
        _, decision = dashboard.targeted_scouting_four_lane_prep_status(); self.assertTrue(decision["lane_1_live_ready_next"])
    def test_dashboard_global_readiness_false(self):
        _, decision = dashboard.targeted_scouting_four_lane_prep_status(); self.assertFalse(decision["global_analysis_readiness"])
    def test_dashboard_json_global_closed(self):
        readiness = runner.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        self.assertIn(readiness["overall_status"], {
            "targeted_scouting_four_lane_prep_dry_run_completed_lane_1_live_ready_global_analysis_closed",
            "targeted_scouting_four_lane_staggered_live_preflight_failed_repair_required_global_analysis_closed",
            "targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready_global_analysis_closed",
            "targeted_scouting_four_lane_candidate_review_completed_verification_ready_global_analysis_closed",
        })
        self.assertNotIn('"global_analysis_readiness": true', json.dumps(readiness, sort_keys=True).casefold())


if __name__ == "__main__":
    unittest.main(verbosity=2)
