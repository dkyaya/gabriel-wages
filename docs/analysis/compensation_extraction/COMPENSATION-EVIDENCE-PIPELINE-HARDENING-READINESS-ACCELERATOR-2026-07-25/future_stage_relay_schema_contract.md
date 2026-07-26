# Future stage relay schema contract

Every relay must include nonblank `commit_hash`, `push_status`, `validation_results`, `dashboard_status`, `forbidden_action_confirmations`, and `next_recommendation`, plus decision/summary, blocker and invariant summaries, git status/log, and the authorized future prompt. Relays must exclude PDFs, images, full page/document text, full tables, raw prompts/responses, secrets, binary builds, and unrelated lockfiles. Relay creation must fail closed when a required inspection field is absent.
