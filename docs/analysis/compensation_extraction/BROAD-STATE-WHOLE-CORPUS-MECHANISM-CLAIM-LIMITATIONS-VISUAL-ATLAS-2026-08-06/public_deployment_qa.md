# Public deployment QA

Status: **PASS**

- Landing page: HTTP 200; expected title, PDF controls, counts, prior-gallery link, and dashboard link present.
- PDF: HTTP 200; 8,709,892 bytes.
- Public and committed PDF SHA-256: `4a38a78cf5be4db2960dfe89953c446f8d56eaed4ec2c0fafff3f99bd1591fa7`.
- Dashboard: atlas card present; primary map remains `scout_coverage_rate`; prior visual-review gallery preserved.

GitHub Pages finished publishing asynchronously after the action-side poller timed out while the backend still reported `deployment_queued`. The public HTTP responses and matching PDF checksum establish successful publication.
