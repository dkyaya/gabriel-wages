# Exact-span rating queue design

Only validated `span_extracted` records enter the queue. Each has exact offsets and hashes, at most 600 exact-span characters, and at most 500 context characters. Ambiguous and no-span sources are excluded. Rating is a separately authorized bounded task.
