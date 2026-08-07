# Portability audit

Pass. No tracked file contains the original machine's absolute repository path, a user-specific home path, or a hard-coded cloud location. `config/local_paths.toml` is absent and ignored. The tracked example uses a relative path. The source corpus is external and configurable at any location. No Git remote is configured. Core tools use the Python standard library.
