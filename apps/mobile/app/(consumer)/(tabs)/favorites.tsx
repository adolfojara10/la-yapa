import { useInfiniteQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useCallback } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { bagsApi } from '@/api';
import { BagCard } from '@/browse/BagCard';
import { Text } from '@/components/ui/Text';
import { useUserLocation } from '@/hooks/useUserLocation';
import { useTheme } from '@/theme';

import type { BagListItem, CursorPage } from '@layapa/shared-types';

export default function FavoritesScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const { location } = useUserLocation();

  const query = useInfiniteQuery<
    CursorPage<BagListItem>,
    Error,
    { pages: CursorPage<BagListItem>[]; pageParams: (string | null)[] },
    readonly unknown[],
    string | null
  >({
    queryKey: ['bags', 'favorites', location?.lat, location?.lng],
    initialPageParam: null,
    queryFn: async ({ pageParam }) =>
      pageParam
        ? bagsApi.listBagsFromCursor(pageParam)
        : bagsApi.listBags({
            is_favorited: true,
            ...(location ? { lat: location.lat, lng: location.lng } : {}),
          }),
    getNextPageParam: (last) => last.next ?? null,
    staleTime: 30_000,
  });

  const bags: BagListItem[] = query.data?.pages.flatMap((p) => p.results) ?? [];

  const handleEndReached = useCallback(() => {
    if (query.hasNextPage && !query.isFetchingNextPage) {
      void query.fetchNextPage();
    }
  }, [query]);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text variant="h2" style={{ color: theme.colors.text }}>
          Tus favoritos
        </Text>
      </View>

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
                Aún no tienes favoritos
              </Text>
              <Text
                variant="body"
                style={{ color: theme.colors.textMuted, marginTop: 8 }}
                align="center"
              >
                Toca el corazón en cualquier bolsa para guardarla aquí.
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
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8 },
  list: { padding: 16, paddingBottom: 32, flexGrow: 1 },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
  footer: { paddingVertical: 16, alignItems: 'center' },
});
