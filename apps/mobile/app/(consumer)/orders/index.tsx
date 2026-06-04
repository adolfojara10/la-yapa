/**
 * Order history screen. Reached from the Perfil tab → "Mis pedidos" link.
 */
import { Image } from 'expo-image';
import { useRouter } from 'expo-router';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { OrderStatusBadge } from '@/components/order/OrderStatusBadge';
import { Text } from '@/components/ui/Text';
import { useOrders } from '@/hooks/useOrders';
import { useTheme } from '@/theme';

import type { Order } from '@layapa/shared-types';

export default function OrdersListScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const query = useOrders();

  if (query.isLoading) {
    return (
      <SafeAreaView style={[styles.center, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator color={theme.colors.primary} />
      </SafeAreaView>
    );
  }

  const orders = query.data?.results ?? [];

  return (
    <SafeAreaView
      edges={['top']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <FlatList<Order>
        data={orders}
        keyExtractor={(o) => o.id}
        renderItem={({ item }) => (
          <Pressable
            onPress={() => router.push(`/(consumer)/orders/${item.id}`)}
            style={({ pressed }) => [
              styles.row,
              {
                backgroundColor: theme.colors.surface,
                borderColor: theme.colors.border,
                borderRadius: theme.radii.lg,
                opacity: pressed ? 0.85 : 1,
              },
            ]}
          >
            <Image
              source={{ uri: item.bag.image_url }}
              style={[styles.thumb, { borderRadius: theme.radii.md }]}
              contentFit="cover"
            />
            <View style={{ flex: 1 }}>
              <Text variant="bodyStrong" numberOfLines={1} style={{ color: theme.colors.text }}>
                {item.business_location.business_name}
              </Text>
              <Text variant="small" numberOfLines={1} style={{ color: theme.colors.textMuted }}>
                {item.bag.title}
              </Text>
              <View style={{ marginTop: 6 }}>
                <OrderStatusBadge status={item.status} />
              </View>
            </View>
            <Text variant="bodyStrong" style={{ color: theme.colors.primary }}>
              ${item.total_paid}
            </Text>
          </Pressable>
        )}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text variant="h3" align="center" style={{ color: theme.colors.text }}>
              Aún no tienes pedidos
            </Text>
            <Text
              variant="body"
              align="center"
              style={{ color: theme.colors.textMuted, marginTop: 8 }}
            >
              Cuando reserves tu primera bolsa, aparecerá aquí.
            </Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  list: { padding: 16, gap: 12, flexGrow: 1 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 12,
    borderWidth: 1,
  },
  thumb: { width: 60, height: 60 },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
});
