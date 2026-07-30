# Resumability report

Every target has a terminal child artifact before it enters the atomic lane checkpoint. Completed targets are skipped, completed lanes cannot rerun, and incomplete lanes resume from their own locked hash/checkpoint only.
