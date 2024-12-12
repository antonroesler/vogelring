export interface Sighting {
  id: string;
  excel_id?: number;
  species?: string;
  ring?: string;
  reading?: string;
  date?: string;
  place?: string;
  group_size?: number;
  comment?: string;
  melder?: string;
  melded?: boolean;
  lat?: number;
  lon?: number;
}

export interface BirdMeta {
  species: string;
  ring: string;
  sighting_count: number;
  last_seen: string;
  first_seen: string;
  other_species_identifications: { [species: string]: number };
  sightings: Sighting[];
}

export interface AnalyticsBirdMeta extends BirdMeta {
  count: number;
  places: string[];
}

export interface FriendResponse {
  bird: BirdMeta;
  friends: AnalyticsBirdMeta[];
}