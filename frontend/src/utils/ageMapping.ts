/**
 * Centralized age mapping for RINGING data only
 * Official ringing age codes and their corresponding labels
 * 
 * NOTE: This is NOT for sightings! Sightings use the BirdAge enum 
 * which has a fixed database model and should not be changed.
 */

export interface AgeOption {
  value: number;
  label: string;
  shortLabel: string;
}

// Official age codes and labels
export const AGE_MAPPING: Record<number, AgeOption> = {
  1: { value: 1, label: 'Nestling', shortLabel: 'Nestling' },
  2: { value: 2, label: 'Fängling', shortLabel: 'Fängling' },
  3: { value: 3, label: 'Diesjährig', shortLabel: 'Diesjährig' },
  4: { value: 4, label: 'Nicht Diesjährig', shortLabel: 'Nicht Diesjährig' },
  5: { value: 5, label: 'Vorjährig', shortLabel: 'Vorjährig' },
  6: { value: 6, label: 'Älter als vorjährig', shortLabel: 'Älter als vorjährig' },
  7: { value: 7, label: '3. Kalender Jahr', shortLabel: '3. Kalender Jahr' },
  8: { value: 8, label: 'Über 3 Jahre', shortLabel: 'Über 3 Jahre' }
};

/**
 * Get ringing age options for form dropdowns
 * @param includeCode Whether to include the numeric code in the display text
 * @returns Array of ringing age options for use in dropdowns
 */
export function getRingingAgeOptions(includeCode = true): Array<{ text: string; value: number }> {
  return Object.values(AGE_MAPPING).map(age => ({
    text: includeCode ? `${age.label} (${age.value})` : age.label,
    value: age.value
  }));
}

/**
 * Format ringing age code to human-readable string
 * @param age Numeric ringing age code
 * @param includeCode Whether to include the numeric code in parentheses
 * @returns Formatted ringing age string
 */
export function formatRingingAge(age: number | string | null | undefined, includeCode = true): string {
  if (age === null || age === undefined) return 'Unbekannt';
  
  const numericAge = typeof age === 'string' ? parseInt(age, 10) : age;
  
  if (isNaN(numericAge)) return 'Unbekannt';
  
  const ageMapping = AGE_MAPPING[numericAge];
  if (ageMapping) {
    return includeCode ? `${ageMapping.label} (${ageMapping.value})` : ageMapping.label;
  }
  
  return `Code ${numericAge}`;
}

/**
 * Get short label for ringing age (without code)
 * @param age Numeric ringing age code
 * @returns Short ringing age label
 */
export function getRingingAgeShortLabel(age: number | string | null | undefined): string {
  if (age === null || age === undefined) return 'Unbekannt';
  
  const numericAge = typeof age === 'string' ? parseInt(age, 10) : age;
  
  if (isNaN(numericAge)) return 'Unbekannt';
  
  const ageMapping = AGE_MAPPING[numericAge];
  return ageMapping ? ageMapping.shortLabel : `Code ${numericAge}`;
}

/**
 * Validate if a ringing age code is valid
 * @param age Ringing age code to validate
 * @returns True if valid, false otherwise
 */
export function isValidRingingAge(age: number): boolean {
  return age in AGE_MAPPING;
}
