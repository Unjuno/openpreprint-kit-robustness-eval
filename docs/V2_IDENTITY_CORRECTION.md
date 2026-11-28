# Identity correction for the v2.0.1 candidate

The immutable v2.0.0 GitHub Release cannot be edited. Its archived metadata declares `version: v2`, which does not match its public tag `v2.0.0`; the identity-bound verifier therefore rejects the release. This candidate changes the bundle metadata version to `v2.0.1` so a future release tag and embedded metadata can agree.

This is a metadata identity correction candidate. It does not alter the existing v1.0.0 or v2.0.0 Releases, and it does not authorize creating or publishing v2.0.1. The PDF contents remain the approved v2 manuscript. A new immutable publication must wait for explicit owner authorization and exact-head CI/verification.
