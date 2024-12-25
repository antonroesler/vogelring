export interface Sighting {
  id: string;
  excel_id?: number;
  species?: string;
  ring?: string;
  reading?: string;
  date?: string;
  place?: string;
  habitat?: string;
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
  first_seen: string;
  last_seen: string;
  other_species_identifications: Record<string, number>;
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

export interface Dashboard {
  total_sightings: number;  // total number of sightings
  total_birds: number;  // total number of individual birds
  bird_count_today: number;  // number of birds seen today
  bird_count_yesterday: number;  // number of birds seen yesterday
  bird_count_this_week: number;  // number of birds seen this week
  bird_count_last_week: number;  // number of birds seen last week
  strike_day_count: number;  // number of consecutive days with sightings until today
  rolling_year_count_per_month_per_species: {
    [species: string]: RollingYearCountPerMonth[];
  };  // number of sightings per month for the last 12 month per species
  top_3_birds_this_year: SimpleBirdMeta[];  // top 3 birds by number of sightings
  top_3_places_this_year: SimplePlaceMeta[];  // top 3 places by number of sightings
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
}

export interface ShareableReport {
  view_url: string;
}
