# Historical Git bundle audit

The private all-refs bundle is **14,830,010,689 bytes** with SHA-256 `cddc30c978b02f19bb5041858cd4388c5501ad6fa71abd033e2bfad673066533`. It advertises 34 refs, including 23 local branches, the freeze tag, remote-tracking refs, worktree refs, and the historical stash. `git bundle verify` reports complete history.

A bounded bare clone passed `git fsck --full`; `main`, the freeze tag, and representative commits resolved. The clone imported 23 branch heads plus the tag. Git reported the stash commit as dangling in the clone because normal bundle cloning does not install `refs/stash`, while the original bundle still advertises and preserves that ref. This is documented, not an integrity failure.

The bundle does not preserve ignored/untracked artifacts. Original sources remain protected by the separate 28-volume source library. Remote transfer of this bundle is still pending.
