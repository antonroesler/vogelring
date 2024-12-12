// Color scheme for bird species
export const speciesColors: Record<string, string> = {
  'Nilgans': '#E57373',      // Soft red
  'Kanadagans': '#81C784',   // Soft green
  'Graugans': '#64B5F6',     // Soft blue
  'Bläss-x Graugans': '#BA68C8', // Soft purple
  'KxG': '#FFD54F',          // Soft yellow
  'Höckerschwan': '#455A64', // Dark blue-gray
  'Weißwangengans': '#9575CD', // Soft violet
  'Mandarinente': '#FFB74D', // Soft orange
  'Kormoran': '#7986CB'      // Soft indigo
};

// Get color for any species (returns a default color if species is not in the main color map)
export const getSpeciesColor = (species: string): string => {
  return speciesColors[species] || '#CCCCCC'; // Default gray for other species
}; 