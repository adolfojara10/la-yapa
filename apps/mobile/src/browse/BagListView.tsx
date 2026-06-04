/**
 * Infinite-scroll FlatList of BagCards.
 *
 * Empty + loading + end-of-list states are handled here so the screen
 * doesn't need to compose them. Pull-to-refresh re-runs the first page.
 */
import { useRouter } from 'expo-router';
import { useCallback } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, View } from 'react-native';

import { Text } from '@/components/ui/Text';
import { useInfiniteBags } from '@/hooks/useInfiniteBags';
import { useTheme } from '@/theme';

import { BagCard } from './BagCard';

import type { BagListItem } from '@layapa/shared-types';

interface Props {
  location: { lat: number; lng: number } | null;
}

export function BagListView({ location }: Props) {
  const { theme } = useTheme();
  const router = useRouter();
  const query = useInfiniteBags({ location });

  const bags: BagListItem[] = query.data?.pages.flatMap((p) => p.results) ?? [];

  const handleEndReached = useCallback(() => {
    if (query.hasNextPage && !query.isFetchingNextPage) {
      void query.fetchNextPage();
    }
  }, [query]);

  return (
    <FlatList
      data={bags}
      keyExtractor={(b) => b.id}
      renderItem={({ item }) => (
        <BagCard bag={item} onPress={() => router.push(`/(consumer)/bag/${item.id}`)} />
      )}
      contentContainerStyle={styles.list}
      onEndReached={handleEndReached}
      onEndReachedThreshold={0.4}
      refreshControl={
        <RefreshControl
          refreshing={query.isRefetching && !query.isFetchingNextPage}
          onRefresh={() => query.refetch()}
          tintColor={theme.colors.primary}
        />
      }
      ListEmptyComponent={
        query.isLoading ? null : (
          <View style={styles.empty}>
            <Text variant="h3" style={{ color: theme.colors.text }} align="center">
              No hay bolsas con esos filtros
            </Text>
            <Text
              variant="body"
              style={{ color: theme.colors.textMuted, marginTop: 8 }}
              align="center"
            >
              Prueba ampliar el radio o quitar algún filtro.
            </Text>
          </View>
        )
      }
      ListFooterComponent={
        query.isFetchingNextPage ? (
          <View style={styles.footer}>
            <ActivityIndicator color={theme.colors.primary} />
          </View>
        ) : null
      }
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: 16, paddingBottom: 32, flexGrow: 1 },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
  footer: { paddingVertical: 16, alignItems: 'center' },
});
