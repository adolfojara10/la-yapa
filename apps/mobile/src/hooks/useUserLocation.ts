/**
 * Resolves the user's location for the browse screen.
 *
 * Order of preference:
 *   1. Live device location (if permission granted)
 *   2. ConsumerProfile.default_location from the auth store
 *   3. null — caller decides how to degrade (list shows ending_soon order;
 *      map shows the default Cuenca centroid).
 */
import { useEffect, useState } from 'react';
import * as Location from 'expo-location';

import { useAuthStore } from '@/auth/store';

export interface UserLocation {
  lat: number;
  lng: number;
  source: 'device' | 'profile';
}

export function useUserLocation(): {
  location: UserLocation | null;
  permissionDenied: boolean;
  refresh: () => Promise<void>;
} {
  const profileDefault = useAuthStore((s) => s.user?.consumer_profile?.default_location ?? null);
  const [location, setLocation] = useState<UserLocation | null>(
    profileDefault ? { lat: profileDefault.lat, lng: profileDefault.lng, source: 'profile' } : null,
  );
  const [permissionDenied, setPermissionDenied] = useState(false);

  async function refresh() {
    const { status } = await Location.getForegroundPermissionsAsync();
    if (status !== 'granted') {
      const ask = await Location.requestForegroundPermissionsAsync();
      if (ask.status !== 'granted') {
        setPermissionDenied(true);
        return;
      }
    }
    try {
      const pos = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude, source: 'device' });
    } catch {
      setPermissionDenied(true);
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { location, permissionDenied, refresh };
}
