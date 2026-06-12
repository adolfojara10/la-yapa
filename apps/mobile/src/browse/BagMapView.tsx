import { useMemo, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import MapView, { Marker, UrlTile } from 'react-native-maps';

import { Text } from '@/components/ui/Text';
import { useInfiniteBags } from '@/hooks/useInfiniteBags';
import { useTheme } from '@/theme';

import { BagBottomSheet, type BottomSheetHandle } from './BagBottomSheet';

import type { BagListItem } from '@layapa/shared-types';

interface Props {
  location: { lat: number; lng: number } | null;
}

interface BagGroup {
  locationId: number;
  latitude: number;
  longitude: number;
  bags: BagListItem[];
}

const CUENCA_REGION = {
  latitude: -2.9006,
  longitude: -79.0045,
  latitudeDelta: 0.12,
  longitudeDelta: 0.12,
};

export function BagMapView({ location }: Props) {
  const { theme } = useTheme();
  const sheetRef = useRef<BottomSheetHandle>(null);
  const [selectedLocationId, setSelectedLocationId] = useState<number | null>(null);
  const query = useInfiniteBags({ location });
  const groups = useMemo(
    () => buildGroups(query.data?.pages.flatMap((page) => page.results) ?? []),
    [query.data],
  );
  const selectedBags = useMemo(
    () => groups.find((group) => group.locationId === selectedLocationId)?.bags ?? [],
    [groups, selectedLocationId],
  );

  const initialRegion = {
    ...(location
      ? {
          latitude: location.lat,
          longitude: location.lng,
          latitudeDelta: 0.08,
          longitudeDelta: 0.08,
        }
      : CUENCA_REGION),
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <MapView
        style={StyleSheet.absoluteFill}
        initialRegion={initialRegion}
        showsUserLocation={Boolean(location)}
        showsMyLocationButton={Boolean(location)}
        mapType="none"
      >
        <UrlTile
          urlTemplate="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          maximumZ={19}
          flipY={false}
        />
        {groups.map((group) => (
          <Marker
            key={group.locationId}
            coordinate={{ latitude: group.latitude, longitude: group.longitude }}
            onPress={() => {
              setSelectedLocationId(group.locationId);
              sheetRef.current?.expand();
            }}
          >
            <View
              style={[
                styles.marker,
                {
                  backgroundColor: theme.colors.primary,
                  borderColor: theme.colors.surface,
                },
              ]}
            >
              <Text
                variant="caption"
                style={{ color: theme.colors.textInverse, fontWeight: '700' }}
              >
                {group.bags.length}
              </Text>
            </View>
          </Marker>
        ))}
      </MapView>

      {query.isLoading ? (
        <View style={styles.loadingOverlay} pointerEvents="none">
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      ) : null}

      <View
        pointerEvents="none"
        style={[
          styles.attribution,
          { backgroundColor: theme.colors.surface, borderColor: theme.colors.border },
        ]}
      >
        <Text variant="caption" style={{ color: theme.colors.textMuted }}>
          © OpenStreetMap contributors
        </Text>
      </View>

      <BagBottomSheet
        ref={sheetRef}
        bags={selectedBags}
        onDismiss={() => setSelectedLocationId(null)}
      />
    </View>
  );
}

function buildGroups(bags: BagListItem[]): BagGroup[] {
  const groups = new Map<number, BagGroup>();
  for (const bag of bags) {
    const latitude = bag.business.latitude;
    const longitude = bag.business.longitude;
    if (latitude === null || longitude === null) continue;
    const existing = groups.get(bag.business.location_id);
    if (existing) {
      existing.bags.push(bag);
      continue;
    }
    groups.set(bag.business.location_id, {
      locationId: bag.business.location_id,
      latitude,
      longitude,
      bags: [bag],
    });
  }
  return [...groups.values()];
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingOverlay: {
    position: 'absolute',
    top: 16,
    right: 16,
  },
  attribution: {
    position: 'absolute',
    right: 12,
    bottom: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderWidth: 1,
    borderRadius: 999,
  },
  marker: {
    minWidth: 32,
    height: 32,
    paddingHorizontal: 8,
    borderRadius: 16,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
