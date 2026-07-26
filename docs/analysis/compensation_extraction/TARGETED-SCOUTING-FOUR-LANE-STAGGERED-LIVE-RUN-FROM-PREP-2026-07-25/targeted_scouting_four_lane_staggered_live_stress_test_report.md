# Four-lane staggered live stress-test report

The focused suite covers missing artifacts, decision drift, queue hash drift, target-ID drift, count drift, cross-lane contamination, already-started rows, missing credentials, simultaneous starts, shortened offsets, schedule/no-overlap conflict, live-call bypass, candidate overpromotion, partial completion masquerading, forbidden status values, dashboard overpromotion, upstream mutation, and resume safety. The scheduling conflict is correctly treated as a preflight failure rather than weakened or silently ignored.
