# Archive transfer requirements

The historical Git bundle and compact summer record must be placed in durable private storage and independently rehashed before cleanup. The clean bundle and source snapshot are recommended fallbacks. `FINAL_HANDOFF_ARCHIVE_CHECKSUMS.sha256` is the comparison manifest. Archive creation, archive transfer, and destructive cleanup are separate approvals. Current cleanup authorization: **none**.
