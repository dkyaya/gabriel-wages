# Source-library portability audit

- Status: **pass**.
- Current source pointers checked: **26,799**; absolute or traversal pointers: **0**.
- Proposed library paths: **26,637**; unique: **26,637**.
- Absolute proposed paths: **0**.
- Parent-traversal proposed paths: **0**.
- Backslash-based proposed paths: **0**.
- Case-insensitive proposed-path collisions: **0**.
- Maximum proposed path length: **82 characters**.

Recipient tools must accept a library root and resolve POSIX member paths beneath it. Historical repository paths may be retained as provenance fields, but no tool may depend on the original machine, username, home directory, or repository location.
