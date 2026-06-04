/**
 * Bag detail screen with sticky reserve CTA.
 *
 * The CTA is intentionally a stub this session — tapping shows a toast.
 * Real reservation/checkout ships in Session 8 (orders + payments).
 */
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Clock, MapPin, Star } from 'lucide-react-native';
import { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useBag } from '@/hooks/useBag';
import { useUserLocation } from '@/hooks/useUserLocation';
import { useTheme } from '@/theme';

import type { BagDetail } from '@layapa/shared-types';

function formatPickupWindow(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const fmt = (d: Date) =>
    d.toLocaleTimeString('es-EC', { hour: 'numeric', minute: '2-digit', hour12: false });
  return `${fmt(s)} – ${fmt(e)}`;
}

function pickupCountdown(start: string, end: string, now: Date): string {
  const e = new Date(end).getTime();
  const s = new Date(start).getTime();
  const diff = (e - now.getTime()) / 1000;
  if (diff <= 0) return 'Cerrado';
  if (now.getTime() < s) {
    const startDiff = (s - now.getTime()) / 1000;
    const h = Math.floor(startDiff / 3600);
    const m = Math.floor((startDiff % 3600) / 60);
    return h > 0 ? `Abre en ${h}h ${m}min` : `Abre en ${m}min`;
  }
  const h = Math.floor(diff / 3600);
  const m = Math.floor((diff % 3600) / 60);
  return h > 0 ? `Cierra en ${h}h ${m}min` : `Cierra en ${m}min`;
}

