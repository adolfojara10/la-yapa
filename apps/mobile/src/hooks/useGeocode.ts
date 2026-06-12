import { useEffect, useState } from 'react';

import { geoApi } from '@/api';

export interface GeocodeSuggestion {
  id: string;
  label: string;
  lat: number;
  lng: number;
}

export function useGeocode(query: string, opts: { country?: string } = {}) {
  const [suggestions, setSuggestions] = useState<GeocodeSuggestion[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }
    const handle = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await geoApi.searchPlaces({
          q: query.trim(),
          country: opts.country ?? 'ec',
          limit: 5,
          lang: 'es',
        });
        setSuggestions(results);
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
