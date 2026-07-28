# Future parallel lane execution standard

Large live scout runs default to four isolated worker lanes with starts at T+0, T+8, T+16, and T+24 minutes. Lanes overlap, checkpoint every target, use one bounded transport retry plus adaptive 3–15 second pacing, never read or write another lane, and never update dashboard/status/shared summaries. The coordinator alone validates, merges, deduplicates, updates dashboard/status/docs, commits, and pushes. Do not silently fall back to sequential execution.
