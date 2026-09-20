const cartoBasemapKey = import.meta.env.VITE_CARTO_BASEMAP_KEY?.trim();

const cartoRasterUrl = (style: 'light_all' | 'dark_all') => {
  const url = `https://{s}.basemaps.cartocdn.com/rastertiles/${style}/{z}/{x}/{y}.png`;

  return cartoBasemapKey
    ? `${url}?key=${encodeURIComponent(cartoBasemapKey)}`
    : url;
};

export const baseMaps = {
  osm: {
    name: 'Standard',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© OpenStreetMap contributors'
  },
  cartoLight: {
    name: 'Hell',
    url: cartoRasterUrl('light_all'),
    attribution: '© OpenStreetMap contributors, © CARTO'
  },
  cartoDark: {
    name: 'Dunkel',
    url: cartoRasterUrl('dark_all'),
    attribution: '© OpenStreetMap contributors, © CARTO'
  }
} as const;
