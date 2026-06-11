/**
 * Typed Linear error handling
 *
 * Centralizes error formatting around the SDK's `LinearError` hierarchy so that
 * catch blocks surface useful, structured information (error type, the first
 * per-error message, HTTP status, and rate-limit retry timing) instead of an
 * opaque `error.message`.
 */
import { LinearError, LinearErrorType, RatelimitedLinearError } from '@linear/sdk';

/**
 * Format any caught value into a human-readable, single-line-friendly message.
 *
 * For `LinearError` instances this surfaces the error type, the first
 * per-error message (the SDK exposes user-presentable text there), the HTTP
 * status, and—for rate-limit errors—the retry-after delay. Falls back to the
 * standard `Error.message`/`String(error)` for non-Linear errors.
 */
export function formatLinearError(error: unknown): string {
  if (error instanceof LinearError) {
    const parts: string[] = [];

    if (error.type) {
      parts.push(`[${error.type}]`);
    }

    // The first per-error message is the most user-presentable text the SDK
    // exposes; fall back to the top-level message otherwise.
    const detail = error.errors?.[0]?.message || error.message;
    if (detail) {
      parts.push(detail);
    }

    if (typeof error.status === 'number') {
      parts.push(`(HTTP ${error.status})`);
    }

    if (error instanceof RatelimitedLinearError && error.retryAfter !== undefined) {
      parts.push(`- retry after ${error.retryAfter}s`);
    }

    return parts.join(' ') || 'Unknown Linear API error';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return String(error);
}

/**
 * Whether a caught error is transient and worth retrying.
 *
 * Currently true for rate-limit and network errors.
 */
export function isRetryableLinearError(error: unknown): boolean {
  if (error instanceof RatelimitedLinearError) {
    return true;
  }
  if (error instanceof LinearError) {
    return (
      error.type === LinearErrorType.Ratelimited || error.type === LinearErrorType.NetworkError
    );
  }
  return false;
}
