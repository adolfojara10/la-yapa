import { apiClient } from './client';

export interface GeoSuggestion {
  id: string;
  label: string;
  lat: number;
  lng: number;
}

interface SearchGeoParams {
  q: string;
  country?: string;
  limit?: number;
  lat?: number;
  lng?: number;
  lang?: string;
}

interface SearchGeoResponse {
  results: GeoSuggestion[];
}

export async function searchPlaces(params: SearchGeoParams): Promise<GeoSuggestion[]> {
  const { data } = await apiClient.get<SearchGeoResponse>('/geo/search', { params });
  return data.results;
}
