import ringSpecies from '@/data/ring-species.json';

// Exact official lookups; retain Vogelring's established name for code 01670.
const speciesNames: Readonly<Record<string, string>> = {
  ...ringSpecies,
  '01670': 'Weißwangengans',
};

export const ringSpeciesCodes = Object.keys(speciesNames);

export function resolveSpeciesName(species: string | null | undefined): string {
  if (!species) return 'Unbekannte Art';
  const code = species.trim();
  if (Object.prototype.hasOwnProperty.call(speciesNames, code)) return speciesNames[code];
  if (/^\d+$/.test(code)) return `Unbekannte Art (Artcode ${code})`;
  return species;
}

// Labels only: callers keep the original values for editing and API requests.
export function speciesOptions(values: string[]): { title: string; value: string }[] {
  const names = [...new Set(values.filter(Boolean).map(resolveSpeciesName))];
  return names.sort((a, b) => a.localeCompare(b, 'de'))
    .map(name => ({ title: name, value: name }));
}
