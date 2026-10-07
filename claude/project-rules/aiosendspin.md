# aiosendspin

- When the spec renames or removes a field, keep accepting the old form, call `flag_noncompliance`, and reject it only when `allow_noncompliant_clients=False`.
- In strict mode, validate before any side effect (marking connected, applying `available`, emitting events).
- Before done, check that behavior with every option at its default is unchanged apart from the intended change: the same clients are accepted and the wire output is the same. Also check the public API for removed or renamed symbols, changed signatures, and new abstract methods on stores. Report both results in one line each, and call out anything that breaks the API or the wire format, such as a previously working client that can no longer connect.
- Throttle warnings on hot paths (first at warning, then rate-limited). No per-chunk debug logs.
- No tests that depend on the ffmpeg build installed in CI.
- Before a compliance review, fetch `~/projects/music-assistant/sendspin-spec` and name the spec commit you compared against.
- Keep the library generic. No features that only Music Assistant needs.
- In reviews, keep server-side and client library findings apart. Client gaps that are still spec-compliant, like optional fields not used yet, go to a follow-up instead of the review.
