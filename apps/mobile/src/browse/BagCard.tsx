/**
 * Single bag card for the browse list.
 *
 * Heavy lift here is the price block (strikethrough + discount badge) and
 * the heart toggle with optimistic update. Image uses expo-image with a
 * subtle placeholder so cards don't pop in.
 */
import { Image } from 'expo-image';
import { Heart } from 'lucide-react-native';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { favoritesApi } from '@/api';
import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

import type { BagListItem } from '@layapa/shared-types';

interface Props {
  bag: BagListItem;
  onPress: () => void;
}

function formatDistance(m: number | null): string {
  if (m === null) return '';
  if (m < 1000) return `${m} m`;
  return `${(m / 1000).toFixed(1)} km`;
}

function formatPickupWindow(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const fmt = (d: Date) =>
    d.toLocaleTimeString('es-EC', { hour: 'numeric', minute: '2-digit', hour12: false });
  return `${fmt(s)}–${fmt(e)}`;
}

export function BagCard({ bag, onPress }: Props) {
  const { theme } = useTheme();
  const [favorited, setFavorited] = useState(bag.is_favorited);
  const [busy, setBusy] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    setFavorited(bag.is_favorited);
  }, [bag.is_favorited]);

  async function handleHeart(e?: any) {
    e?.stopPropagation?.();
    if (busy) return;
    const next = !favorited;
    setFavorited(next); // optimistic
    setBusy(true);
    try {
      const result = await favoritesApi.toggleFavorite(bag.business.location_id);
      setFavorited(result.favorited);
      void queryClient.invalidateQueries({ queryKey: ['bags'] });
    } catch {
      setFavorited(!next); // rollback
    } finally {
      setBusy(false);
    }
  }

  const business = bag.business;
  const rating = business.rating_average ?? null;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.border,
          borderRadius: theme.radii.lg,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      <View style={styles.imageWrap}>
        <Image
          source={bag.image_url ? { uri: bag.image_url } : null}
          style={styles.image}
          contentFit="cover"
          placeholder={{ blurhash: 'LEHV6nWB2yk8pyo0adR*.7kCMdnj' }}
          transition={200}
        />
        <View
          style={[
            styles.discountBadge,
            { backgroundColor: theme.colors.primary, borderRadius: theme.radii.full },
          ]}
        >
          <Text variant="caption" style={{ color: theme.colors.textInverse, fontWeight: '700' }}>
            -{bag.discount_percent}%
          </Text>
        </View>
        <Pressable
          onPress={handleHeart}
          hitSlop={8}
          style={[
            styles.heart,
            { backgroundColor: theme.colors.surface, borderRadius: theme.radii.full },
          ]}
        >
          <Heart
            size={20}
            color={favorited ? theme.colors.error : theme.colors.textMuted}
            fill={favorited ? theme.colors.error : 'transparent'}
          />
        </Pressable>
      </View>

      <View style={styles.body}>
        <Text variant="bodyStrong" numberOfLines={1} style={{ color: theme.colors.text }}>
          {business.name}
        </Text>
        <Text variant="small" numberOfLines={1} style={{ color: theme.colors.textMuted }}>
          {bag.title}
        </Text>

        <View style={styles.metaRow}>
          {rating !== null ? (
            <Text variant="small" style={{ color: theme.colors.textMuted }}>
              ★ {rating.toFixed(1)} ({business.rating_count})
            </Text>
          ) : (
            <Text variant="small" style={{ color: theme.colors.textMuted }}>
              Sin reseñas
            </Text>
          )}
          {bag.distance_m !== null ? (
            <Text variant="small" style={{ color: theme.colors.textMuted }}>
              · {formatDistance(bag.distance_m)}
            </Text>
          ) : null}
        </View>

        <View style={styles.priceRow}>
          <Text variant="h3" style={{ color: theme.colors.primary }}>
            ${bag.sale_price}
          </Text>
          <Text
            variant="small"
            style={{
              color: theme.colors.textMuted,
              textDecorationLine: 'line-through',
              marginLeft: 8,
            }}
          >
            ${bag.original_price}
          </Text>
          <View style={{ flex: 1 }} />
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            {formatPickupWindow(bag.pickup_window_start, bag.pickup_window_end)}
          </Text>
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { borderWidth: 1, overflow: 'hidden', marginBottom: 12 },
  imageWrap: { position: 'relative', aspectRatio: 16 / 9 },
  image: { width: '100%', height: '100%' },
  discountBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  heart: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  body: { padding: 12, gap: 4 },
  metaRow: { flexDirection: 'row', alignItems: 'center', marginTop: 2 },
  priceRow: { flexDirection: 'row', alignItems: 'baseline', marginTop: 4 },
});
