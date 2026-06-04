/**
 * Browse screen — sticky header + List/Map toggle + filter sheet.
 */
import { useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BagListView } from '@/browse/BagListView';
import { BagMapView } from '@/browse/BagMapView';
import { FiltersSheet, type FiltersSheetHandle } from '@/browse/FiltersSheet';
import { SearchBar } from '@/browse/SearchBar';
import { useUserLocation } from '@/hooks/useUserLocation';
import { useTheme } from '@/theme';

export default function BrowseScreen() {
  const { theme } = useTheme();
  const { location } = useUserLocation();
  const [view, setView] = useState<'list' | 'map'>('list');
  const filtersRef = useRef<FiltersSheetHandle>(null);

  return (
    <SafeAreaView
      edges={['top']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <SearchBar
        view={view}
        onToggleView={() => setView((v) => (v === 'list' ? 'map' : 'list'))}
        onOpenFilters={() => filtersRef.current?.expand()}
      />
      <View style={{ flex: 1 }}>
        {view === 'list' ? <BagListView location={location} /> : <BagMapView location={location} />}
      </View>
      <FiltersSheet ref={filtersRef} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
});
