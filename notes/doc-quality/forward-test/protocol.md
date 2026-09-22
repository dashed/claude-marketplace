# Upload protocol

## Retry policy

This fictional source is provided for an offline skill forward test.

The worker must call upload_snapshot() only while snapshot_uploads_enabled is true. On HTTP 503, retry at most 2 times with at least 750 ms between attempts, unless cancellation was requested; then stop without another request. Never retry HTTP 400. Payloads cannot exceed 8 MiB (8388608 bytes). After retry exhaustion, record failure and retain the local snapshot. Losing the cancellation signal can leave a job waiting for a retry. HTTP 503 after server-side commit is not characterized, so duplicate processing remains a known risk. No canary evidence exists yet.
