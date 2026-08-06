# Repository secret and path audit

- status: pass_with_reviewed_synthetic_fixture
- secret_pattern_file_count: 0
- reviewed_false_positive_count: 1
- environment_file_count: 0
- absolute_path_file_count: 89
- secret_values_in_outputs: False
- method: bounded redacted pattern scan of tracked text and representative temporary files

No secret value is reproduced in inventory output. Any match is represented only by file path, risk type, line number, and a redacted fingerprint.
