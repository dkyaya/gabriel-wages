# Public-link validation

The methodology prose replacement is pushed to `origin/main` at content commit `59a1bfc926108a2a5591980a9b4efd048115a902`.

A fresh download from the raw GitHub URL returned the 58-page PDF and matched the committed SHA-256 exactly: `781adb2ffe047d8a8523fcf3a65e743917bb1a3e0ca00c7df0f8c85a035a9b76`.

The GitHub Pages URL returned HTTP 404 during this audit. A dashboard deployment was dispatched and remained in progress during the repository-checkout step. Pages is therefore recorded as deployment pending, not as a PDF failure.
