/**
 * Utility functions for form validation and data cleaning
 */

/**
 * Converts a value to a number or null
 * Handles empty strings, whitespace, and invalid numbers
 */
export function toNumberOrNull(value: any): number | null {
  if (value === '' || value === null || value === undefined) {
    return null;
  }
  
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (trimmed === '') {
      return null;
    }
    const numValue = parseInt(trimmed, 10);
    return isNaN(numValue) || numValue < 0 ? null : numValue;
  }
  
  if (typeof value === 'number') {
    return isNaN(value) || value < 0 ? null : value;
  }
  
  return null;
}

/**
 * Converts a value to a string or null
 * Handles empty strings and whitespace
 */
export function toStringOrNull(value: any): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed === '' ? null : trimmed;
  }
  
  return String(value).trim() || null;
}

/**
 * Cleans sighting data by converting empty strings to null and validating types
 */
export function cleanSightingData(sighting: any): any {
  const cleaned = { ...sighting };
  
  // Numeric fields that should be converted to number or null
  const numericFields = ['small_group_size', 'large_group_size', 'breed_size', 'family_size'];
  numericFields.forEach(field => {
    cleaned[field] = toNumberOrNull(cleaned[field]);
  });

  // String fields that should be converted to string or null
  const stringFields = ['species', 'ring', 'reading', 'place', 'area', 'habitat', 'field_fruit', 'comment', 'melder', 'partner'];
  stringFields.forEach(field => {
    cleaned[field] = toStringOrNull(cleaned[field]);
  });

  return cleaned;
}

/**
 * Creates a numeric input handler that updates a reactive object
 */
export function createNumericInputHandler(target: any, field: string) {
  return (event: Event) => {
    const inputElement = event.target as HTMLInputElement;
    target[field] = toNumberOrNull(inputElement.value);
  };
}