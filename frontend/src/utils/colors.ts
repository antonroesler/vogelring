// Color scheme for bird species
export const speciesColors: Record<string, string> = {
  'Nilgans': '#D07B4D',      // Natural tan
  'Kanadagans': '#37906D',   // Balanced green
  'Graugans': '#228096',     // Bold teal
  'Bläss-x Graugans': '#69AC91', // Balanced green 75%
  'KxG': '#EAD054',          // Positive yellow
  'Höckerschwan': '#00436C', // Deep blue
  'Weißwangengans': '#9BC8B6', // Balanced green 50%
  'Mandarinente': '#DC9C7A', // Natural tan 75%
  'Kormoran': '#E7BDA6'      // Natural tan 50%
};

// Get color for any species (returns a default color if species is not in the main color map)
export const getSpeciesColor = (species: string): string => {
  return speciesColors[species] || '#DED5CA'; // Default to soft cream for other species
}; 