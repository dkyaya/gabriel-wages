# Public-link validation

The final atlas assets were committed and pushed to `origin/main` in content commit `833ab96315d4fdd12df5f6873bc3dcf6ee6cdbcb`. The raw GitHub PDF returned HTTP 200 with the expected 2,369,807-byte content length. Its SHA-256, `e5260ee42a70081e166120b337a789c2e1663631755baa99e585c8d75939e8b8`, exactly matched the committed local PDF. The GitHub Pages landing path returned HTTP 404 while deployment workflow run 31126967034 remained queued.

Result: **deployment pending**. This does not invalidate the locally verified PDF. The raw GitHub PDF is available while the Pages runner is pending.
