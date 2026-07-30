# Pages smoke status reconciliation

Mismatch present: **true**.

The prior public smoke was successful. The mismatch was a derived relay aggregation bug: the relay builder tested the controlled enum `public_pages_visible_current_passed` against `passed`. The public smoke report is the authoritative source, corroborated by validation check 30 and the recorded Pages workflow/browser evidence.
