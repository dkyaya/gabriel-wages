# Extraction disk-capacity methodology

Representative extraction samples covered normal and low-text PDFs, normal/table/structured HTML, CSV, and text. Full artifacts are written as deterministic per-payload gzip streams and never assembled into a monolith. Production stops before the 8 GiB reserve is threatened; retained evidence is never deleted to create room.
