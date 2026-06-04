/**
 * Forward-geocode a search query via Mapbox.
 *
 * Returns a debounced list of suggestions. Calls Mapbox directly from the
 * device with the public access token — no backend proxy this session.
 * Country bias `ec` (Ecuador) keeps results relevant for our launch market.
 *
 * If the access token is missing (dev w/o Mapbox provisioned), this hook
 * gracefully returns an empty list rather than throwing.
 */
import { useEffect, useState } from 'react';

export interface GeocodeSuggestion {
  id: string;
  label: string;
  lat: number;
  lng: number;
}

const MAPBOX_TOKEN = process.env.EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN ?? '';

export function useGeocode(query: string, opts: { country?: string } = {}) {
  const [suggestions, setSuggestions] = useState<GeocodeSuggestion[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query.trim() || !MAPBOX_TOKEN) {
      setSuggestions([]);
      return;
    }
    const handle = setTimeout(async () => {
      setLoading(true);
      try {
        const url = new URL(
          `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json`,
        );
        url.searchParams.set('access_token', MAPBOX_TOKEN);
        url.searchParams.set('country', opts.country ?? 'ec');
        url.searchParams.set('limit', '5');
        const response = await fetch(url.toString());
        interface Feature {
          id: string;
          place_name: string;
          center: [number, number];
        }
        const body = (await response.json()) as { features?: Feature[] };
        setSuggestions(
          (body.features ?? []).map((f) => ({
            id: f.id,
            label: f.place_name,
            lng: f.center[0],
            lat: f.center[1],
          })),
        );
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(handle);
  }, [query, opts.country]);

  return { suggestions, loading };
}
