/**
 * Centralized EURING age code -> label mapping.
 * Shared by Ringings and Sightings (sightings render via utils/sightingCoding.ts,
 * which reuses these labels).
 *
 * `value` is the integer stored in the DB. `ringCode` is the character RING/EURING
 * uses in its own age list — identical to `value` for 0–9, but the letters A–D for
 * 10–13 (over-4th-year classes, useful for gulls etc.). We display and export the
 * ringCode so the sheet matches RING exactly.
 */

export interface AgeOption {
  value: number;
  ringCode: string;
  label: string;
  shortLabel: string;
}

// Official age codes and labels (EURING). Codes 9–D added for older birds
// (gulls etc.); 0 = unknown (e.g. only the ring was found).
export const AGE_MAPPING: Record<number, AgeOption> = {
  0: { value: 0, ringCode: '0', label: 'unbekannt', shortLabel: 'unbekannt' },
  1: { value: 1, ringCode: '1', label: 'Nestling', shortLabel: 'Nestling' },
  2: { value: 2, ringCode: '2', label: 'Fängling', shortLabel: 'Fängling' },
  3: { value: 3, ringCode: '3', label: 'Diesjährig', shortLabel: 'Diesjährig' },
  4: { value: 4, ringCode: '4', label: 'Nicht Diesjährig', shortLabel: 'Nicht Diesjährig' },
  5: { value: 5, ringCode: '5', label: 'Vorjährig', shortLabel: 'Vorjährig' },
  6: { value: 6, ringCode: '6', label: 'Älter als vorjährig', shortLabel: 'Älter als vorjährig' },
  7: { value: 7, ringCode: '7', label: 'im 3. Kalenderjahr', shortLabel: 'im 3. Kalenderjahr' },
  8: { value: 8, ringCode: '8', label: 'über 3 Jahre alt', shortLabel: 'über 3 Jahre alt' },
  9: { value: 9, ringCode: '9', label: 'im 4. Kalenderjahr', shortLabel: 'im 4. Kalenderjahr' },
  10: { value: 10, ringCode: 'A', label: 'über 4 Jahre alt', shortLabel: 'über 4 Jahre alt' },
  11: { value: 11, ringCode: 'B', label: 'im 5. Kalenderjahr', shortLabel: 'im 5. Kalenderjahr' },
  12: { value: 12, ringCode: 'C', label: 'über 5 Jahre alt', shortLabel: 'über 5 Jahre alt' },
  13: { value: 13, ringCode: 'D', label: 'im 6. Kalenderjahr', shortLabel: 'im 6. Kalenderjahr' }
};

/**
 * Age codes in dropdown display order: 1–13 first (the common progression),
 * then 0 "Unbekannt" last so it doesn't precede Nestling.
 */
export const AGE_CODE_ORDER: number[] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0];

/**
 * Get ringing age options for form dropdowns
 * @param includeCode Whether to include the numeric code in the display text
 * @returns Array of ringing age options for use in dropdowns
 */
export function getRingingAgeOptions(includeCode = true): Array<{ text: string; value: number }> {
  return AGE_CODE_ORDER.map(code => AGE_MAPPING[code]).map(age => ({
    text: includeCode ? `${age.label} (${age.ringCode})` : age.label,
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
    return includeCode ? `${ageMapping.label} (${ageMapping.ringCode})` : ageMapping.label;
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
