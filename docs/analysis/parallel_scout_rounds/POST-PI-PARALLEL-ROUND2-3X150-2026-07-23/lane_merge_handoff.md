# POST-PI-PARALLEL-ROUND2-3X150-2026-07-23 — Post-Lane Merge Handoff

This handoff is a future coordinator boundary, not merge authorization.

1. Preserve every lane output and prove the locked input hashes against
   `docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/parallel_round_manifest.json`.
2. Run:

   ```bash
   python scripts/audit_parallel_scout_lanes.py \
     --manifest docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/parallel_round_manifest.json \
     --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/post_lane_audit
   ```

3. Review lane classifications, parseable/failure/stopped/candidate counts, completed
   ID overlap, and `merge_recommendation.md`.
4. If the recommendation is `merge_all_lanes`, stop and obtain authorization for the
   separate serial accounting task.
5. If it is `merge_completed_lanes_only_with_user_approval`, do not merge until the
   user explicitly accepts the changed round scope.
6. If it is `do_not_merge_until_resume_or_review`, preserve all artifacts and resolve
   lane lineage before accounting.

The auditor never runs shared builders. A later serial merge may rebuild queue and
coverage exactly once, then refresh yield learning and dashboard/project-phase JSON.
No lane independently commits or edits shared accounting.
