import type { Sighting } from '@/types';

/**
 * Creates a new sighting object with fields cleared according to user settings
 * @param currentSighting - The current sighting data
 * @param clearFieldsSettings - User's field clearing preferences (true = clear field, false = preserve field)
 * @returns New sighting object with fields cleared according to settings
 */
export function createClearedSighting(
  currentSighting: Partial<Sighting>,
  clearFieldsSettings: Record<string, boolean>
): Partial<Sighting> {
  const preservedSighting: Partial<Sighting> = {};
  
  // Preserve fields based on settings
  Object.keys(currentSighting).forEach(key => {
    if (!clearFieldsSettings[key]) {
      preservedSighting[key as keyof Sighting] = currentSighting[key as keyof Sighting];
    }
  });

  // Handle coordinates together - if either lat or lon should be cleared, clear both
  if (clearFieldsSettings.lat || clearFieldsSettings.lon) {
    preservedSighting.lat = null;
    preservedSighting.lon = null;
    preservedSighting.is_exact_location = false;
  } else {
    preservedSighting.lat = currentSighting.lat;
    preservedSighting.lon = currentSighting.lon;
    preservedSighting.is_exact_location = currentSighting.is_exact_location;
  }

  // Always reset Ring and Ablesung (reading) fields regardless of settings
  // These should never be preserved to avoid duplicate entries
  preservedSighting.ring = undefined;
  preservedSighting.reading = undefined;

  // Always reset melded status
  preservedSighting.melded = false;
  
  return preservedSighting;
}

/**
 * Creates a default sighting object for new entries
 * @returns Default sighting object with current date
 */
export function createDefaultSighting(): Partial<Sighting> {
  return {
    date: new Date().toISOString().split('T')[0],
    melded: false,
    is_exact_location: false
  };
}
