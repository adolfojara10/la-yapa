import DateTimePicker, { type DateTimePickerEvent } from '@react-native-community/datetimepicker';
import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Platform, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { businessApi } from '@/api';
import { pickImageAsset, uploadLabel } from '@/business/uploads';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useBagTemplates, useBusinessLocations, useManagedBag } from '@/hooks/useBusinessResources';
import { useTheme } from '@/theme';

import type { BusinessBagPayload } from '@layapa/shared-types';

interface Props {
  bagId?: string;
  templateId?: string;
}

type PickerTarget = 'date' | 'start' | 'end' | null;

function toDateParts(iso: string) {
  const date = new Date(iso);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const hh = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');
  return { date: `${yyyy}-${mm}-${dd}`, time: `${hh}:${min}` };
}

function buildIso(dateText: string, timeText: string) {
  return new Date(`${dateText}T${timeText}:00`).toISOString();
}

function tomorrowDate() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return toDateParts(date.toISOString()).date;
}

const DIETARY_OPTIONS = [
  { key: 'vegetarian', label: 'Vegetariano' },
  { key: 'vegan', label: 'Vegano' },
  { key: 'gluten_free', label: 'Sin gluten' },
  { key: 'sin_lactosa', label: 'Sin lactosa' },
  { key: 'organico', label: 'Organico' },
];

const ALLERGEN_OPTIONS = [
  { key: 'gluten', label: 'Gluten' },
  { key: 'lacteos', label: 'Lacteos' },
  { key: 'mani', label: 'Mani' },
  { key: 'huevo', label: 'Huevo' },
  { key: 'soya', label: 'Soya' },
];

