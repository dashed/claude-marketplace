# Snapshot upload rollout

## Upload retries

During rollout, the worker MUST apply `upload_snapshot()` only when `snapshot_uploads_enabled` is true and, because losing the cancellation signal can leave a job waiting for a retry, when the server returns HTTP 503 it MUST retry at most 2 times with at least 750 ms between attempts unless cancellation has been requested, in which case it MUST stop without sending another request; HTTP 400 MUST NOT be retried, the payload MUST be at most 8 MiB, and after those retries are exhausted the worker MUST record a failed upload rather than deleting the local snapshot. Whether HTTP 503 can be returned after the server commits an upload is unverified, so duplicate processing remains a known risk. Preserve the settings below and follow [Upload protocol](protocol.md#retry-policy).

```json
{"max_retries": 2, "min_backoff_ms": 750, "max_body_bytes": 8388608}
```

## Rollout evidence

Record observed retries and cancellation outcomes during the canary. No canary result has been collected yet.
