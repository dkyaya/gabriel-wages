# Resumability report

Every lane retains an append-only result ledger, a per-row checkpoint, and a resume-state JSON. A rerun skips identities already present only after proving they belong to that lane's immutable locked queue. The coordinator rejects partial lanes and any identity mismatch, so partial outputs cannot masquerade as complete.
