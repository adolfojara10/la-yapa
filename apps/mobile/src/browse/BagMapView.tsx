/**
 * Map view backed by @rnmapbox/maps.
 *
 * Markers are clustered by (lat, lng) on the client — multiple bags at the
 * same location collapse into one pin with a count badge. Tap → opens the
 * BagBottomSheet for that location.
 *
 * If the Mapbox access token isn't provisioned, MapView renders an empty
 * gray grid (Mapbox's degraded behavior) but the screen does NOT crash —
 * markers still appear on the empty grid. The list view remains the usable
 * fallback in that case.
 */
import Mapbox from '@rnmapbox/maps';
import { useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { Text } from '@/components/ui/Text';
import { useInfiniteBags } from '@/hooks/useInfiniteBags';
import { useTheme } from '@/theme';

import { BagBottomSheet, type BottomSheetHandle } from './BagBottomSheet';

import type { BagListItem } from '@layapa/shared-types';

interface Props {
  location: { lat: number; lng: number } | null;
}

// Set token once at module load — the Mapbox SDK is happy with empty string;
// tiles just won't load. See PROGRESS.md Session 7 Caveats.
Mapbox.setAccessToken(process.env.EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN ?? '');

// Centroid for the default-no-location fallback (Cuenca, Ecuador).
const DEFAULT_CENTER: [number, number] = [-79.0059, -2.9001];

interface ClusterEntry {
  key: string;
  lat: number;
  lng: number;
  bags: BagListItem[];
}

function clusterByLocation(bags: BagListItem[]): ClusterEntry[] {
  const groups = new Map<string, ClusterEntry>();
  for (const bag of bags) {
    const { latitude, longitude, location_id } = bag.business;
    if (latitude === null || longitude === null) continue;
    const key = String(location_id);
    const existing = groups.get(key);
    if (existing) {
      existing.bags.push(bag);
    } else {
      groups.set(key, { key, lat: latitude, lng: longitude, bags: [bag] });
    }
  }
  return [...groups.values()];
}

export function BagMapView({ location }: Props) {
  const { theme } = useTheme();
  const query = useInfiniteBags({ location });
  const sheetRef = useRef<BottomSheetHandle>(null);
  const [selectedCluster, setSelectedCluster] = useState<ClusterEntry | null>(null);

  const clusters = useMemo(
    () => clusterByLocation(query.data?.pages.flatMap((p) => p.results) ?? []),
    [query.data],
  );

  const center: [number, number] = location ? [location.lng, location.lat] : DEFAULT_CENTER;

  useEffect(() => {
    if (selectedCluster) sheetRef.current?.expand();
  }, [selectedCluster]);

  return (
    <View style={styles.container}>
      <Mapbox.MapView
        style={StyleSheet.absoluteFillObject}
        styleURL={Mapbox.StyleURL.Light}
        scaleBarEnabled={false}
      >
        <Mapbox.Camera centerCoordinate={center} zoomLevel={13} animationMode="none" />
        {location ? <Mapbox.UserLocation visible androidRenderMode="normal" /> : null}
        {clusters.map((cluster) => (
          <Mapbox.PointAnnotation
            key={cluster.key}
            id={cluster.key}
            coordinate={[cluster.lng, cluster.lat]}
            onSelected={() => setSelectedCluster(cluster)}
          >
            <View
              style={[
                styles.marker,
                {
                  backgroundColor: theme.colors.primary,
                  borderColor: theme.colors.textInverse,
                  borderRadius: theme.radii.full,
                },
              ]}
            >
              <Text
                variant="caption"
                style={{ color: theme.colors.textInverse, fontWeight: '700' }}
              >
                {cluster.bags.length}
              </Text>
            </View>
          </Mapbox.PointAnnotation>
        ))}
      </Mapbox.MapView>
      <BagBottomSheet
        ref={sheetRef}
        bags={selectedCluster?.bags ?? []}
        onDismiss={() => setSelectedCluster(null)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  marker: {
    minWidth: 32,
    height: 32,
    paddingHorizontal: 8,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
