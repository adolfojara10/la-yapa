/**
 * Filters bottom sheet — wraps the whole filter UI and binds it to the
 * filter store. Tap "Aplicar" refetches the bag list immediately and then
 * closes the sheet.
 */
import BottomSheet, {
  BottomSheetFooter,
  BottomSheetScrollView,
  type BottomSheetFooterProps,
} from '@gorhom/bottom-sheet';
import { useQueryClient } from '@tanstack/react-query';
import { forwardRef, useCallback, useImperativeHandle, useMemo, useRef } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useFilterStore, type DistanceOption, type RatingOption } from '@/filters/store';
import { useTheme } from '@/theme';

import type { BagSort, PickupWindow } from '@layapa/shared-types';

export interface FiltersSheetHandle {
  expand: () => void;
  close: () => void;
}

const DIETARY_OPTIONS = [
  { key: 'vegetarian', label: 'Vegetariano' },
  { key: 'vegan', label: 'Vegano' },
  { key: 'gluten_free', label: 'Sin gluten' },
  { key: 'sin_lactosa', label: 'Sin lactosa' },
  { key: 'organico', label: 'Orgánico' },
];

const ALLERGEN_OPTIONS = [
  { key: 'mani', label: 'Maní' },
  { key: 'gluten', label: 'Gluten' },
  { key: 'lacteos', label: 'Lácteos' },
  { key: 'frutos_secos', label: 'Frutos secos' },
  { key: 'mariscos', label: 'Mariscos' },
];

const WINDOW_OPTIONS: { key: PickupWindow | null; label: string }[] = [
  { key: null, label: 'Cualquiera' },
  { key: 'today', label: 'Hoy' },
  { key: 'tomorrow', label: 'Mañana' },
  { key: 'this_week', label: 'Esta semana' },
];

const DISTANCE_OPTIONS: { key: DistanceOption; label: string }[] = [
  { key: 1, label: '1 km' },
  { key: 3, label: '3 km' },
  { key: 5, label: '5 km' },
  { key: 10, label: '10 km' },
];

const RATING_OPTIONS: { key: RatingOption; label: string }[] = [
  { key: 0, label: 'Cualquiera' },
  { key: 4, label: '4★ +' },
  { key: 4.5, label: '4.5★ +' },
];

const SORT_OPTIONS: { key: BagSort; label: string }[] = [
  { key: 'distance', label: 'Distancia' },
  { key: 'price', label: 'Precio' },
  { key: 'rating', label: 'Rating' },
  { key: 'ending_soon', label: 'Terminan pronto' },
];

