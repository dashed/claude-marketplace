import { describe, it, expect } from 'vitest';
import { EXIT_CODES } from '../scripts/lib/exit-codes';

describe('EXIT_CODES', () => {
  it('defines SUCCESS as 0', () => {
    expect(EXIT_CODES.SUCCESS).toBe(0);
  });

  it('defines MISSING_API_KEY as 1', () => {
    expect(EXIT_CODES.MISSING_API_KEY).toBe(1);
  });

  it('defines INVALID_ARGUMENTS as 2', () => {
    expect(EXIT_CODES.INVALID_ARGUMENTS).toBe(2);
  });

  it('defines RESOURCE_NOT_FOUND as 3', () => {
    expect(EXIT_CODES.RESOURCE_NOT_FOUND).toBe(3);
  });

  it('defines API_ERROR as 4', () => {
    expect(EXIT_CODES.API_ERROR).toBe(4);
  });

  it('defines VALIDATION_ERROR as 5', () => {
    expect(EXIT_CODES.VALIDATION_ERROR).toBe(5);
  });

  it('defines PERMISSION_DENIED as 6', () => {
    expect(EXIT_CODES.PERMISSION_DENIED).toBe(6);
  });

  it('has unique exit code values', () => {
    const values = Object.values(EXIT_CODES);
    const uniqueValues = new Set(values);
    expect(uniqueValues.size).toBe(values.length);
  });

  it('has all numeric values', () => {
    for (const value of Object.values(EXIT_CODES)) {
      expect(typeof value).toBe('number');
    }
  });
});
