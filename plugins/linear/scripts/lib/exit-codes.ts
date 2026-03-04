/**
 * Distinct exit codes for SDK scripts
 * Enables programmatic error handling and automation
 */
export const EXIT_CODES = {
  SUCCESS: 0,
  MISSING_API_KEY: 1,
  INVALID_ARGUMENTS: 2,
  RESOURCE_NOT_FOUND: 3,
  API_ERROR: 4,
  VALIDATION_ERROR: 5,
  PERMISSION_DENIED: 6,
} as const;

export type ExitCode = (typeof EXIT_CODES)[keyof typeof EXIT_CODES];
