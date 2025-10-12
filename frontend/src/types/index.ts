export interface Sighting {
  id: string;
  excel_id?: number;
  species?: string;
  ring?: string;
  reading?: string;
  date?: string;
  place?: string;
  area?: string;
  habitat?: string;
  field_fruit?: string;
  group_size?: number;
  small_group_size?: number;
  large_group_size?: number;
  comment?: string;
  melder?: string;
  melded?: boolean;
  lat?: number;
  lon?: number;
  is_exact_location?: boolean;
  partner?: string | null;
  status?: 'BV' | 'MG' | 'NB' | 'RV' | 'TF' | null;
  age?: BirdAge | null;
  breed_size?: number | null;
  family_size?: number | null;
  pair?: PairType | null;
  sex?: "M" | "W" | null;
}

export enum BirdStatus {
  BV = "BV",
  MG = "MG",
  NB = "NB",
  RV = "RV",
  TOTFUND = "TF"
}

export interface BirdMeta {
  species: string;
  ring: string;
  sighting_count: number;
  first_seen: string;
  last_seen: string;
  other_species_identifications: Record<string, number>;
  sightings: Sighting[];
  partners?: Partner[];
}

export interface AnalyticsBirdMeta extends BirdMeta {
  count: number;
  places: string[];
}

export interface FriendResponse {
  bird: BirdMeta;
  friends: AnalyticsBirdMeta[];
  seen_status: Record<string, SeenStatus>;
}

export interface RollingYearCountPerMonth {
  year: number;
  month: number;
  count: number;
}

export interface SimpleBirdMeta {
  species: string;
  ring: string;
  sighting_count: number;
}

export interface SimplePlaceMeta {
  place: string;
  count: number;
}

export interface SuggestionBird {
  ring: string;
  species: string;
  sighting_count: number;
  last_seen: string;
  first_seen: string;
}

export interface Dashboard {
  count_sightings_this_week: number;
  count_sightings_last_week: number;
  count_sightings_today: number;
  count_sightings_yesterday: number;
  day_streak: number;
  count_total_sightings: number;
  count_total_unique_birds: number;
  top_species: { [species: string]: number };
  top_locations: { [location: string]: number };
}

export interface Ringing {
  id: string;
  ring: string;
  ring_scheme: string;
  species: string;
  date: string;  // ISO format date string
  place: string;
  lat: number;
  lon: number;
  ringer: string;
  sex: number;
  age: number;
  status?: BirdStatus;  // New optional field
  comment?: string;  // New optional comment field
}

export interface ShareableReport {
  view_url: string;
}

export interface Partner {
  ring: string;
  year: number;
}

export interface SuggestionLists {
  places: string[];
  species: string[];
  habitats: string[];
  melders: string[];
  field_fruits: string[];
}

export enum BirdAge {
  AD = "ad",  // Adult
  DJ = "dj",  // Diesjährig
  VJ = "vj",  // Vorjährig
  JUV = "juv" // Juvenile
}

export enum PairType {
  PAIRED = "x",
  FAMILY = "F",
  SCHOOL = "S"
}

export enum SeenStatus {
  CURRENT_BIRD = "CURRENT_BIRD",
  SEEN_TOGETHER = "SEEN_TOGETHER",
  SEEN_SEPARATE = "SEEN_SEPARATE"
}

// Family Relationship Types
export interface FamilyPartner {
  ring: string;
  year: number;
  confidence?: string;
  source?: string;
  notes?: string;
}

export interface FamilyChild {
  ring: string;
  year: number;
  confidence?: string;
  source?: string;
  notes?: string;
}

export interface FamilyParent {
  ring: string;
  year: number;
  confidence?: string;
  source?: string;
  notes?: string;
}

export interface FamilySibling {
  ring: string;
  year: number;
  confidence?: string;
  source?: string;
  notes?: string;
}

export interface FamilyTreeEntry {
  ring: string;
  partners: FamilyPartner[];
  children: FamilyChild[];
  parents: FamilyParent[];
  siblings: FamilySibling[];
}