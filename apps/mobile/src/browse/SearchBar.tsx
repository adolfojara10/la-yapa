/**
 * Sticky header for the browse screen: search + filter + view toggle.
 *
 * The search input is bound directly to the filter store's `q` so typing
 * filters the bag list live (debouncing happens at the store boundary —
 * `q` is sent on every keystroke; React Query's keepPreviousData smooths
 * the UI). Open-filters chip shows the active-filter count.
 */
import { Filter, List as ListIcon, MapPin, Search, X } from 'lucide-react-native';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { Text } from '@/components/ui/Text';
import { useFilterStore } from '@/filters/store';
import { useTheme } from '@/theme';

interface Props {
  view: 'list' | 'map';
  onToggleView: () => void;
  onOpenFilters: () => void;
}

export function SearchBar({ view, onToggleView, onOpenFilters }: Props) {
  const { theme } = useTheme();
  const q = useFilterStore((s) => s.q);
  const setSearchQuery = useFilterStore((s) => s.setSearchQuery);
  const activeCount = useFilterStore((s) => s.activeCount());

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: theme.colors.surface, borderBottomColor: theme.colors.border },
      ]}
    >
      <View
        style={[
          styles.inputWrap,
          {
            backgroundColor: theme.colors.background,
            borderColor: theme.colors.border,
            borderRadius: theme.radii.md,
          },
        ]}
      >
        <Search size={18} color={theme.colors.textMuted} />
        <TextInput
          value={q}
          onChangeText={setSearchQuery}
          placeholder="Buscar bolsas, panaderías..."
          placeholderTextColor={theme.colors.textMuted}
          style={[styles.input, { color: theme.colors.text, fontFamily: theme.fonts.body }]}
          returnKeyType="search"
        />
        {q ? (
          <Pressable onPress={() => setSearchQuery('')} hitSlop={8}>
            <X size={16} color={theme.colors.textMuted} />
          </Pressable>
        ) : null}
      </View>

      <Pressable
        onPress={onOpenFilters}
        style={[
          styles.iconButton,
          { backgroundColor: theme.colors.background, borderColor: theme.colors.border },
        ]}
        hitSlop={6}
      >
        <Filter size={18} color={theme.colors.text} />
        {activeCount > 0 ? (
          <View style={[styles.badge, { backgroundColor: theme.colors.primary }]}>
            <Text
              variant="caption"
              style={{ color: theme.colors.textInverse, fontWeight: '700', fontSize: 10 }}
            >
              {activeCount}
            </Text>
          </View>
        ) : null}
      </Pressable>

      <Pressable
        onPress={onToggleView}
        style={[
          styles.iconButton,
          { backgroundColor: theme.colors.background, borderColor: theme.colors.border },
        ]}
        hitSlop={6}
      >
        {view === 'list' ? (
          <MapPin size={18} color={theme.colors.text} />
        ) : (
          <ListIcon size={18} color={theme.colors.text} />
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 8,
    borderBottomWidth: 1,
  },
  inputWrap: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    height: 40,
    borderWidth: 1,
    gap: 8,
  },
  input: { flex: 1, fontSize: 14, padding: 0 },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badge: {
    position: 'absolute',
    top: -4,
    right: -4,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    paddingHorizontal: 4,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
