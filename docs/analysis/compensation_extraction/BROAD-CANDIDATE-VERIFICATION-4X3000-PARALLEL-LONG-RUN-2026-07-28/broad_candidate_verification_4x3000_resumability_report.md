# Resumability report

Each worker appends one durable result row and rewrites a compact checkpoint after every locator. Completed lanes refuse rerun; incomplete lanes resume from the committed row-ID set after queue-hash validation.
