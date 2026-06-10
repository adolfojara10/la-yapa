/**
 * Suspended-meals tab — lists active donations available for the vendor
 * to dispatch. Tap → "Despachar" confirmation modal with optional notes.
 */
import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import BottomSheet, { BottomSheetView } from '@gorhom/bottom-sheet';
import { useMemo } from 'react';

import { businessApi } from '@/api';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useSuspendedMeals } from '@/hooks/useSuspendedMeals';
import { useTheme } from '@/theme';

import type { SuspendedMealForDispatch } from '@layapa/shared-types';

export default function SuspendedTab() {
  const { theme } = useTheme();
  const toast = useToast();
  const query = useSuspendedMeals();
  const [selected, setSelected] = useState<SuspendedMealForDispatch | null>(null);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const sheetRef = useRef<BottomSheet>(null);
  const snapPoints = useMemo(() => ['55%'], []);

  function openDispatch(item: SuspendedMealForDispatch) {
    setSelected(item);
    setNotes('');
    sheetRef.current?.snapToIndex(0);
  }

  async function handleDispatch() {
    if (!selected) return;
    setSubmitting(true);
    try {
      await businessApi.dispatchSuspended({
        donation_id: selected.id,
        business_location_id: selected.business_location_id ?? undefined,
        notes: notes.trim() || undefined,
      });
      toast.show({ title: 'Comida suspendida despachada 🌱', tone: 'success' });
      sheetRef.current?.close();
      setSelected(null);
      await query.refetch();
    } catch (err) {
      const detail = (err as { response?: { data?: { code?: string; detail?: string } } }).response
        ?.data;
      if (detail?.code === 'dispatch_rate_limit_exceeded') {
        Alert.alert(
          'Límite diario alcanzado',
          'Has alcanzado el máximo de 5 comidas suspendidas despachadas hoy en esta ubicación.',
        );
      } else if (detail?.code === 'donation_not_available') {
        toast.show({ title: 'Esta donación ya fue reclamada.', tone: 'warning' });
      } else if (detail?.code === 'not_your_location') {
        toast.show({ title: 'Selecciona una ubicación válida.', tone: 'error' });
      } else {
        toast.show({ title: detail?.detail ?? 'No se pudo despachar.', tone: 'error' });
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SafeAreaView
      edges={['top']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <View style={styles.header}>
        <Text variant="h2" style={{ color: theme.colors.text }}>
          Comidas suspendidas
        </Text>
        <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
          Donaciones esperando ser servidas a alguien que las necesite.
        </Text>
      </View>

      <FlatList<SuspendedMealForDispatch>
        data={query.data ?? []}
        keyExtractor={(d) => d.id}
        renderItem={({ item }) => (
          <Pressable
            onPress={() => openDispatch(item)}
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
            <View style={{ flex: 1 }}>
              <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                {item.bag_title || 'Donación al pool general'}
              </Text>
              <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                {item.business_location_name}
              </Text>
              {item.is_anonymous ? (
                <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 2 }}>
                  Donante anónimo
                </Text>
              ) : null}
            </View>
            <Text variant="h3" style={{ color: theme.colors.primary }}>
              ${item.amount}
            </Text>
          </Pressable>
        )}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          query.isLoading ? (
            <View style={styles.empty}>
              <ActivityIndicator color={theme.colors.primary} />
            </View>
          ) : (
            <View style={styles.empty}>
              <Text variant="body" align="center" style={{ color: theme.colors.textMuted }}>
                Aún no hay comidas suspendidas disponibles.
              </Text>
            </View>
          )
        }
      />

      <BottomSheet
        ref={sheetRef}
        index={-1}
        snapPoints={snapPoints}
        enablePanDownToClose
        backgroundStyle={{ backgroundColor: theme.colors.surface }}
        handleIndicatorStyle={{ backgroundColor: theme.colors.border }}
      >
        <BottomSheetView style={styles.sheetContent}>
          <Text variant="h3" style={{ color: theme.colors.text }}>
            Despachar comida suspendida
          </Text>
          {selected ? (
            <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 8 }}>
              {selected.bag_title || 'Pool general'} · ${selected.amount}
            </Text>
          ) : null}
          <TextInput
            value={notes}
            onChangeText={setNotes}
            placeholder="Notas (opcional)"
            placeholderTextColor={theme.colors.textMuted}
            multiline
            numberOfLines={3}
            style={[
              styles.notesInput,
              {
                color: theme.colors.text,
                backgroundColor: theme.colors.background,
                borderColor: theme.colors.border,
                borderRadius: theme.radii.md,
              },
            ]}
          />
          <Button
            variant="primary"
            size="lg"
            fullWidth
            loading={submitting}
            onPress={handleDispatch}
          >
            Despachar
          </Button>
        </BottomSheetView>
      </BottomSheet>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: { padding: 16, paddingBottom: 8 },
  list: { padding: 16, gap: 12, flexGrow: 1 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
    borderWidth: 1,
  },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32 },
  sheetContent: { padding: 20, gap: 12 },
  notesInput: {
    minHeight: 80,
    padding: 12,
    borderWidth: 1,
    textAlignVertical: 'top',
    fontSize: 14,
  },
});
