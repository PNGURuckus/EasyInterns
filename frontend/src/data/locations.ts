export type LocationOption = {
  id: string;
  label: string;
  city: string;
  region: string;
  country: string;
  latitude: number;
  longitude: number;
};

export const TOP_LOCATIONS: LocationOption[] = [
  { id: "toronto_on", label: "Toronto, ON", city: "Toronto", region: "Ontario", country: "Canada", latitude: 43.6532, longitude: -79.3832 },
  { id: "vancouver_bc", label: "Vancouver, BC", city: "Vancouver", region: "British Columbia", country: "Canada", latitude: 49.2827, longitude: -123.1207 },
  { id: "montreal_qc", label: "Montréal, QC", city: "Montréal", region: "Quebec", country: "Canada", latitude: 45.5019, longitude: -73.5674 },
  { id: "ottawa_on", label: "Ottawa, ON", city: "Ottawa", region: "Ontario", country: "Canada", latitude: 45.4215, longitude: -75.6972 },
  { id: "calgary_ab", label: "Calgary, AB", city: "Calgary", region: "Alberta", country: "Canada", latitude: 51.0447, longitude: -114.0719 },
  { id: "edmonton_ab", label: "Edmonton, AB", city: "Edmonton", region: "Alberta", country: "Canada", latitude: 53.5461, longitude: -113.4938 },
  { id: "waterloo_on", label: "Waterloo, ON", city: "Waterloo", region: "Ontario", country: "Canada", latitude: 43.4643, longitude: -80.5204 },
  { id: "halifax_ns", label: "Halifax, NS", city: "Halifax", region: "Nova Scotia", country: "Canada", latitude: 44.6488, longitude: -63.5752 },
  { id: "victoria_bc", label: "Victoria, BC", city: "Victoria", region: "British Columbia", country: "Canada", latitude: 48.4284, longitude: -123.3656 },
  { id: "winnipeg_mb", label: "Winnipeg, MB", city: "Winnipeg", region: "Manitoba", country: "Canada", latitude: 49.8951, longitude: -97.1384 },
  { id: "quebec_city_qc", label: "Québec City, QC", city: "Québec City", region: "Quebec", country: "Canada", latitude: 46.8139, longitude: -71.208 },
  { id: "regina_sk", label: "Regina, SK", city: "Regina", region: "Saskatchewan", country: "Canada", latitude: 50.4452, longitude: -104.6189 },
  { id: "saskatoon_sk", label: "Saskatoon, SK", city: "Saskatoon", region: "Saskatchewan", country: "Canada", latitude: 52.1579, longitude: -106.6702 },
  { id: "st_johns_nl", label: "St. John's, NL", city: "St. John's", region: "Newfoundland and Labrador", country: "Canada", latitude: 47.5615, longitude: -52.7126 },
  { id: "charlottetown_pe", label: "Charlottetown, PE", city: "Charlottetown", region: "Prince Edward Island", country: "Canada", latitude: 46.2382, longitude: -63.1311 }
];

export type LocationScope = "city" | "region" | "country" | "remote";

export const REGION_FILTERS: { id: string; label: string; scope: LocationScope; locations?: string[] }[] = [
  { id: "remote", label: "Remote roles", scope: "remote" },
  { id: "canada", label: "All of Canada", scope: "country" },
  { id: "tech_hubs", label: "Top Tech Hubs", scope: "city", locations: ["toronto_on", "vancouver_bc", "montreal_qc", "waterloo_on"] },
  { id: "government", label: "Public Sector Focus", scope: "city", locations: ["ottawa_on", "quebec_city_qc", "regina_sk"] }
];

export const DEFAULT_MAP_CENTER: [number, number] = [56.1304, -106.3468];
export const DEFAULT_MAP_ZOOM = 4;