export default function BagDetailScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { location } = useUserLocation();
  const query = useBag(id, location);
  const [quantity, setQuantity] = useState(1);
  const { width } = useWindowDimensions();

  if (query.isLoading) {
    return (
      <SafeAreaView style={[styles.center, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator color={theme.colors.primary} />
      </SafeAreaView>
    );
  }

  if (query.isError || !query.data) {
    return (
      <SafeAreaView style={[styles.center, { backgroundColor: theme.colors.background }]}>
        <Text variant="h3" style={{ color: theme.colors.text }} align="center">
          No pudimos cargar la bolsa.
        </Text>
        <Button variant="ghost" onPress={() => router.back()}>
          Volver
        </Button>
      </SafeAreaView>
    );
  }

  const bag: BagDetail = query.data;
  const images = [bag.image_url, ...(bag.extra_image_urls ?? [])].filter(Boolean);
  const total = (Number(bag.sale_price) * quantity).toFixed(2);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <FlatList
          data={images}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          keyExtractor={(url, i) => `${url}-${i}`}
          renderItem={({ item }) => (
            <Image
              source={{ uri: item }}
              style={{ width, aspectRatio: 16 / 9 }}
              contentFit="cover"
              transition={200}
            />
          )}
        />

        <View style={styles.body}>
          <Text variant="h2" style={{ color: theme.colors.text }}>
            {bag.business.name}
          </Text>
          <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
            {bag.title}
          </Text>

          <View style={styles.metaRow}>
            {bag.business.rating_average !== null ? (
              <View style={styles.metaItem}>
                <Star size={14} color={theme.colors.warning} fill={theme.colors.warning} />
                <Text variant="small" style={{ color: theme.colors.textMuted, marginLeft: 4 }}>
                  {bag.business.rating_average.toFixed(1)} ({bag.business.rating_count})
                </Text>
              </View>
            ) : null}
            {bag.distance_m !== null ? (
              <View style={styles.metaItem}>
                <MapPin size={14} color={theme.colors.textMuted} />
                <Text variant="small" style={{ color: theme.colors.textMuted, marginLeft: 4 }}>
                  {(bag.distance_m / 1000).toFixed(1)} km
                </Text>
              </View>
            ) : null}
            <View style={styles.metaItem}>
              <Clock size={14} color={theme.colors.textMuted} />
              <Text variant="small" style={{ color: theme.colors.textMuted, marginLeft: 4 }}>
                {formatPickupWindow(bag.pickup_window_start, bag.pickup_window_end)}
              </Text>
            </View>
          </View>

          <Text variant="small" style={{ color: theme.colors.primary, marginTop: 8 }}>
            {pickupCountdown(bag.pickup_window_start, bag.pickup_window_end, new Date())}
          </Text>

          {bag.description ? (
            <Text variant="body" style={{ color: theme.colors.text, marginTop: 16 }}>
              {bag.description}
            </Text>
          ) : null}

          {bag.type === 'surprise' ? (
            <View
              style={[
                styles.surpriseBox,
                {
                  backgroundColor: theme.colors.primarySoft,
                  borderRadius: theme.radii.md,
                },
              ]}
            >
              <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                Lo que puedes recibir
              </Text>
              <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                Esta bolsa es una sorpresa — el contenido varía cada día según lo que quede al final
                del servicio. Cantidad y variedad equivalen al precio original.
              </Text>
            </View>
          ) : null}

          {bag.dietary_tags.length > 0 ? (
            <Section label="Preferencias">
              <ChipRow items={bag.dietary_tags} tone="primary" />
            </Section>
          ) : null}

          {bag.allergen_warnings.length > 0 ? (
            <Section label="Contiene alérgenos">
              <ChipRow items={bag.allergen_warnings} tone="error" />
            </Section>
          ) : null}

          {bag.quantity_available > 1 ? (
            <Section label="Cantidad">
              <View style={styles.qtyRow}>
                {[1, 2, 3]
                  .filter((n) => n <= bag.quantity_available)
                  .map((n) => (
                    <Pressable
                      key={n}
                      onPress={() => setQuantity(n)}
                      style={[
                        styles.qtyChip,
                        {
                          borderRadius: theme.radii.full,
                          borderColor: quantity === n ? theme.colors.primary : theme.colors.border,
                          backgroundColor: quantity === n ? theme.colors.primary : 'transparent',
                        },
                      ]}
                    >
                      <Text
                        variant="bodyStrong"
                        style={{
                          color: quantity === n ? theme.colors.textInverse : theme.colors.text,
                        }}
                      >
                        {n}
                      </Text>
                    </Pressable>
                  ))}
              </View>
            </Section>
          ) : null}

          {bag.latest_reviews.length > 0 ? (
            <Section label="Reseñas recientes">
              {bag.latest_reviews.map((review) => (
                <View key={review.id} style={styles.review}>
                  <View style={styles.reviewHeader}>
                    <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                      {review.consumer_first_name || 'Cliente'}
                    </Text>
                    <Text variant="small" style={{ color: theme.colors.warning, marginLeft: 8 }}>
                      {'★'.repeat(review.rating)}
                    </Text>
                  </View>
                  {review.comment ? (
                    <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                      {review.comment}
                    </Text>
                  ) : null}
                </View>
              ))}
            </Section>
          ) : null}
        </View>
      </ScrollView>

      <SafeAreaView
        edges={['bottom']}
        style={[
          styles.cta,
          { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.border },
        ]}
      >
        <View style={styles.ctaInner}>
          <View>
            <Text variant="small" style={{ color: theme.colors.textMuted }}>
              Total
            </Text>
            <Text variant="h3" style={{ color: theme.colors.primary }}>
              ${total}
            </Text>
          </View>
          <View style={{ flex: 1 }} />
          <Button
            variant="primary"
            size="lg"
            onPress={() =>
              toast.show({
                title: 'El checkout llega en la próxima sesión.',
                tone: 'info',
              })
            }
          >
            Reservar por ${total}
          </Button>
        </View>
      </SafeAreaView>
    </View>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  const { theme } = useTheme();
  return (
    <View style={styles.section}>
      <Text variant="bodyStrong" style={{ color: theme.colors.text, marginBottom: 8 }}>
        {label}
      </Text>
      {children}
    </View>
  );
}

function ChipRow({ items, tone }: { items: string[]; tone: 'primary' | 'error' }) {
  const { theme } = useTheme();
  const bg = tone === 'error' ? theme.colors.errorSoft : theme.colors.primarySoft;
  return (
    <View style={styles.chipRow}>
      {items.map((label) => (
        <View
          key={label}
          style={[styles.chip, { backgroundColor: bg, borderRadius: theme.radii.full }]}
        >
          <Text variant="small" style={{ color: theme.colors.text, fontWeight: '600' }}>
            {label.replace(/_/g, ' ')}
          </Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  scroll: { paddingBottom: 120 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16 },
  body: { padding: 16 },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 12 },
  metaItem: { flexDirection: 'row', alignItems: 'center' },
  surpriseBox: { padding: 12, marginTop: 16 },
  section: { marginTop: 20 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingVertical: 6, paddingHorizontal: 12 },
  qtyRow: { flexDirection: 'row', gap: 8 },
  qtyChip: {
    width: 44,
    height: 44,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  review: { marginBottom: 12 },
  reviewHeader: { flexDirection: 'row', alignItems: 'center' },
  cta: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    borderTopWidth: 1,
  },
  ctaInner: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
});