function formatPickerLabel(value: string, kind: 'date' | 'time') {
  if (kind === 'date') {
    const date = new Date(`${value}T12:00:00`);
    return date.toLocaleDateString('es-EC', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  }
  return value;
}

export function BagFormScreen({ bagId, templateId }: Props) {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const isEditing = Boolean(bagId);
  const bagQuery = useManagedBag(bagId);
  const locations = useBusinessLocations();
  const templates = useBagTemplates();

  const [initialized, setInitialized] = useState(false);
  const [type, setType] = useState<'surprise' | 'specific'>('surprise');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [image, setImage] = useState<BusinessBagPayload['image']>();
  const [locationId, setLocationId] = useState<number | null>(null);
  const [quantity, setQuantity] = useState('5');
  const [originalPrice, setOriginalPrice] = useState('9.00');
  const [salePrice, setSalePrice] = useState('3.00');
  const [saleDirty, setSaleDirty] = useState(false);
  const [pickupDate, setPickupDate] = useState(tomorrowDate());
  const [startTime, setStartTime] = useState('14:00');
  const [endTime, setEndTime] = useState('17:00');
  const [pickerTarget, setPickerTarget] = useState<PickerTarget>(null);
  const [dietaryTags, setDietaryTags] = useState<string[]>([]);
  const [allergenWarnings, setAllergenWarnings] = useState<string[]>([]);
  const [suspendedMealEligible, setSuspendedMealEligible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [templateSaving, setTemplateSaving] = useState(false);

  const selectedTemplate = templates.data?.find((item) => item.id === templateId);

  useEffect(() => {
    if (saleDirty) return;
    const original = Number(originalPrice);
    if (!Number.isFinite(original) || original <= 0) return;
    setSalePrice((original / 3).toFixed(2));
  }, [originalPrice, saleDirty]);

  useEffect(() => {
    if (initialized) return;
    if (isEditing && bagQuery.data) {
      const start = toDateParts(bagQuery.data.pickup_window_start);
      const end = toDateParts(bagQuery.data.pickup_window_end);
      setType(bagQuery.data.type);
      setTitle(bagQuery.data.title);
      setDescription(bagQuery.data.description);
      setLocationId(bagQuery.data.business_location_id);
      setQuantity(String(bagQuery.data.quantity_available));
      setOriginalPrice(bagQuery.data.original_price);
      setSalePrice(bagQuery.data.sale_price);
      setSaleDirty(true);
      setPickupDate(start.date);
      setStartTime(start.time);
      setEndTime(end.time);
      setDietaryTags(bagQuery.data.dietary_tags);
      setAllergenWarnings(bagQuery.data.allergen_warnings);
      setSuspendedMealEligible(bagQuery.data.is_suspended_meal_eligible);
      setInitialized(true);
      return;
    }
    if (!isEditing && selectedTemplate) {
      setType(selectedTemplate.type);
      setTitle(selectedTemplate.title);
      setDescription(selectedTemplate.description);
      setOriginalPrice(selectedTemplate.original_price);
      setSalePrice(selectedTemplate.sale_price);
      setSaleDirty(true);
      setDietaryTags(selectedTemplate.dietary_tags);
      setAllergenWarnings(selectedTemplate.allergen_warnings);
      setSuspendedMealEligible(selectedTemplate.is_suspended_meal_eligible);
      setInitialized(true);
      return;
    }
    if (!isEditing && !templateId && locations.data?.[0]) {
      setLocationId(locations.data[0].id);
      setInitialized(true);
    }
  }, [bagQuery.data, initialized, isEditing, locations.data, selectedTemplate, templateId]);

  useEffect(() => {
    if (locationId === null && locations.data?.[0]) {
      setLocationId(locations.data[0].id);
    }
  }, [locationId, locations.data]);

  function toggleValue(values: string[], next: string, setValues: (value: string[]) => void) {
    setValues(values.includes(next) ? values.filter((item) => item !== next) : [...values, next]);
  }

  function pickerValue(target: Exclude<PickerTarget, null>) {
    if (target === 'date') {
      return new Date(`${pickupDate}T12:00:00`);
    }
    const time = target === 'start' ? startTime : endTime;
    return new Date(`${pickupDate}T${time}:00`);
  }

  function handlePickerChange(event: DateTimePickerEvent, selected?: Date) {
    if (event.type === 'dismissed' || !selected || !pickerTarget) {
      if (Platform.OS === 'android') {
        setPickerTarget(null);
      }
      return;
    }

    if (pickerTarget === 'date') {
      const parts = toDateParts(selected.toISOString());
      setPickupDate(parts.date);
    } else {
      const hours = String(selected.getHours()).padStart(2, '0');
      const minutes = String(selected.getMinutes()).padStart(2, '0');
      const value = `${hours}:${minutes}`;
      if (pickerTarget === 'start') {
        setStartTime(value);
      } else {
        setEndTime(value);
      }
    }

    if (Platform.OS === 'android') {
      setPickerTarget(null);
    }
  }

  async function handleSave() {
    if (!locationId) {
      toast.show({ title: 'Selecciona una ubicacion primero.', tone: 'warning' });
      return;
    }
    const payload: BusinessBagPayload = {
      business_location_id: locationId,
      type,
      title: title.trim(),
      description: description.trim(),
      image,
      original_price: originalPrice,
      sale_price: salePrice,
      quantity_available: Number(quantity),
      pickup_window_start: buildIso(pickupDate, startTime),
      pickup_window_end: buildIso(pickupDate, endTime),
      dietary_tags: dietaryTags,
      allergen_warnings: allergenWarnings,
      is_suspended_meal_eligible: suspendedMealEligible,
      is_active: true,
    };

    setSubmitting(true);
    try {
      if (isEditing && bagId) {
        await businessApi.updateBag(bagId, payload);
      } else {
        await businessApi.createBag(payload);
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['business-bags'] }),
        queryClient.invalidateQueries({ queryKey: ['business-bag', bagId] }),
      ]);
      toast.show({ title: isEditing ? 'Bolsa actualizada.' : 'Bolsa publicada.', tone: 'success' });
      router.replace('/(business)/(tabs)/bags');
    } catch (error) {
      const detail = (error as { response?: { data?: { detail?: string } } }).response?.data
        ?.detail;
      toast.show({ title: detail ?? 'No pudimos guardar la bolsa.', tone: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSaveTemplate() {
    setTemplateSaving(true);
    try {
      await businessApi.createBagTemplate({
        name: title.trim() || 'Plantilla sin nombre',
        type,
        title: title.trim(),
        description: description.trim(),
        image,
        original_price: originalPrice,
        sale_price: salePrice,
        dietary_tags: dietaryTags,
        allergen_warnings: allergenWarnings,
        is_suspended_meal_eligible: suspendedMealEligible,
      });
      await queryClient.invalidateQueries({ queryKey: ['business-bag-templates'] });
      toast.show({ title: 'Plantilla guardada.', tone: 'success' });
    } catch {
      toast.show({ title: 'No pudimos guardar la plantilla.', tone: 'error' });
    } finally {
      setTemplateSaving(false);
    }
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <ScrollView contentContainerStyle={styles.content}>
        {isEditing && bagQuery.data && !bagQuery.data.can_edit ? (
          <View
            style={[
              styles.banner,
              {
                backgroundColor: theme.colors.primarySoft,
                borderRadius: theme.radii.lg,
              },
            ]}
          >
            <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
              Esta bolsa ya tiene ventas y no puede editarse.
            </Text>
          </View>
        ) : null}

        <View style={styles.choiceRow}>
          {(['surprise', 'specific'] as const).map((option) => {
            const active = type === option;
            return (
              <Pressable
                key={option}
                onPress={() => setType(option)}
                style={[
                  styles.choiceCard,
                  {
                    borderColor: active ? theme.colors.primary : theme.colors.border,
                    backgroundColor: active ? theme.colors.primarySoft : theme.colors.surface,
                    borderRadius: theme.radii.lg,
                  },
                ]}
              >
                <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                  {option === 'surprise' ? 'Sorpresa' : 'Especifica'}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Input label="Titulo" value={title} onChangeText={setTitle} />
        <Input label="Descripcion" value={description} onChangeText={setDescription} multiline />
        <Button
          variant="ghost"
          fullWidth
          onPress={() =>
            void pickImageAsset().then((asset) => {
              if (asset) setImage(asset);
            })
          }
        >
          {uploadLabel(image)}
        </Button>

        <View style={{ gap: 8 }}>
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            Ubicacion
          </Text>
          <View style={styles.chipRow}>
            {locations.data?.map((location) => {
              const active = locationId === location.id;
              return (
                <Pressable
                  key={location.id}
                  onPress={() => setLocationId(location.id)}
                  style={[
                    styles.chip,
                    {
                      borderColor: active ? theme.colors.primary : theme.colors.border,
                      backgroundColor: active ? theme.colors.primary : 'transparent',
                      borderRadius: theme.radii.full,
                    },
                  ]}
                >
                  <Text
                    variant="small"
                    style={{ color: active ? theme.colors.textInverse : theme.colors.text }}
                  >
                    {location.name}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        <View style={styles.row}>
          <View style={{ flex: 1 }}>
            <Input
              label="Cantidad"
              value={quantity}
              onChangeText={setQuantity}
              keyboardType="number-pad"
            />
          </View>
          <View style={{ flex: 1 }}>
            <Input
              label="Precio original"
              value={originalPrice}
              onChangeText={setOriginalPrice}
              keyboardType="decimal-pad"
            />
          </View>
        </View>

        <Input
          label="Precio La Yapa"
          value={salePrice}
          onChangeText={(value) => {
            setSaleDirty(true);
            setSalePrice(value);
          }}
          keyboardType="decimal-pad"
          helperText="Sugerido automatico: 1/3 del precio original"
        />

        <View style={{ gap: 8 }}>
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            Ventana de retiro
          </Text>
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Button variant="ghost" fullWidth onPress={() => setPickerTarget('date')}>
                {formatPickerLabel(pickupDate, 'date')}
              </Button>
            </View>
          </View>
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Button variant="ghost" fullWidth onPress={() => setPickerTarget('start')}>
                Inicio: {formatPickerLabel(startTime, 'time')}
              </Button>
            </View>
            <View style={{ flex: 1 }}>
              <Button variant="ghost" fullWidth onPress={() => setPickerTarget('end')}>
                Fin: {formatPickerLabel(endTime, 'time')}
              </Button>
            </View>
          </View>
          {pickerTarget ? (
            <View
              style={[
                styles.pickerCard,
                {
                  backgroundColor: theme.colors.surface,
                  borderColor: theme.colors.border,
                  borderRadius: theme.radii.lg,
                },
              ]}
            >
              <DateTimePicker
                value={pickerValue(pickerTarget)}
                mode={pickerTarget === 'date' ? 'date' : 'time'}
                display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                onChange={handlePickerChange}
              />
              {Platform.OS === 'ios' ? (
                <Button variant="ghost" fullWidth onPress={() => setPickerTarget(null)}>
                  Listo
                </Button>
              ) : null}
            </View>
          ) : null}
        </View>

        <View style={{ gap: 8 }}>
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            Dietas
          </Text>
          <View style={styles.chipRow}>
            {DIETARY_OPTIONS.map((option) => {
              const active = dietaryTags.includes(option.key);
              return (
                <Pressable
                  key={option.key}
                  onPress={() => toggleValue(dietaryTags, option.key, setDietaryTags)}
                  style={[
                    styles.chip,
                    {
                      borderColor: active ? theme.colors.primary : theme.colors.border,
                      backgroundColor: active ? theme.colors.primary : 'transparent',
                      borderRadius: theme.radii.full,
                    },
                  ]}
                >
                  <Text
                    variant="small"
                    style={{ color: active ? theme.colors.textInverse : theme.colors.text }}
                  >
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        <View style={{ gap: 8 }}>
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            Alergenos
          </Text>
          <View style={styles.chipRow}>
            {ALLERGEN_OPTIONS.map((option) => {
              const active = allergenWarnings.includes(option.key);
              return (
                <Pressable
                  key={option.key}
                  onPress={() => toggleValue(allergenWarnings, option.key, setAllergenWarnings)}
                  style={[
                    styles.chip,
                    {
                      borderColor: active ? theme.colors.primary : theme.colors.border,
                      backgroundColor: active ? theme.colors.primary : 'transparent',
                      borderRadius: theme.radii.full,
                    },
                  ]}
                >
                  <Text
                    variant="small"
                    style={{ color: active ? theme.colors.textInverse : theme.colors.text }}
                  >
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        <Pressable
          onPress={() => setSuspendedMealEligible((current) => !current)}
          style={[
            styles.choiceCard,
            {
              borderColor: suspendedMealEligible ? theme.colors.primary : theme.colors.border,
              backgroundColor: suspendedMealEligible
                ? theme.colors.primarySoft
                : theme.colors.surface,
              borderRadius: theme.radii.lg,
            },
          ]}
        >
          <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
            Elegible para comida suspendida
          </Text>
        </Pressable>

        <Button
          variant="primary"
          size="lg"
          loading={submitting}
          disabled={Boolean(isEditing && bagQuery.data && !bagQuery.data.can_edit)}
          fullWidth
          onPress={handleSave}
        >
          {isEditing ? 'Guardar cambios' : 'Publicar bolsa'}
        </Button>
        <Button
          variant="ghost"
          size="lg"
          loading={templateSaving}
          fullWidth
          onPress={handleSaveTemplate}
        >
          Guardar como plantilla
        </Button>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: { padding: 16, gap: 14, paddingBottom: 32 },
  row: { flexDirection: 'row', gap: 12 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderWidth: 1.5 },
  choiceRow: { flexDirection: 'row', gap: 12 },
  choiceCard: { flex: 1, padding: 16, borderWidth: 1.5 },
  banner: { padding: 16 },
  pickerCard: { padding: 12, borderWidth: 1, gap: 8 },
});
