// Farbringe: palette, labels and search helpers.
// Keep in sync with backend/src/utils/color_rings.py

export type ColorKey =
  | 'white' | 'black' | 'red' | 'orange' | 'yellow'
  | 'lightgreen' | 'darkgreen' | 'lightblue' | 'darkblue'
  | 'violet' | 'pink' | 'brown' | 'grey';

export interface ColorDef {
  key: ColorKey;
  label: string;
  hex: string;
  abbrevs: string[];
}

export const COLOR_PALETTE: ColorDef[] = [
  { key: 'white', label: 'weiß', hex: '#ffffff', abbrevs: ['w', 'weiss'] },
  { key: 'black', label: 'schwarz', hex: '#1f1f1f', abbrevs: ['s', 'n'] },
  { key: 'red', label: 'rot', hex: '#d32f2f', abbrevs: ['r'] },
  { key: 'orange', label: 'orange', hex: '#f57c00', abbrevs: ['o'] },
  { key: 'yellow', label: 'gelb', hex: '#fdd835', abbrevs: ['y', 'ge'] },
  { key: 'lightgreen', label: 'hellgrün', hex: '#8bc34a', abbrevs: ['hg', 'hellgruen', 'lime'] },
  { key: 'darkgreen', label: 'dunkelgrün', hex: '#2e7d32', abbrevs: ['dg', 'g', 'gruen', 'grün', 'dunkelgruen'] },
  { key: 'lightblue', label: 'hellblau', hex: '#4fc3f7', abbrevs: ['hb'] },
  { key: 'darkblue', label: 'dunkelblau', hex: '#1a3a8f', abbrevs: ['db', 'b', 'blau'] },
  { key: 'violet', label: 'violett', hex: '#7b1fa2', abbrevs: ['v', 'lila'] },
  { key: 'pink', label: 'rosa', hex: '#f48fb1', abbrevs: ['p', 'pink'] },
  { key: 'brown', label: 'braun', hex: '#6d4c41', abbrevs: ['br'] },
  { key: 'grey', label: 'grau', hex: '#9e9e9e', abbrevs: ['gr'] },
];

export const MARK_TYPES = [
  { value: 'leg', title: 'Beinring' },
  { value: 'neck', title: 'Halsring' },
  { value: 'wing', title: 'Flügelmarke' },
];

export const LEGS = [
  { value: 'left', title: 'links' },
  { value: 'right', title: 'rechts' },
];

const byKey = new Map(COLOR_PALETTE.map(c => [c.key, c]));

export const getColor = (key?: string | null): ColorDef | undefined =>
  key ? byKey.get(key as ColorKey) : undefined;

export const colorLabel = (key?: string | null): string =>
  getColor(key)?.label ?? key ?? '';

// Readable default text color when the inscription color is unknown
export const contrastHex = (hex: string): string => {
  const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
  return 0.299 * r + 0.587 * g + 0.114 * b > 150 ? '#1f1f1f' : '#ffffff';
};

export const normalizeCode = (code?: string | null): string =>
  (code ?? '').replace(/\s+/g, '').toUpperCase();

export interface ColorRingLike {
  ring_color?: string | null;
  text_color?: string | null;
  code?: string | null;
}

// "rot · Schrift weiß" – spelled out so the ring is usable without seeing colors
export const describeColors = (cr: ColorRingLike): string => {
  const ring = colorLabel(cr.ring_color);
  return cr.text_color ? `${ring} · Schrift ${colorLabel(cr.text_color)}` : ring;
};

export const describeColorRing = (cr: ColorRingLike): string =>
  `${describeColors(cr)} ${cr.code ?? ''}`.trim();

// Lowercased text a free-text ring search can match against
export const colorRingSearchText = (cr?: ColorRingLike | null): string => {
  if (!cr?.code) return '';
  const parts = [cr.code, cr.ring_color, cr.text_color]
    .flatMap(key => {
      const def = getColor(key);
      return def ? [def.label, def.key, ...def.abbrevs] : [key ?? ''];
    });
  return parts.join(' ').toLowerCase();
};

// Every whitespace-separated token must appear somewhere in the haystack
export const matchesRingSearch = (query: string, haystack: string): boolean => {
  const tokens = query.toLowerCase().split(/[\s/]+/).filter(Boolean);
  const text = haystack.toLowerCase();
  return tokens.every(t => text.includes(t));
};

// Bird detail URL: by metal ring, or by color ring when the metal ring is unknown
export const birdPath = (bird: { ring?: string | null; color_ring?: { id: string } | null }): string | null => {
  if (bird.ring) return `/birds/${encodeURIComponent(bird.ring)}`;
  if (bird.color_ring) return `/birds/farbring/${bird.color_ring.id}`;
  return null;
};
