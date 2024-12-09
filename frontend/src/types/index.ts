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
  ring: string;
  species: string;
  last_seen: string;
  sighting_count: number;
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