export const FiltersSheet = forwardRef<FiltersSheetHandle, object>(
  function FiltersSheet(_props, ref) {
    const { theme } = useTheme();
    const insets = useSafeAreaInsets();
    const queryClient = useQueryClient();
    const sheetRef = useRef<BottomSheet>(null);
    const snapPoints = useMemo(() => ['85%'], []);

    const store = useFilterStore();

    useImperativeHandle(ref, () => ({
      expand: () => sheetRef.current?.snapToIndex(0),
      close: () => sheetRef.current?.close(),
    }));

    const applyFilters = useCallback(() => {
      void queryClient.invalidateQueries({ queryKey: ['bags', 'list'] });
      sheetRef.current?.close();
    }, [queryClient]);

    const renderFooter = useCallback(
      (props: BottomSheetFooterProps) => (
        <BottomSheetFooter {...props} bottomInset={insets.bottom}>
          <View
            style={[
              styles.footer,
              theme.shadows.sm.rn,
              {
                backgroundColor: theme.colors.surfaceMuted,
                borderTopColor: theme.colors.borderStrong,
              },
            ]}
          >
            <Button variant="primary" size="lg" fullWidth onPress={applyFilters}>
              Aplicar
            </Button>
          </View>
        </BottomSheetFooter>
      ),
      [applyFilters, insets.bottom, theme],
    );

    return (
      <BottomSheet
        ref={sheetRef}
        index={-1}
        snapPoints={snapPoints}
        enablePanDownToClose
        backgroundStyle={{ backgroundColor: theme.colors.surface }}
        handleIndicatorStyle={{ backgroundColor: theme.colors.border }}
        footerComponent={renderFooter}
      >
        <BottomSheetScrollView contentContainerStyle={styles.content}>
          <View style={styles.headerRow}>
            <Text variant="h3" style={{ color: theme.colors.text }}>
              Filtros
            </Text>
            <View style={styles.headerActions}>
              <Button variant="ghost" size="sm" onPress={store.reset}>
                Limpiar
              </Button>
              <Button variant="secondary" size="sm" onPress={applyFilters}>
                Aplicar
              </Button>
            </View>
          </View>

          <FilterSection label="Preferencias" theme={theme}>
            <ChipRow
              options={DIETARY_OPTIONS}
              isActive={(k) => store.dietary.includes(k)}
              onToggle={store.toggleDietary}
            />
          </FilterSection>

          <FilterSection label="Evitar alérgenos" theme={theme}>
            <ChipRow
              options={ALLERGEN_OPTIONS}
              isActive={(k) => store.excludeAllergens.includes(k)}
              onToggle={store.toggleAllergen}
              activeTone="error"
            />
          </FilterSection>

          <FilterSection label="Recoger" theme={theme}>
            <ChipRow
              options={WINDOW_OPTIONS.map((o) => ({ key: String(o.key), label: o.label }))}
              isActive={(k) =>
                (k === 'null' && store.pickupWindow === null) || k === store.pickupWindow
              }
              onToggle={(k) => store.setPickupWindow(k === 'null' ? null : (k as PickupWindow))}
              exclusive
            />
          </FilterSection>

          <FilterSection label="Distancia" theme={theme}>
            <ChipRow
              options={DISTANCE_OPTIONS.map((o) => ({ key: String(o.key), label: o.label }))}
              isActive={(k) => String(store.distanceKm) === k}
              onToggle={(k) => store.setDistance(Number(k) as DistanceOption)}
              exclusive
            />
          </FilterSection>

          <FilterSection label="Rating mínimo" theme={theme}>
            <ChipRow
              options={RATING_OPTIONS.map((o) => ({ key: String(o.key), label: o.label }))}
              isActive={(k) => String(store.minRating) === k}
              onToggle={(k) => store.setMinRating(Number(k) as RatingOption)}
              exclusive
            />
          </FilterSection>

          <FilterSection label="Ordenar por" theme={theme}>
            <ChipRow
              options={SORT_OPTIONS.map((o) => ({ key: o.key, label: o.label }))}
              isActive={(k) => store.sort === k}
              onToggle={(k) => store.setSort(k as BagSort)}
              exclusive
            />
          </FilterSection>
        </BottomSheetScrollView>
      </BottomSheet>
    );
  },
);

function FilterSection({
  label,
  theme,
  children,
}: {
  label: string;
  theme: ReturnType<typeof useTheme>['theme'];
  children: React.ReactNode;
}) {
  return (
    <View style={styles.section}>
      <Text variant="bodyStrong" style={{ color: theme.colors.text, marginBottom: 8 }}>
        {label}
      </Text>
      {children}
    </View>
  );
}

interface ChipRowProps {
  options: { key: string; label: string }[];
  isActive: (key: string) => boolean;
  onToggle: (key: string) => void;
  exclusive?: boolean;
  activeTone?: 'primary' | 'error';
}

function ChipRow({ options, isActive, onToggle, activeTone = 'primary' }: ChipRowProps) {
  const { theme } = useTheme();
  const activeBg = activeTone === 'error' ? theme.colors.error : theme.colors.primary;

  return (
    <View style={styles.chipRow}>
      {options.map((opt) => {
        const active = isActive(opt.key);
        return (
          <Pressable
            key={opt.key}
            onPress={() => onToggle(opt.key)}
            style={[
              styles.chip,
              {
                borderRadius: theme.radii.full,
                borderColor: active ? activeBg : theme.colors.border,
                backgroundColor: active ? activeBg : 'transparent',
              },
            ]}
          >
            <Text
              variant="small"
              style={{
                color: active ? theme.colors.textInverse : theme.colors.text,
                fontWeight: '600',
              }}
            >
              {opt.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, paddingBottom: 140, gap: 8 },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  headerActions: { flexDirection: 'row', gap: 8 },
  section: { marginVertical: 8 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderWidth: 1.5 },
  footer: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 16,
    borderTopWidth: 1,
  },
});
